#!/usr/bin/env python3
"""Run one CLI analysis without starting Streamlit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.service import analyze_profile  # noqa: E402

PROFILE = {
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
    "unhoused_status": "예",
    "separate_household_status": "예",
    "unmarried_status": "혼인 중이 아님",
}


def main() -> int:
    result = analyze_profile(PROFILE, log_result=False)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
