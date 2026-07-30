from src.affordability import calculate_affordability, deposit_monthly_equivalent


def test_deposit_monthly_equivalent_uses_four_percent_default() -> None:
    assert deposit_monthly_equivalent(12_000_000) == 40_000


def test_affordability_low_burden_case() -> None:
    result = calculate_affordability(
        monthly_income=4_500_000,
        deposit=10_000_000,
        monthly_rent=500_000,
        management_fee=80_000,
        monthly_debt_payment=0,
        household_size=1,
    )
    assert result.monthly_housing_cost == 613_333
    assert result.affordability_ratio < 0.2
    assert result.rule_risk_class == 0
    assert result.recommended_max_housing_cost > result.monthly_housing_cost


def test_affordability_high_burden_case() -> None:
    result = calculate_affordability(
        monthly_income=1_800_000,
        deposit=5_000_000,
        monthly_rent=900_000,
        management_fee=150_000,
        monthly_debt_payment=250_000,
        household_size=1,
    )
    assert result.affordability_ratio > 0.5
    assert result.rule_risk_class == 2
    assert result.monthly_gap_to_recommendation < 0
