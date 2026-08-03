"""Project paths and stable labels used across the application."""

from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT_DIR / "models"
REPORTS_DIR = ROOT_DIR / "reports"
SQL_DIR = ROOT_DIR / "sql"

MODEL_PATH = Path(os.getenv("JIPFIT_MODEL_PATH", MODELS_DIR / "burden_model.joblib"))
DATABASE_PATH = Path(os.getenv("JIPFIT_DB_PATH", DATA_DIR / "jipfit_demo.db"))
POLICY_CATALOG_PATH = PROCESSED_DATA_DIR / "policy_catalog.csv"
REGION_INDEX_PATH = PROCESSED_DATA_DIR / "regional_cost_index.csv"
SYNTHETIC_DATA_PATH = PROCESSED_DATA_DIR / "synthetic_housing_scenarios.csv"

RISK_LABELS = {
    0: "안정",
    1: "주의",
    2: "위험",
}

RISK_DESCRIPTIONS = {
    0: "순수 주거비와 부채상환을 함께 보아도 현재 계획이 비교적 안정적인 범위에 있습니다.",
    1: "순수 주거비는 감당 가능해 보여도 부채상환을 포함한 통합 고정비를 추가 점검해야 합니다.",
    2: "현재 계획은 현금흐름 압박이 커서 월세·보증금·부채 조건을 다시 조정하는 편이 안전합니다.",
}
