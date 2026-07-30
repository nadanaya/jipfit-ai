"""Train and evaluate the burden-risk classifier."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import MODEL_PATH, REPORTS_DIR, RISK_LABELS, ROOT_DIR, SYNTHETIC_DATA_PATH

RANDOM_SEED = 42
FEATURE_NAMES = [
    "age",
    "monthly_income",
    "assets",
    "deposit",
    "monthly_rent",
    "management_fee",
    "monthly_debt_payment",
    "household_size",
    "region_cost_index",
    "is_unemployed",
    "car_value",
]
TARGET_NAME = "burden_class"


def _as_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _as_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_as_builtin(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def _evaluate(model: Any, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
    predictions = model.predict(x_test)
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "macro_f1": round(float(f1_score(y_test, predictions, average="macro")), 4),
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=[0, 1, 2]).tolist(),
        "classification_report": classification_report(
            y_test,
            predictions,
            labels=[0, 1, 2],
            target_names=[RISK_LABELS[i] for i in [0, 1, 2]],
            output_dict=True,
            zero_division=0,
        ),
    }


def train_and_save(
    data_path: Path = SYNTHETIC_DATA_PATH,
    model_path: Path = MODEL_PATH,
    reports_dir: Path = REPORTS_DIR,
) -> dict[str, Any]:
    if not data_path.exists():
        raise FileNotFoundError(
            f"Training data not found: {data_path}. Run python scripts/bootstrap.py first."
        )

    frame = pd.read_csv(data_path)
    required = set(FEATURE_NAMES + [TARGET_NAME])
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Training data is missing columns: {sorted(missing)}")

    x = frame[FEATURE_NAMES]
    y = frame[TARGET_NAME].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.20,
        stratify=y,
        random_state=RANDOM_SEED,
    )

    candidates: dict[str, Any] = {
        "majority_baseline": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1_500,
                        class_weight="balanced",
                        random_state=RANDOM_SEED,
                    ),
                ),
            ]
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=260,
            max_depth=12,
            min_samples_leaf=4,
            class_weight="balanced_subsample",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
    }

    model_metrics: dict[str, dict[str, Any]] = {}
    trained_models: dict[str, Any] = {}
    for name, model in candidates.items():
        model.fit(x_train, y_train)
        trained_models[name] = model
        model_metrics[name] = _evaluate(model, x_test, y_test)

    comparable = {k: v for k, v in model_metrics.items() if k != "majority_baseline"}
    best_name = max(comparable, key=lambda key: comparable[key]["macro_f1"])
    best_model = trained_models[best_name]

    created_at = datetime.now(UTC).isoformat()
    artifact = {
        "model": best_model,
        "model_name": best_name,
        "feature_names": FEATURE_NAMES,
        "class_labels": RISK_LABELS,
        "created_at_utc": created_at,
        "training_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "random_seed": RANDOM_SEED,
        "metrics": model_metrics[best_name],
        "data_notice": "합성 데이터로 학습한 참고용 분류 모델입니다. 실제 대출 승인이나 정책 수급 자격을 확정하지 않습니다.",
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_path)

    reports_dir.mkdir(parents=True, exist_ok=True)
    metrics_payload = {
        "generated_at_utc": created_at,
        "dataset": str(data_path.resolve().relative_to(ROOT_DIR.resolve())) if data_path.resolve().is_relative_to(ROOT_DIR.resolve()) else str(data_path),
        "rows": int(len(frame)),
        "class_distribution": {
            str(k): int(v) for k, v in y.value_counts().sort_index().items()
        },
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "selected_model": best_name,
        "feature_names": FEATURE_NAMES,
        "models": _as_builtin(model_metrics),
        "warning": "Metrics are measured on synthetic data and do not establish real-world financial validity.",
    }
    (reports_dir / "metrics.json").write_text(
        json.dumps(metrics_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    best_predictions = best_model.predict(x_test)
    errors = x_test.copy()
    errors["actual"] = y_test.to_numpy()
    errors["predicted"] = best_predictions
    errors = errors[errors["actual"] != errors["predicted"]].head(20)
    error_lines = [
        "# 오류 분석",
        "",
        "이 문서는 합성 테스트셋에서 선택 모델이 틀린 사례를 기록합니다.",
        "실제 금융·주거 의사결정의 정확도를 의미하지 않습니다.",
        "",
        f"- 선택 모델: `{best_name}`",
        f"- 오류 표본 수(전체 테스트셋): `{int((best_predictions != y_test.to_numpy()).sum())}`",
        "- 주된 위험: 경계 구간에 의도적으로 넣은 노이즈, 합성 분포와 현실 분포의 차이",
        "",
        "## 앞선 오분류 사례",
        "",
    ]
    if errors.empty:
        error_lines.append("오분류가 없습니다. 합성 규칙 과적합 가능성을 우선 점검해야 합니다.")
    else:
        error_lines.append(errors.to_markdown(index=False))
    error_lines.extend(
        [
            "",
            "## 개선 우선순위",
            "",
            "1. 익명화된 실제 월별 현금흐름 데이터로 외부 검증",
            "2. 지역별 실거래 임대료와 관리비 데이터 연결",
            "3. 직업 안정성·비정기 지출·부양 여부 등 변수 추가",
            "4. 성별·출신지 등 불필요한 민감정보를 사용하지 않는 공정성 점검",
        ]
    )
    (reports_dir / "error-analysis.md").write_text(
        "\n".join(error_lines) + "\n", encoding="utf-8"
    )

    return metrics_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=SYNTHETIC_DATA_PATH)
    parser.add_argument("--model", type=Path, default=MODEL_PATH)
    parser.add_argument("--reports", type=Path, default=REPORTS_DIR)
    args = parser.parse_args()

    metrics = train_and_save(args.data, args.model, args.reports)
    selected = metrics["selected_model"]
    selected_metrics = metrics["models"][selected]
    print(f"Selected model: {selected}")
    print(f"Accuracy: {selected_metrics['accuracy']:.4f}")
    print(f"Macro F1: {selected_metrics['macro_f1']:.4f}")
    print(f"Saved model: {args.model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
