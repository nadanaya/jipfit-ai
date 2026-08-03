"""Rule-based pre-screening and policy discovery for youth housing support.

Only conditions that can be inferred from the user's inputs are scored. Missing
official checks remain visible as manual checks so the result does not look like
an eligibility determination.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from src.config import POLICY_CATALOG_PATH

MEDIAN_INCOME_60_2026 = {
    1: 1_538_543,
    2: 2_519_575,
    3: 3_215_422,
    4: 3_896_843,
    5: 4_534_031,
    6: 5_133_571,
}

HAPPY_HOUSING_INCOME_LIMIT_2026 = {
    1: 4_576_036,
    2: 6_452_897,
    3: 8_168_429,
    4: 8_802_202,
    5: 9_326_985,
    6: 9_906_263,
}

YOUTH_MONTHLY_RENT_ASSET_LIMIT = 122_000_000
HAPPY_HOUSING_YOUTH_ASSET_LIMIT = 251_000_000
PUBLIC_RENTAL_CAR_VALUE_LIMIT_2026 = 45_420_000


@dataclass(frozen=True)
class PolicyRecommendation:
    policy_id: str
    name: str
    category: str
    description: str
    status: str
    score: int
    score_breakdown: list[dict[str, int | str]]
    priority_note: str
    passed_checks: list[str]
    failed_checks: list[str]
    manual_checks: list[str]
    official_url: str
    verified_at: str
    source_note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _household_value(table: Mapping[int, int], household_size: int) -> int:
    if household_size < 1:
        raise ValueError("household_size must be at least 1")
    max_size = max(table)
    if household_size <= max_size:
        return table[household_size]
    last = table[max_size]
    previous = table[max_size - 1]
    return last + (household_size - max_size) * (last - previous)


def load_policy_catalog(path: Path = POLICY_CATALOG_PATH) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Policy catalog not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    required = {
        "policy_id",
        "name",
        "category",
        "description",
        "rule_mode",
        "official_url",
        "verified_at",
        "source_note",
    }
    if not rows:
        raise ValueError("Policy catalog is empty")
    missing = required.difference(rows[0])
    if missing:
        raise ValueError(f"Policy catalog is missing columns: {sorted(missing)}")
    return rows


def _check(condition: bool, success: str, failure: str) -> tuple[str, str]:
    return ("passed", success) if condition else ("failed", failure)


def _append_tri_state(
    *,
    status: str,
    passed: list[str],
    failed: list[str],
    manual: list[str],
    yes_value: str,
    success: str,
    no_failure: str,
    unknown_manual: str,
) -> None:
    if status == yes_value:
        passed.append(success)
    elif status == "잘 모르겠음":
        manual.append(unknown_manual)
    else:
        failed.append(no_failure)


def _evaluate_monthly_rent(profile: Mapping[str, Any]) -> tuple[list[str], list[str], list[str]]:
    passed: list[str] = []
    failed: list[str] = []
    manual: list[str] = []
    household_size = int(profile["household_size"])
    income_limit = _household_value(MEDIAN_INCOME_60_2026, household_size)

    checks = [
        _check(19 <= int(profile["age"]) <= 34, "연령 19~34세 범위", "연령이 청년 월세지원 단순 범위를 벗어남"),
        _check(
            int(profile["monthly_income"]) <= income_limit,
            f"입력 월소득이 단순 기준 {income_limit:,}원 이하",
            f"입력 월소득 기준으로는 소득요건 초과 가능성이 높음({income_limit:,}원 기준)",
        ),
        _check(
            int(profile["assets"]) <= YOUTH_MONTHLY_RENT_ASSET_LIMIT,
            "청년가구 자산이 단순 기준 1억 2,200만원 이하",
            "청년가구 자산이 단순 기준 1억 2,200만원을 초과",
        ),
    ]
    for state, message in checks:
        (passed if state == "passed" else failed).append(message)

    _append_tri_state(
        status=str(profile.get("separate_household_status", "예" if bool(profile["separate_household"]) else "아니오")),
        passed=passed,
        failed=failed,
        manual=manual,
        yes_value="예",
        success="부모와 별도 거주로 입력됨",
        no_failure="핵심요건 미충족: 부모와 별도 거주 조건을 충족하지 않음",
        unknown_manual="부모와 별도 거주 여부 확인 필요",
    )
    _append_tri_state(
        status=str(profile.get("unhoused_status", "예" if bool(profile["unhoused"]) else "아니오")),
        passed=passed,
        failed=failed,
        manual=manual,
        yes_value="예",
        success="무주택으로 입력됨",
        no_failure="핵심요건 미충족: 무주택 조건을 충족하지 않음",
        unknown_manual="본인과 세대원의 주택 소유 여부 확인 필요",
    )

    manual.extend(
        [
            "원가구 소득·자산 기준과 예외 사유 확인",
            "최근 공고의 신청기간, 중복지원, 월세 환산 조건 확인",
            "입력값은 단순 월소득 기준이므로 공식 소득 산정 방식 재확인",
        ]
    )
    return passed, failed, manual


def _evaluate_happy_housing(profile: Mapping[str, Any]) -> tuple[list[str], list[str], list[str]]:
    passed: list[str] = []
    failed: list[str] = []
    manual: list[str] = []
    household_size = int(profile["household_size"])
    income_limit = _household_value(HAPPY_HOUSING_INCOME_LIMIT_2026, household_size)

    checks = [
        _check(19 <= int(profile["age"]) <= 39, "청년계층 연령 범위", "청년계층 연령 범위를 벗어남"),
        _check(
            int(profile["monthly_income"]) <= income_limit,
            f"가구 월소득이 단순 기준 {income_limit:,}원 이하",
            f"가구 월소득이 단순 기준 {income_limit:,}원을 초과",
        ),
        _check(
            int(profile["assets"]) <= HAPPY_HOUSING_YOUTH_ASSET_LIMIT,
            "총자산이 단순 기준 2억 5,100만원 이하",
            "총자산이 단순 기준 2억 5,100만원을 초과",
        ),
        _check(
            int(profile["car_value"]) <= PUBLIC_RENTAL_CAR_VALUE_LIMIT_2026,
            "자동차 가액이 단순 기준 4,542만원 이하",
            "자동차 가액이 단순 기준 4,542만원을 초과",
        ),
    ]
    for state, message in checks:
        (passed if state == "passed" else failed).append(message)

    _append_tri_state(
        status=str(profile.get("unmarried_status", "혼인 중이 아님" if bool(profile["unmarried"]) else "혼인 중")),
        passed=passed,
        failed=failed,
        manual=manual,
        yes_value="혼인 중이 아님",
        success="혼인 중이 아님으로 입력됨",
        no_failure=(
            "핵심요건 미충족: 혼인 중으로 입력되어 행복주택 미혼 청년계층 기준과 맞지 않음. "
            "신혼부부 계층은 별도 진단 필요"
        ),
        unknown_manual="혼인 상태 확인 필요",
    )
    _append_tri_state(
        status=str(profile.get("unhoused_status", "예" if bool(profile["unhoused"]) else "아니오")),
        passed=passed,
        failed=failed,
        manual=manual,
        yes_value="예",
        success="무주택으로 입력됨",
        no_failure="핵심요건 미충족: 무주택 조건을 충족하지 않음",
        unknown_manual="본인과 세대원의 주택 소유 여부 확인 필요",
    )

    manual.extend(
        [
            "대학생·취업준비생·사회초년생 등 세부 계층 증빙 확인",
            "모집지구, 경쟁률, 배점, 순위 조건 확인",
            "최신 입주자 모집공고와 지역 제한 확인",
            "특례나 우선공급 여부는 공식 공고에서 별도 확인",
        ]
    )
    return passed, failed, manual


def _evaluate_discovery(
    policy_id: str,
    profile: Mapping[str, Any],
) -> tuple[list[str], list[str], list[str]]:
    passed: list[str] = []
    failed: list[str] = []
    manual: list[str] = []

    age = int(profile["age"])
    deposit = int(profile["deposit"])
    rent = int(profile["monthly_rent"])
    unhoused_status = str(profile.get("unhoused_status", "예" if bool(profile["unhoused"]) else "아니오"))

    if policy_id == "YOUTH_JEONSE_LOAN":
        if deposit > 0 and rent == 0:
            passed.append("전세보증금 마련 목적의 계약 형태")
        elif deposit > 0 and rent > 0:
            failed.append("현재 입력은 보증부월세 계약이므로 전세자금 상품과 직접 매칭되지는 않음")
            manual.append("전세 매물로 계약 형태를 바꿀 경우 별도 검토 가능")
        else:
            failed.append("입력 보증금이 없어 전세자금 필요가 낮음")
        _append_tri_state(
            status=unhoused_status,
            passed=passed,
            failed=failed,
            manual=manual,
            yes_value="예",
            success="무주택으로 입력됨",
            no_failure="핵심요건 미충족: 무주택 조건을 충족하지 않음",
            unknown_manual="본인과 세대원의 주택 소유 여부 확인 필요",
        )
        (passed if 19 <= age <= 34 else manual).append("청년 대출 탐색 연령대" if 19 <= age <= 34 else "상품별 연령 요건 확인")
        manual.extend(["부부합산 소득·순자산·세대주 요건 확인", "임차보증금·면적·금리·취급은행 공식 심사"])

    elif policy_id == "YOUTH_DEPOSIT_RENT_LOAN":
        if deposit > 0 and rent > 0:
            passed.append("보증금과 월세를 함께 부담하는 계약 형태")
        else:
            failed.append("보증금과 월세를 함께 부담하는 입력이 아님")
        _append_tri_state(
            status=unhoused_status,
            passed=passed,
            failed=failed,
            manual=manual,
            yes_value="예",
            success="무주택으로 입력됨",
            no_failure="핵심요건 미충족: 무주택·세대주 등 기본요건 확인 필요",
            unknown_manual="본인과 세대원의 주택 소유 여부 확인 필요",
        )
        (passed if 19 <= age <= 34 else manual).append("청년 대출 탐색 연령대" if 19 <= age <= 34 else "상품별 연령 요건 확인")
        manual.extend(["소득·세대주·예비세대주 요건 확인", "대상주택과 보증금·월세 한도 확인", "취급은행 실제 대출 가능 여부 확인"])

    elif policy_id == "YOUTH_GUARANTEE_FEE":
        if deposit > 0:
            passed.append("반환보증 검토가 필요한 임차보증금이 있음")
        else:
            failed.append("보증금이 없어 반환보증료 지원 우선순위가 낮음")
        _append_tri_state(
            status=unhoused_status,
            passed=passed,
            failed=failed,
            manual=manual,
            yes_value="예",
            success="무주택으로 입력됨",
            no_failure="핵심요건 미충족: 무주택 조건을 충족하지 않음",
            unknown_manual="본인과 세대원의 주택 소유 여부 확인 필요",
        )
        manual.extend(["거주 지자체의 시행 공고 여부 확인", "반환보증 가입 가능성과 실제 보증료 규모 확인"])

    else:
        manual.append("공식 페이지에서 전체 신청 조건 확인")

    return passed, failed, manual


def _score(
    policy_id: str,
    rule_mode: str,
    passed: list[str],
    failed: list[str],
    manual: list[str],
) -> tuple[int, str, list[dict[str, int | str]], str]:
    base = 48
    passed_points = len(passed) * 8
    failed_penalty = len(failed) * -22
    manual_penalty = len(manual) * -3
    mode_bonus = 5 if rule_mode == "screening" else 0
    score = base + passed_points + failed_penalty + manual_penalty + mode_bonus
    if rule_mode == "screening":
        cap = 92
    else:
        cap = 84
    if failed:
        cap = min(cap, 68)
    has_core_failure = any("핵심요건 미충족" in message for message in failed)
    if has_core_failure:
        cap = min(cap, 35)
    score = max(0, min(cap, score))

    if has_core_failure:
        status = "핵심요건 미충족"
    elif failed:
        status = "현재 입력상 우선순위 낮음"
    elif any("주택 소유 여부 확인 필요" in message for message in manual):
        status = "확인 필요"
    elif score >= 80:
        status = "높은 적합도"
    else:
        status = "상세조건 확인"

    breakdown = [
        {"항목": "기본 탐색 점수", "점수": base},
        {"항목": f"입력상 충족 조건 {len(passed)}개", "점수": passed_points},
        {"항목": f"현재 입력과 불일치 {len(failed)}개", "점수": failed_penalty},
        {"항목": f"추가 확인 조건 {len(manual)}개", "점수": manual_penalty},
    ]
    if mode_bonus:
        breakdown.append({"항목": "사전진단형 정책 가점", "점수": mode_bonus})
    if score < base + passed_points + failed_penalty + manual_penalty + mode_bonus:
        breakdown.append({"항목": "불일치 조건에 따른 상한 적용", "점수": score})

    priority_note = "현재 입력 조건에서는 뚜렷한 하향 사유가 없습니다."
    if has_core_failure:
        priority_note = "현재 입력상 핵심요건을 충족하지 않아 추천 대상 가능성이 낮습니다."
    elif policy_id == "YOUTH_JEONSE_LOAN" and failed:
        priority_note = (
            "현재 입력은 보증부월세 계약이므로 전세자금대출과 계약 형태가 직접 일치하지 않습니다. "
            "전세 매물 검토 시 다시 진단하세요."
        )
    elif failed:
        priority_note = "현재 입력과 맞지 않는 조건이 있어 우선순위를 낮췄습니다."
    elif manual:
        priority_note = "입력상 큰 불일치는 없지만 공식 공고와 증빙 조건 확인이 남아 있습니다."

    return score, status, breakdown, priority_note


def recommend_policies(
    profile: Mapping[str, Any],
    *,
    catalog_path: Path = POLICY_CATALOG_PATH,
    limit: int | None = 5,
) -> list[dict[str, Any]]:
    required = {
        "age",
        "monthly_income",
        "assets",
        "deposit",
        "monthly_rent",
        "household_size",
        "car_value",
        "unhoused",
        "separate_household",
        "unmarried",
    }
    missing = required.difference(profile)
    if missing:
        raise ValueError(f"Missing policy profile fields: {sorted(missing)}")

    recommendations: list[PolicyRecommendation] = []
    for row in load_policy_catalog(catalog_path):
        policy_id = row["policy_id"]
        if policy_id == "YOUTH_MONTHLY_RENT_2026":
            passed, failed, manual = _evaluate_monthly_rent(profile)
        elif policy_id == "HAPPY_HOUSING_YOUTH_2026":
            passed, failed, manual = _evaluate_happy_housing(profile)
        else:
            passed, failed, manual = _evaluate_discovery(policy_id, profile)

        score, status, score_breakdown, priority_note = _score(
            policy_id, row["rule_mode"], passed, failed, manual
        )
        recommendations.append(
            PolicyRecommendation(
                policy_id=policy_id,
                name=row["name"],
                category=row["category"],
                description=row["description"],
                status=status,
                score=score,
                score_breakdown=score_breakdown,
                priority_note=priority_note,
                passed_checks=passed,
                failed_checks=failed,
                manual_checks=manual,
                official_url=row["official_url"],
                verified_at=row["verified_at"],
                source_note=row["source_note"],
            )
        )

    recommendations.sort(
        key=lambda item: (
            item.status == "높은 적합도",
            item.status == "상세조건 확인",
            item.status == "확인 필요",
            item.score,
        ),
        reverse=True,
    )
    if limit is not None:
        recommendations = recommendations[:limit]
    return [item.to_dict() for item in recommendations]
