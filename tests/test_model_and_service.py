from pathlib import Path

from src.config import MODEL_PATH
from src.predict import load_model_artifact, predict_burden
from src.service import analyze_profile


def demo_profile() -> dict[str, object]:
    return {
        "age": 27,
        "monthly_income": 3_000_000,
        "assets": 10_000_000,
        "deposit": 10_000_000,
        "monthly_rent": 650_000,
        "management_fee": 100_000,
        "monthly_debt_payment": 200_000,
        "household_size": 1,
        "region": "서울",
        "is_unemployed": False,
        "car_value": 0,
        "unhoused": True,
        "separate_household": True,
        "unmarried": True,
    }


def test_model_artifact_exists_after_bootstrap() -> None:
    assert Path(MODEL_PATH).exists()
    artifact = load_model_artifact()
    assert artifact["model_name"] in {"logistic_regression", "random_forest"}
    assert len(artifact["feature_names"]) == 11


def test_predict_burden_returns_valid_probability_map() -> None:
    features = {
        "age": 27,
        "monthly_income": 3_000_000,
        "assets": 10_000_000,
        "deposit": 10_000_000,
        "monthly_rent": 650_000,
        "management_fee": 100_000,
        "monthly_debt_payment": 200_000,
        "household_size": 1,
        "region_cost_index": 1.35,
        "is_unemployed": 0,
        "car_value": 0,
    }
    result = predict_burden(features)
    assert result["class_id"] in {0, 1, 2}
    assert result["label"] in {"안정", "주의", "위험"}
    assert abs(sum(result["probabilities"].values()) - 1.0) < 0.01


def test_end_to_end_service_result(tmp_path: Path) -> None:
    result = analyze_profile(
        demo_profile(),
        log_result=True,
        db_path=tmp_path / "service.db",
    )
    assert result["affordability"]["monthly_housing_cost"] == 783_333
    assert result["affordability"]["total_fixed_cost_with_debt"] == 983_333
    assert result["affordability"]["total_fixed_cost_ratio"] == 0.3278
    assert result["model"]["label"] == "주의"
    assert len(result["policies"]) == 5
    assert len(result["action_plan"]) == 3
    assert result["session_id"]
