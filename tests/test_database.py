import sqlite3
from pathlib import Path

from src.database import initialize_database, log_analysis_run


def profile() -> dict[str, object]:
    return {
        "age": 27,
        "monthly_income": 3_000_000,
        "assets": 10_000_000,
        "region": "서울",
    }


def affordability() -> dict[str, object]:
    return {
        "monthly_housing_cost": 783_333,
        "affordability_ratio": 0.2611,
        "recommended_max_housing_cost": 900_000,
    }


def test_database_initializes_and_logs_with_parameter_binding(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    initialize_database(db)
    session_id = log_analysis_run(
        profile=profile(),
        affordability=affordability(),
        risk_class=1,
        policy_ids=["HAPPY_HOUSING_YOUTH_2026"],
        db_path=db,
    )
    assert session_id
    with sqlite3.connect(db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM analysis_runs").fetchone()[0]
        row = conn.execute(
            "SELECT region_code, risk_class FROM analysis_runs LIMIT 1"
        ).fetchone()
    assert count == 1
    assert row == ("SEOUL", 1)
