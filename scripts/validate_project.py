#!/usr/bin/env python3
"""Run reproducible project validation and write a machine-readable report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "README.md",
    "app.py",
    "requirements.txt",
    "models/burden_model.joblib",
    "reports/metrics.json",
    "data/processed/synthetic_housing_scenarios.csv",
    "data/processed/policy_catalog.csv",
    "sql/schema.sql",
    "sql/seed.sql",
    "sql/queries.sql",
    "sql/tests.sql",
    "docs/demo-script.md",
]


def run_step(name: str, command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "name": name,
        "command": command,
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "stdout": completed.stdout[-6000:],
        "stderr": completed.stderr[-6000:],
    }


def validate_metrics() -> dict[str, object]:
    path = ROOT / "reports" / "metrics.json"
    if not path.exists():
        return {"name": "metrics_gate", "status": "failed", "error": f"Missing {path}"}
    data = json.loads(path.read_text(encoding="utf-8"))
    selected = data["selected_model"]
    model_f1 = float(data["models"][selected]["macro_f1"])
    baseline_f1 = float(data["models"]["majority_baseline"]["macro_f1"])
    passed = model_f1 >= baseline_f1 + 0.15 and model_f1 >= 0.75
    return {
        "name": "metrics_gate",
        "status": "passed" if passed else "failed",
        "selected_model": selected,
        "macro_f1": model_f1,
        "baseline_macro_f1": baseline_f1,
        "requirement": "selected >= baseline + 0.15 and selected >= 0.75",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "reports" / "project-validation.json",
    )
    args = parser.parse_args()

    missing = [relative for relative in REQUIRED_FILES if not (ROOT / relative).exists()]
    checks: list[dict[str, object]] = [
        {
            "name": "required_files",
            "status": "passed" if not missing else "failed",
            "missing": missing,
        }
    ]

    checks.append(
        run_step(
            "python_compile",
            [sys.executable, "-m", "compileall", "-q", "app.py", "src", "scripts", "tests"],
        )
    )
    checks.append(
        run_step(
            "sqlite_validation",
            [
                sys.executable,
                "scripts/validate_sqlite.py",
                "--schema",
                "sql/schema.sql",
                "--seed",
                "sql/seed.sql",
                "--queries",
                "sql/queries.sql",
                "--tests",
                "sql/tests.sql",
                "--report",
                "sql/validation-report.json",
            ],
        )
    )
    checks.append(run_step("pytest", [sys.executable, "-m", "pytest"]))
    checks.append(run_step("cli_demo", [sys.executable, "scripts/run_demo.py"]))
    checks.append(validate_metrics())

    failed = [check for check in checks if check.get("status") != "passed"]
    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "project": "JipFit AI",
        "team": "OneRoof Lab",
        "status": "failed" if failed else "passed",
        "checks": checks,
        "limitations": [
            "Model metrics are based on synthetic data.",
            "Streamlit browser interaction is not covered by unit tests.",
            "Policy recommendations remain pre-screening only.",
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    for check in checks:
        print(f"[{check['status'].upper():6}] {check['name']}")
        if check.get("status") != "passed":
            print(json.dumps(check, ensure_ascii=False, indent=2))
    print(f"Report: {args.report}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
