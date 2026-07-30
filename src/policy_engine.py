"""Rule-based pre-screening and policy discovery for youth housing support.

Only conditions that were clearly available from official MyHome pages are used
for hard checks. Remaining conditions are surfaced as manual checks rather than
silently assumed. This is a discovery aid, not an eligibility determination.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from src.config import POLICY_CATALOG_PATH

# 2026 MyHome youth-monthly-rent self-diagnosis values (KRW/month).
MEDIAN_INCOME_60_2026 = {
    1: 1_538_543,
    2: 2_519_575,
    3: 3_215_422,
    4: 3_896_843,
    5: 4_534_031,
    6: 5_133_571,
}

# 2026 public-rental income reference used for the simplified Happiness Housing
# check. One-person and two-person values include the published percentage add-on.
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
    # Conservative linear extension for UI continuity; official confirmation is
    # always required for households above the table.
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


def _evaluate_monthly_rent(profile: Mapping[str, Any]) -> tuple[list[str], list[str], list[str]]:
    passed: list[str] = []
    failed: list[str] = []
    manual: list[str] = []
    household_size = int(profile["household_size"])
    income_limit = _household_value(MEDIAN_INCOME_60_2026, household_size)

    checks = [
        _check(19 <= int(profile["age"]) <= 34, "2026년 기준 연령 19~34세 범위", "연령이 2026년 청년월세 사전진단 범위를 벗어남"),
        _check(bool(profile["separate_household"]), "부모와 별도 거주", "부모와 별도 거주 조건 확인 필요"),
        _check(bool(profile["unhoused"]), "무주택으로 입력됨", "무주택 조건과 맞지 않음"),
        _check(int(profile["monthly_income"]) <= income_limit, f"청년가구 월소득이 {income_limit:,}원 이하", f"청년가구 월소득이 단순화 기준 {income_limit:,}원을 초과"),
        _check(int(profile["assets"]) <= YOUTH_MONTHLY_RENT_ASSET_LIMIT, "청년가구 자산이 1억 2,200만원 이하", "청년가구 자산이 단순화 기준 1억 2,200만원을 초과"),
    ]
    for state, message in checks:
        (passed if state == "passed" else failed).append(message)

    manual.extend(
        [
            "원가구 소득·재산 기준과 예외 사유 확인",
            "생애 24개월 수혜 여부 및 중복 월세지원 여부 확인",
            "임대차계약·보증금·월세 환산 조건을 공식 자가진단에서 확인",
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
        _check(19 <= int(profile["age"]) <= 39, "청년계층 연령 19~39세 범위", "청년계층 연령 범위를 벗어남"),
        _check(bool(profile["unmarried"]), "혼인 중이 아닌 것으로 입력됨", "청년계층의 혼인 조건과 맞지 않음"),
        _check(bool(profile["unhoused"]), "무주택으로 입력됨", "무주택 조건과 맞지 않음"),
        _check(int(profile["monthly_income"]) <= income_limit, f"가구 월소득이 단순화 기준 {income_limit:,}원 이하", f"가구 월소득이 단순화 기준 {income_limit:,}원을 초과"),
        _check(int(profile["assets"]) <= HAPPY_HOUSING_YOUTH_ASSET_LIMIT, "총자산이 2억 5,100만원 이하", "총자산이 단순화 기준 2억 5,100만원을 초과"),
        _check(int(profile["car_value"]) <= PUBLIC_RENTAL_CAR_VALUE_LIMIT_2026, "자동차 가액이 4,542만원 이하", "자동차 가액이 단순화 기준 4,542만원을 초과"),
    ]
    for state, message in checks:
        (passed if state == "passed" else failed).append(message)

    manual.extend(
        [
            "대학생·취업준비생·사회초년생 등 세부 계층 증빙 확인",
            "세대 범위와 실제 소득 산정 방식 확인",
            "희망 지역의 최신 입주자 모집공고 확인",
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
    unhoused = bool(profile["unhoused"])

    if policy_id == "YOUTH_JEONSE_LOAN":
        state, message = (
            ("passed", "전세·보증금 자금 수요가 있음")
            if deposit > 0
            else ("failed", "입력된 보증금이 없어 전세자금 수요가 낮음")
        )
        (passed if state == "passed" else failed).append(message)
        (passed if unhoused else failed).append("무주택으로 입력됨" if unhoused else "무주택 조건 확인 필요")
        if 19 <= age <= 34:
            passed.append("청년 대출 탐색 우선 연령대")
        else:
            manual.append("상품별 연령 요건 확인")
        manual.extend(["부부합산 연소득·순자산·세대주 요건 확인", "임차보증금·면적·대출한도·금리 공식 심사"])

    elif policy_id == "YOUTH_DEPOSIT_RENT_LOAN":
        if deposit > 0 and rent > 0:
            passed.append("보증금과 월세를 함께 부담하는 계약 형태")
        else:
            failed.append("보증금과 월세를 함께 부담하는 입력이 아님")
        (passed if unhoused else failed).append("무주택으로 입력됨" if unhoused else "무주택 조건 확인 필요")
        if 19 <= age <= 34:
            passed.append("청년 대출 탐색 우선 연령대")
        else:
            manual.append("상품별 연령 요건 확인")
        manual.extend(["소득·순자산·세대주 요건 확인", "대상주택과 보증금·월세 한도 확인"])

    elif policy_id == "YOUTH_GUARANTEE_FEE":
        if deposit > 0:
            passed.append("보증금 반환보증을 검토할 수 있는 임차보증금이 있음")
        else:
            failed.append("보증금이 없어 반환보증료 지원 우선순위가 낮음")
        (passed if unhoused else failed).append("무주택으로 입력됨" if unhoused else "무주택 조건 확인 필요")
        manual.extend(["거주 지역의 시행 공고 여부 확인", "연령·소득·보증금과 보증 가입 요건 확인"])

    else:
        manual.append("공식 페이지에서 전체 신청 조건 확인")

    return passed, failed, manual


def _score(rule_mode: str, passed: list[str], failed: list[str], manual: list[str]) -> tuple[int, str]:
    score = 55 + len(passed) * 8 - len(failed) * 24 - len(manual) * 2
    if rule_mode == "screening":
        score += 7
    score = max(0, min(100, score))

    if failed:
        status = "현재 입력상 우선순위 낮음"
    elif rule_mode == "screening":
        status = "사전진단 통과"
    else:
        status = "상세조건 확인"
    return score, status


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

        score, status = _score(row["rule_mode"], passed, failed, manual)
        recommendations.append(
            PolicyRecommendation(
                policy_id=policy_id,
                name=row["name"],
                category=row["category"],
                description=row["description"],
                status=status,
                score=score,
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
            item.status == "사전진단 통과",
            item.status == "상세조건 확인",
            item.score,
        ),
        reverse=True,
    )
    if limit is not None:
        recommendations = recommendations[:limit]
    return [item.to_dict() for item in recommendations]
