"""Application service that combines affordability, ML, and policy discovery."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Mapping

from src.affordability import calculate_affordability
from src.config import DATABASE_PATH, REGION_INDEX_PATH
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
) -> list[str]:
    actions: list[str] = []
    gap = int(affordability["monthly_gap_to_recommendation"])
    if gap < 0:
        actions.append(
            f"월 주거비를 최소 {abs(gap):,}원 낮추도록 월세·관리비·보증금 조합을 다시 비교합니다."
        )
    else:
        actions.append(
            f"현재 계획은 권장 상한보다 월 {gap:,}원 여유가 있으므로 비상저축을 우선 확보합니다."
        )

    top = next((item for item in policies if item["status"] != "현재 입력상 우선순위 낮음"), None)
    if top:
        actions.append(
            f"우선 후보인 ‘{top['name']}’의 공식 자가진단과 최신 모집공고를 확인합니다."
        )
    else:
        actions.append("마이홈 자가진단에서 지역별 주거복지사업을 다시 검색합니다.")

    if int(model_result["class_id"]) == 2:
        actions.append("계약 전 3개월 현금흐름을 점검하고, 보증금 대출·월세 지원을 함께 비교합니다.")
    else:
        actions.append("계약 전 반환보증 가능 여부, 관리비 항목, 중도해지 조건을 확인합니다.")
    return actions


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
    model_result = predict_burden(model_features)
    policies = recommend_policies(profile)
    actions = _build_action_plan(affordability_result, model_result, policies)

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
        "disclaimer": "본 결과는 참고용 사전 안내입니다. 실제 대출 승인이나 정책 수급 자격을 확정하지 않습니다. 실제 신청 전 공식 기관의 최신 기준과 심사 절차를 확인하세요.",
    }
