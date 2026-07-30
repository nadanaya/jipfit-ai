"""Inference utilities and a command-line demo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd

from src.config import MODEL_PATH, RISK_DESCRIPTIONS, RISK_LABELS


def load_model_artifact(model_path: Path = MODEL_PATH) -> dict[str, Any]:
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}. Run python scripts/bootstrap.py first."
        )
    artifact = joblib.load(model_path)
    required = {"model", "feature_names", "class_labels"}
    missing = required.difference(artifact)
    if missing:
        raise ValueError(f"Invalid model artifact; missing keys: {sorted(missing)}")
    return artifact


def predict_burden(
    features: Mapping[str, int | float],
    model_path: Path = MODEL_PATH,
) -> dict[str, Any]:
    artifact = load_model_artifact(model_path)
    feature_names = list(artifact["feature_names"])
    missing = [name for name in feature_names if name not in features]
    if missing:
        raise ValueError(f"Missing model features: {missing}")

    row = pd.DataFrame([{name: features[name] for name in feature_names}])
    model = artifact["model"]
    predicted = int(model.predict(row)[0])

    probabilities: dict[str, float] = {}
    if hasattr(model, "predict_proba"):
        raw = model.predict_proba(row)[0]
        classes = [int(v) for v in model.classes_]
        probabilities = {
            RISK_LABELS[class_id]: round(float(probability), 4)
            for class_id, probability in zip(classes, raw, strict=True)
        }

    return {
        "class_id": predicted,
        "label": RISK_LABELS[predicted],
        "description": RISK_DESCRIPTIONS[predicted],
        "probabilities": probabilities,
        "model_name": artifact.get("model_name", "unknown"),
        "model_created_at_utc": artifact.get("created_at_utc"),
        "data_notice": artifact.get("data_notice"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--age", type=int, default=27)
    parser.add_argument("--income", type=int, default=3_000_000)
    parser.add_argument("--assets", type=int, default=10_000_000)
    parser.add_argument("--deposit", type=int, default=10_000_000)
    parser.add_argument("--rent", type=int, default=650_000)
    parser.add_argument("--management", type=int, default=100_000)
    parser.add_argument("--debt", type=int, default=200_000)
    parser.add_argument("--household-size", type=int, default=1)
    parser.add_argument("--region-index", type=float, default=1.25)
    parser.add_argument("--unemployed", action="store_true")
    parser.add_argument("--car-value", type=int, default=0)
    parser.add_argument("--model", type=Path, default=MODEL_PATH)
    args = parser.parse_args()

    features = {
        "age": args.age,
        "monthly_income": args.income,
        "assets": args.assets,
        "deposit": args.deposit,
        "monthly_rent": args.rent,
        "management_fee": args.management,
        "monthly_debt_payment": args.debt,
        "household_size": args.household_size,
        "region_cost_index": args.region_index,
        "is_unemployed": int(args.unemployed),
        "car_value": args.car_value,
    }
    print(json.dumps(predict_burden(features, args.model), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
