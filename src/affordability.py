"""Transparent housing-affordability calculations.

The deterministic affordability engine is intentionally separate from the ML
model. It gives users an auditable recommendation, while the model estimates a
risk class from the same raw inputs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

DEPOSIT_ANNUAL_OPPORTUNITY_RATE = 0.04
RECOMMENDED_HOUSING_RATIO = 0.30
SAFETY_SAVINGS_RATE = 0.10

# Demo assumptions for the prototype, not government eligibility thresholds.
# Values are monthly minimum living-cost buffers in KRW.
MIN_LIVING_COST_BY_HOUSEHOLD = {
    1: 1_150_000,
    2: 1_750_000,
    3: 2_250_000,
    4: 2_700_000,
    5: 3_100_000,
    6: 3_450_000,
}


@dataclass(frozen=True)
class AffordabilityResult:
    monthly_housing_cost: int
    deposit_monthly_equivalent: int
    affordability_ratio: float
    total_fixed_cost_with_debt: int
    total_fixed_cost_ratio: float
    recommended_max_housing_cost: int
    monthly_gap_to_recommendation: int
    monthly_gap_to_total_recommendation: int
    disposable_after_housing_and_debt: int
    minimum_living_cost_buffer: int
    rule_risk_class: int

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


def _require_non_negative(name: str, value: int | float) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def minimum_living_cost(household_size: int) -> int:
    """Return the prototype living-cost buffer for a household size."""
    if household_size < 1:
        raise ValueError("household_size must be at least 1")
    capped = min(household_size, max(MIN_LIVING_COST_BY_HOUSEHOLD))
    base = MIN_LIVING_COST_BY_HOUSEHOLD[capped]
    if household_size <= capped:
        return base
    return base + (household_size - capped) * 300_000


def deposit_monthly_equivalent(
    deposit: int,
    annual_rate: float = DEPOSIT_ANNUAL_OPPORTUNITY_RATE,
) -> int:
    """Convert a deposit into a monthly opportunity-cost estimate."""
    _require_non_negative("deposit", deposit)
    _require_non_negative("annual_rate", annual_rate)
    return int(round(deposit * annual_rate / 12))


def calculate_affordability(
    *,
    monthly_income: int,
    deposit: int,
    monthly_rent: int,
    management_fee: int,
    monthly_debt_payment: int,
    household_size: int,
    deposit_annual_rate: float = DEPOSIT_ANNUAL_OPPORTUNITY_RATE,
    recommended_ratio: float = RECOMMENDED_HOUSING_RATIO,
    savings_rate: float = SAFETY_SAVINGS_RATE,
) -> AffordabilityResult:
    """Calculate current burden and a conservative monthly housing budget.

    The result is a planning aid, not a loan approval or statutory benefit
    decision. All monetary values are KRW per month unless noted otherwise.
    """
    if monthly_income <= 0:
        raise ValueError("monthly_income must be greater than 0")
    for name, value in (
        ("deposit", deposit),
        ("monthly_rent", monthly_rent),
        ("management_fee", management_fee),
        ("monthly_debt_payment", monthly_debt_payment),
    ):
        _require_non_negative(name, value)
    if not 0 < recommended_ratio <= 1:
        raise ValueError("recommended_ratio must be between 0 and 1")
    if not 0 <= savings_rate < 1:
        raise ValueError("savings_rate must be between 0 and 1")

    living_buffer = minimum_living_cost(household_size)
    deposit_cost = deposit_monthly_equivalent(deposit, deposit_annual_rate)
    housing_cost = monthly_rent + management_fee + deposit_cost
    total_fixed_cost = housing_cost + monthly_debt_payment
    affordability_ratio = housing_cost / monthly_income
    total_fixed_cost_ratio = total_fixed_cost / monthly_income
    disposable = monthly_income - housing_cost - monthly_debt_payment

    ratio_cap = int(monthly_income * recommended_ratio)
    recommended = max(0, ratio_cap)
    gap = recommended - housing_cost
    total_gap = recommended - total_fixed_cost

    if (
        affordability_ratio <= 0.30
        and total_fixed_cost_ratio <= 0.30
        and disposable >= living_buffer * 0.90
    ):
        rule_class = 0
    elif (
        affordability_ratio <= 0.45
        and total_fixed_cost_ratio <= 0.45
        and disposable >= living_buffer * 0.60
    ):
        rule_class = 1
    else:
        rule_class = 2

    return AffordabilityResult(
        monthly_housing_cost=int(housing_cost),
        deposit_monthly_equivalent=int(deposit_cost),
        affordability_ratio=round(float(affordability_ratio), 4),
        total_fixed_cost_with_debt=int(total_fixed_cost),
        total_fixed_cost_ratio=round(float(total_fixed_cost_ratio), 4),
        recommended_max_housing_cost=int(recommended),
        monthly_gap_to_recommendation=int(gap),
        monthly_gap_to_total_recommendation=int(total_gap),
        disposable_after_housing_and_debt=int(disposable),
        minimum_living_cost_buffer=int(living_buffer),
        rule_risk_class=int(rule_class),
    )
