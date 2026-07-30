"""SQLite initialization and privacy-minimized analysis logging."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.config import DATABASE_PATH, SQL_DIR


def initialize_database(
    db_path: Path = DATABASE_PATH,
    schema_path: Path = SQL_DIR / "schema.sql",
    seed_path: Path = SQL_DIR / "seed.sql",
) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema = schema_path.read_text(encoding="utf-8")
    seed = seed_path.read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema)
        conn.executescript(seed)
        conn.commit()
    return db_path


def region_code_for_name(region: str, db_path: Path = DATABASE_PATH) -> str:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT region_code FROM regions WHERE region_name = ?",
            (region,),
        ).fetchone()
    if row is None:
        raise ValueError(f"Unknown region: {region}")
    return str(row[0])


def log_analysis_run(
    *,
    profile: Mapping[str, Any],
    affordability: Mapping[str, Any],
    risk_class: int,
    policy_ids: Sequence[str],
    db_path: Path = DATABASE_PATH,
    session_id: str | None = None,
) -> str:
    """Store only the minimum numeric fields needed for demo analytics.

    No name, phone number, address, account number, or raw free-text input is
    collected. A random session ID is returned for debugging.
    """
    if not db_path.exists():
        initialize_database(db_path)
    anonymous_session = session_id or str(uuid.uuid4())
    region_code = region_code_for_name(str(profile["region"]), db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            INSERT INTO analysis_runs (
                session_id, age, monthly_income, assets, region_code,
                monthly_housing_cost, affordability_ratio,
                recommended_housing_cost, risk_class, policy_ids_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                anonymous_session,
                int(profile["age"]),
                int(profile["monthly_income"]),
                int(profile["assets"]),
                region_code,
                int(affordability["monthly_housing_cost"]),
                float(affordability["affordability_ratio"]),
                int(affordability["recommended_max_housing_cost"]),
                int(risk_class),
                json.dumps(list(policy_ids), ensure_ascii=False),
            ),
        )
        conn.commit()
    return anonymous_session
