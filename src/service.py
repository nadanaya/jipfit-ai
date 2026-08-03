"""Application service that combines affordability, ML, and policy discovery."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Mapping

from src.affordability import calculate_affordability
from src.config import DATABASE_PATH, REGION_INDEX_PATH, RISK_DESCRIPTIONS, RISK_LABELS
from src.database import log_analysis_run
from src.policy_engine import recommend_policies
from src.predict import predict_burden


def load_region_index(path: Path = REGION_INDEX_PATH) -> dict[str, dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Region index not found: {path}")
    result: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            result[row["region"]] = {
                "region_code": row["region_code"],
                "demo_cost_index": float(row["demo_cost_index"]),
                "note": row["note"],
            }
    if not result:
        raise ValueError("Region index is empty")
    return result


def _validate_profile(profile: Mapping[str, Any]) -> None:
    required = {
        "age",
        "monthly_income",
        "assets",
        "deposit",
        "monthly_rent",
        "management_fee",
        "monthly_debt_payment",
        "household_size",
        "region",
        "is_unemployed",
        "car_value",
        "unhoused",
        "separate_household",
        "unmarried",
    }
    missing = required.difference(profile)
    if missing:
        raise ValueError(f"Missing profile fields: {sorted(missing)}")


def _build_action_plan(
    affordability: Mapping[str, Any],
    model_result: Mapping[str, Any],
    policies: list[Mapping[str, Any]],
    profile: Mapping[str, Any],
) -> list[str]:
    actions: list[str] = []
    gap = int(
        affordability.get(
            "monthly_gap_to_total_recommendation",
            affordability["monthly_gap_to_recommendation"],
        )
    )
    if gap < 0:
        gap_man = abs(gap) / 10_000
        recommended_man = affordability["recommended_max_housing_cost"] / 10_000
        actions.append(
            f"월 {gap_man:,.1f}만 원 절감을 목표로, 통합 고정비가 {recommended_man:,.1f}만 원 이하인 매물과 비교합니다."
        )
    else:
        gap_man = gap / 10_000
        actions.append(
            f"주거비와 부채상환을 합친 월 고정비가 권장 기준보다 {gap_man:,.1f}만 원 낮습니다. "
            "비상자금과 계약 후 현금흐름을 우선 확인합니다."
        )

    unhoused_status = str(profile.get("unhoused_status", "예" if bool(profile["unhoused"]) else "아니오"))
    top = next(
        (
            item
            for item in policies
            if item["status"] not in {"현재 입력상 우선순위 낮음", "핵심요건 미충족"}
        ),
        None,
    )
    if unhoused_status == "아니오":
        actions.append("현재 입력상 무주택 요건을 충족하지 않아 주요 청년 임대·대출 정책의 대상 가능성이 낮습니다. 본인과 세대원의 주택·분양권·입주권 보유 여부를 먼저 확인하세요.")
    elif unhoused_status == "잘 모르겠음":
        actions.append("본인과 세대원의 주택 소유 여부를 확인한 뒤 정책 진단을 다시 실행합니다.")
    elif top:
        actions.append(f"{top['name']}의 공식 자가진단과 최신 모집공고를 먼저 확인합니다.")
    else:
        actions.append("마이홈 자가진단에서 지역별 주거복지사업을 다시 검색합니다.")

    actions.append("계약 전 반환보증 가입 가능 여부, 관리비 세부 항목, 중도해지 조건을 확인합니다.")

    return actions


def _apply_conservative_rule_overlay(
    affordability: Mapping[str, Any],
    model_result: Mapping[str, Any],
) -> dict[str, Any]:
    rule_class = int(affordability["rule_risk_class"])
    model_class = int(model_result["class_id"])
    probabilities = dict(model_result.get("probabilities") or {})
    ai_reference_score = (
        probabilities.get("주의", 0.0) * 0.5 + probabilities.get("위험", 0.0)
        if probabilities
        else model_class / 2
    )
    if rule_class > model_class:
        return {
            **model_result,
            "class_id": rule_class,
            "label": RISK_LABELS[rule_class],
            "rule_class_id": rule_class,
            "rule_label": RISK_LABELS[rule_class],
            "ai_class_id": model_class,
            "ai_label": RISK_LABELS[model_class],
            "ai_reference_score": round(float(ai_reference_score), 2),
            "description": RISK_DESCRIPTIONS[rule_class],
            "model_note": (
                "규칙 기반 진단은 소득 대비 주거비, 부채 포함 통합 고정비, 정책 기본조건 매칭을 봅니다. "
                "AI 참고 위험도는 합성 데이터 기반 보조 지표입니다."
            ),
        }
    return {
        **model_result,
        "rule_class_id": rule_class,
        "rule_label": RISK_LABELS[rule_class],
        "ai_class_id": model_class,
        "ai_label": RISK_LABELS[model_class],
        "ai_reference_score": round(float(ai_reference_score), 2),
        "model_note": (
            "규칙 기반 진단은 소득 대비 주거비, 부채 포함 통합 고정비, 정책 기본조건 매칭을 봅니다. "
            "AI 참고 위험도는 합성 데이터 기반 보조 지표입니다."
        ),
    }


def analyze_profile(
    profile: Mapping[str, Any],
    *,
    log_result: bool = False,
    db_path: Path = DATABASE_PATH,
) -> dict[str, Any]:
    _validate_profile(profile)
    regions = load_region_index()
    region_name = str(profile["region"])
    if region_name not in regions:
        raise ValueError(f"Unsupported region: {region_name}")
    region_meta = regions[region_name]

    affordability_result = calculate_affordability(
        monthly_income=int(profile["monthly_income"]),
        deposit=int(profile["deposit"]),
        monthly_rent=int(profile["monthly_rent"]),
        management_fee=int(profile["management_fee"]),
        monthly_debt_payment=int(profile["monthly_debt_payment"]),
        household_size=int(profile["household_size"]),
    ).to_dict()

    model_features = {
        "age": int(profile["age"]),
        "monthly_income": int(profile["monthly_income"]),
        "assets": int(profile["assets"]),
        "deposit": int(profile["deposit"]),
        "monthly_rent": int(profile["monthly_rent"]),
        "management_fee": int(profile["management_fee"]),
        "monthly_debt_payment": int(profile["monthly_debt_payment"]),
        "household_size": int(profile["household_size"]),
        "region_cost_index": float(region_meta["demo_cost_index"]),
        "is_unemployed": int(bool(profile["is_unemployed"])),
        "car_value": int(profile["car_value"]),
    }
    model_result = _apply_conservative_rule_overlay(affordability_result, predict_burden(model_features))
    policies = recommend_policies(profile)
    actions = _build_action_plan(affordability_result, model_result, policies, profile)

    session_id = None
    if log_result:
        session_id = log_analysis_run(
            profile=profile,
            affordability=affordability_result,
            risk_class=int(model_result["class_id"]),
            policy_ids=[item["policy_id"] for item in policies[:3]],
            db_path=db_path,
        )

    return {
        "profile_summary": {
            "region": region_name,
            "region_cost_index": region_meta["demo_cost_index"],
            "region_index_notice": region_meta["note"],
        },
        "affordability": affordability_result,
        "model": model_result,
        "policies": policies,
        "action_plan": actions,
        "session_id": session_id,
        "disclaimer": (
            "본 결과는 참고용 사전 안내입니다. 실제 대출 승인이나 정책 수급 자격을 확정하지 않습니다. "
            "실제 신청 전 공식 기관의 최신 기준과 심사 절차를 확인하세요."
        ),
    }
