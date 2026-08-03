from src.policy_engine import recommend_policies


def base_profile() -> dict[str, object]:
    return {
        "age": 25,
        "monthly_income": 1_400_000,
        "assets": 20_000_000,
        "deposit": 10_000_000,
        "monthly_rent": 450_000,
        "household_size": 1,
        "car_value": 0,
        "unhoused": True,
        "separate_household": True,
        "unmarried": True,
    }


def test_monthly_rent_support_can_pass_simplified_screening() -> None:
    results = recommend_policies(base_profile())
    policy = next(item for item in results if item["policy_id"] == "YOUTH_MONTHLY_RENT_2026")
    assert policy["status"] == "높은 적합도"
    assert policy["score"] < 100
    assert policy["failed_checks"] == []
    assert len(policy["manual_checks"]) >= 1


def test_high_income_is_explained_as_failed_check() -> None:
    profile = base_profile()
    profile["monthly_income"] = 4_000_000
    results = recommend_policies(profile)
    policy = next(item for item in results if item["policy_id"] == "YOUTH_MONTHLY_RENT_2026")
    assert policy["status"] == "현재 입력상 우선순위 낮음"
    assert any("소득요건" in message for message in policy["failed_checks"])


def test_policy_results_always_keep_official_link_and_date() -> None:
    results = recommend_policies(base_profile())
    assert all(item["official_url"].startswith("https://") for item in results)
    assert all(item["verified_at"] == "2026-07-29" for item in results)


def test_monthly_contract_downgrades_jeonse_loan_priority() -> None:
    results = recommend_policies(base_profile())
    jeonse = next(item for item in results if item["policy_id"] == "YOUTH_JEONSE_LOAN")
    deposit_rent = next(item for item in results if item["policy_id"] == "YOUTH_DEPOSIT_RENT_LOAN")
    assert jeonse["status"] == "현재 입력상 우선순위 낮음"
    assert deposit_rent["score"] > jeonse["score"]
