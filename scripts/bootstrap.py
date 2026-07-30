#!/usr/bin/env python3
"""Create all local demo assets: data, SQLite database, model, and sample output."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    DATABASE_PATH,
    MODEL_PATH,
    REPORTS_DIR,
    SYNTHETIC_DATA_PATH,
)
from src.data_generation import write_dataset  # noqa: E402
from src.database import initialize_database  # noqa: E402
from src.service import analyze_profile  # noqa: E402
from src.train import train_and_save  # noqa: E402


def write_data_quality_report(frame: pd.DataFrame) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "missing_cells": int(frame.isna().sum().sum()),
        "duplicate_rows": int(frame.duplicated().sum()),
        "class_distribution": {
            str(k): int(v)
            for k, v in frame["burden_class"].value_counts().sort_index().items()
        },
        "numeric_ranges": {
            column: {
                "min": float(frame[column].min()),
                "max": float(frame[column].max()),
            }
            for column in [
                "age",
                "monthly_income",
                "assets",
                "deposit",
                "monthly_rent",
                "management_fee",
                "monthly_debt_payment",
                "region_cost_index",
                "car_value",
            ]
        },
        "notice": "All rows are synthetic and contain no real person or account data.",
    }
    path = REPORTS_DIR / "data-quality.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


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


def main() -> int:
    print("[1/5] Generating transparent synthetic data...")
    write_dataset(SYNTHETIC_DATA_PATH, rows=6_000, seed=42)
    frame = pd.read_csv(SYNTHETIC_DATA_PATH)
    quality_path = write_data_quality_report(frame)
    print(f"      {len(frame):,} rows -> {SYNTHETIC_DATA_PATH}")
    print(f"      quality report -> {quality_path}")

    print("[2/5] Initializing SQLite demo database...")
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
    initialize_database(DATABASE_PATH)
    print(f"      database -> {DATABASE_PATH}")

    print("[3/5] Training and evaluating candidate models...")
    metrics = train_and_save(SYNTHETIC_DATA_PATH, MODEL_PATH, REPORTS_DIR)
    chosen = metrics["selected_model"]
    score = metrics["models"][chosen]["macro_f1"]
    print(f"      selected {chosen} (macro F1={score:.4f})")

    print("[4/5] Creating a deterministic demo result...")
    result = analyze_profile(demo_profile(), log_result=True)
    assets_dir = ROOT / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    demo_path = assets_dir / "demo_result.json"
    demo_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"      demo result -> {demo_path}")

    print("[5/5] Bootstrap complete.")
    print("Next: streamlit run app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
