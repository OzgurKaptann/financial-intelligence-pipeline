"""
run_pipeline.py — Runs the complete Financial Intelligence Pipeline end-to-end.

Execution order:
  1. synthetic_data_generator.py  → data/synthetic/synthetic_financial_metrics.csv
  2. database_loader.py           → data/final/financial_intelligence.sqlite
  3. export_mart.py               → data/final/mart_company_financial_performance.csv
  4. validation.py                → reports/validation_report.md
  5. report_generator.py          → reports/executive_summary.md

Stops immediately on any stage failure.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

STAGES = [
    {
        "name": "Stage 1 — Synthetic Data Generator",
        "script": PROJECT_ROOT / "src" / "synthetic_data_generator.py",
    },
    {
        "name": "Stage 2 — Database Loader",
        "script": PROJECT_ROOT / "src" / "database_loader.py",
    },
    {
        "name": "Stage 3 — Export Mart",
        "script": PROJECT_ROOT / "src" / "export_mart.py",
    },
    {
        "name": "Stage 4 — Validation",
        "script": PROJECT_ROOT / "src" / "validation.py",
    },
    {
        "name": "Stage 5 — Report Generator",
        "script": PROJECT_ROOT / "src" / "report_generator.py",
    },
]

FINAL_OUTPUTS = [
    PROJECT_ROOT / "data" / "synthetic" / "synthetic_financial_metrics.csv",
    PROJECT_ROOT / "data" / "final" / "financial_intelligence.sqlite",
    PROJECT_ROOT / "data" / "final" / "mart_company_financial_performance.csv",
    PROJECT_ROOT / "reports" / "validation_report.md",
    PROJECT_ROOT / "reports" / "executive_summary.md",
]


def print_header(text: str) -> None:
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)


def run_stage(stage: dict) -> None:
    """Run a single pipeline stage. Exits the process if the stage fails."""
    print_header(stage["name"])
    result = subprocess.run(
        [sys.executable, str(stage["script"])],
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        print()
        print(f"[FAILED] {stage['name']} exited with code {result.returncode}.")
        print("Pipeline stopped. Fix the error above and re-run.")
        sys.exit(result.returncode)
    print(f"\n[OK] {stage['name']} completed successfully.")


def print_final_outputs() -> None:
    print_header("Final Outputs")
    all_present = True
    for path in FINAL_OUTPUTS:
        exists = path.exists()
        status = "FOUND" if exists else "MISSING"
        print(f"  [{status}]  {path.relative_to(PROJECT_ROOT)}")
        if not exists:
            all_present = False
    if not all_present:
        print("\n[WARNING] One or more expected output files are missing.")
    return all_present


def main() -> None:
    print_header("Financial Intelligence Pipeline — Full Run")
    print(f"  Project root: {PROJECT_ROOT}")

    for stage in STAGES:
        run_stage(stage)

    all_present = print_final_outputs()

    print()
    if all_present:
        print("=" * 70)
        print("  PIPELINE COMPLETE — All stages passed. All outputs present.")
        print("=" * 70)
    else:
        print("=" * 70)
        print("  PIPELINE COMPLETE — Stages passed but some output files are missing.")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
