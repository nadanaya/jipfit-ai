"""Generate a transparent synthetic dataset for the housing screening prototype."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.affordability import deposit_monthly_equivalent, minimum_living_cost
from src.config import REGION_INDEX_PATH, SYNTHETIC_DATA_PATH

RANDOM_SEED = 42


def load_region_table(path: Path = REGION_INDEX_PATH) -> pd.DataFrame:
    table = pd.read_csv(path)
    required = {"region", "demo_cost_index"}
    missing = required.difference(table.columns)
    if missing:
        raise ValueError(f"Region table is missing columns: {sorted(missing)}")
    return table


def generate_synthetic_scenarios(
    rows: int = 6_000,
    seed: int = RANDOM_SEED,
    region_path: Path = REGION_INDEX_PATH,
) -> pd.DataFrame:
    """Create reproducible fictional profiles and a burden-risk label.

    The target is derived from affordability and cash-flow constraints with a
    small amount of boundary noise. The dataset is for product prototyping only.
    """
    if rows < 300:
        raise ValueError("rows must be at least 300 for a stable demo split")

    rng = np.random.default_rng(seed)
    regions = load_region_table(region_path)
    region_names = regions["region"].to_numpy()
    region_indices = regions["demo_cost_index"].to_numpy(dtype=float)

    region_choice = rng.integers(0, len(regions), size=rows)
    region = region_names[region_choice]
    region_cost_index = region_indices[region_choice]

    age = rng.integers(19, 40, size=rows)
    household_size = rng.choice([1, 2, 3, 4], size=rows, p=[0.72, 0.20, 0.06, 0.02])
    is_unemployed = rng.binomial(1, 0.09, size=rows)

    monthly_income = rng.lognormal(mean=np.log(3_050_000), sigma=0.43, size=rows)
    monthly_income *= np.where(is_unemployed == 1, rng.uniform(0.35, 0.65, size=rows), 1.0)
    monthly_income = np.clip(monthly_income, 800_000, 9_000_000).round().astype(int)

    assets = rng.gamma(shape=1.8, scale=18_000_000, size=rows)
    assets += np.maximum(age - 24, 0) * rng.uniform(350_000, 1_100_000, size=rows)
    assets = np.clip(assets, 0, 300_000_000).round().astype(int)

    deposit = rng.gamma(shape=1.7, scale=13_000_000, size=rows) * region_cost_index
    deposit = np.clip(deposit, 0, 180_000_000).round().astype(int)

    base_rent = 470_000 * region_cost_index + rng.normal(0, 135_000, size=rows)
    deposit_discount = np.minimum(deposit * 0.0017, 220_000)
    monthly_rent = np.clip(base_rent - deposit_discount, 180_000, 1_650_000)
    monthly_rent = monthly_rent.round().astype(int)

    management_fee = rng.normal(90_000 + 22_000 * region_cost_index, 35_000, size=rows)
    management_fee = np.clip(management_fee, 25_000, 320_000).round().astype(int)

    debt_probability = np.clip(0.25 + (age - 19) * 0.012, 0.25, 0.52)
    has_debt = rng.binomial(1, debt_probability)
    monthly_debt_payment = has_debt * rng.gamma(shape=1.6, scale=190_000, size=rows)
    monthly_debt_payment = np.clip(monthly_debt_payment, 0, 1_600_000).round().astype(int)

    car_value = rng.gamma(shape=1.2, scale=7_500_000, size=rows)
    car_value *= rng.binomial(1, 0.38, size=rows)
    car_value = np.clip(car_value, 0, 60_000_000).round().astype(int)

    deposit_cost = np.array([deposit_monthly_equivalent(int(v)) for v in deposit])
    housing_cost = monthly_rent + management_fee + deposit_cost
    living_cost = np.array([minimum_living_cost(int(v)) for v in household_size])
    affordability_ratio = housing_cost / monthly_income
    disposable = monthly_income - housing_cost - monthly_debt_payment

    risk = np.zeros(rows, dtype=int)
    medium = (affordability_ratio > 0.30) | (disposable < living_cost * 0.90)
    high = (affordability_ratio > 0.45) | (disposable < living_cost * 0.58)
    risk[medium] = 1
    risk[high] = 2

    # Add modest uncertainty near decision boundaries so the model is not a
    # perfect copy of one hard rule and can demonstrate probabilistic output.
    boundary = (
        (np.abs(affordability_ratio - 0.30) < 0.035)
        | (np.abs(affordability_ratio - 0.45) < 0.035)
    )
    flip = boundary & (rng.random(rows) < 0.10)
    directions = rng.choice([-1, 1], size=rows)
    risk = np.where(flip, np.clip(risk + directions, 0, 2), risk)

    frame = pd.DataFrame(
        {
            "age": age,
            "monthly_income": monthly_income,
            "assets": assets,
            "deposit": deposit,
            "monthly_rent": monthly_rent,
            "management_fee": management_fee,
            "monthly_debt_payment": monthly_debt_payment,
            "household_size": household_size,
            "region": region,
            "region_cost_index": region_cost_index.round(3),
            "is_unemployed": is_unemployed,
            "car_value": car_value,
            "burden_class": risk,
        }
    )
    return frame


def write_dataset(
    output_path: Path = SYNTHETIC_DATA_PATH,
    rows: int = 6_000,
    seed: int = RANDOM_SEED,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = generate_synthetic_scenarios(rows=rows, seed=seed)
    frame.to_csv(output_path, index=False)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=6_000)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--output", type=Path, default=SYNTHETIC_DATA_PATH)
    args = parser.parse_args()

    path = write_dataset(args.output, rows=args.rows, seed=args.seed)
    frame = pd.read_csv(path)
    print(f"Synthetic dataset: {path}")
    print(f"Rows: {len(frame):,}")
    print("Class distribution:")
    print(frame["burden_class"].value_counts(normalize=True).sort_index().round(3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
