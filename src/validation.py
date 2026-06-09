"""
validation.py

Reads the dashboard mart CSV and runs 16 validation checks against
documented data contracts and financial coherence rules.

Writes: reports/validation_report.md

Every check produces one of three statuses:
  PASSED  — requirement is met; pipeline is safe to use.
  WARNING — acceptable for MVP; worth noting for future improvement.
  FAILED  — analytical integrity is broken; pipeline output should not be trusted.
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import COMPANIES, MART_CSV, PERIODS, PROJECT_ROOT, REPORTS_DIR

EXPECTED_ROWS = 6
EXPECTED_COLS = 22
EXPECTED_COMPANY_COUNT = len(COMPANIES)
EXPECTED_PERIOD_COUNT = len(PERIODS)

RAW_METRIC_COLS = [
    "revenue",
    "gross_profit",
    "operating_profit",
    "net_income",
    "total_assets",
    "total_debt",
    "cash",
    "operating_cash_flow",
]

VALIDATION_REPORT_PATH = REPORTS_DIR / "validation_report.md"

STATUS_ICON = {
    "PASSED":  "✅",
    "WARNING": "⚠️",
    "FAILED":  "❌",
}


# =============================================================================
# Step 1 — Load
# =============================================================================

def load_mart_csv() -> pd.DataFrame:
    """Load the mart CSV. Raises FileNotFoundError if it does not exist."""
    if not MART_CSV.exists():
        raise FileNotFoundError(
            f"Mart CSV not found: {MART_CSV}\n"
            "Run src/export_mart.py first."
        )
    return pd.read_csv(MART_CSV)


# =============================================================================
# Step 2 — Run checks
# =============================================================================

def run_validation_checks(df: pd.DataFrame) -> list[dict]:
    """
    Run all 16 validation checks against the mart DataFrame.

    Returns a list of result dicts, each with:
      check_id  — sequential integer
      name      — short check description
      status    — PASSED | WARNING | FAILED
      detail    — human-readable explanation of the result
    """
    results: list[dict] = []

    def record(check_id: int, name: str, status: str, detail: str) -> None:
        results.append({
            "check_id": check_id,
            "name":     name,
            "status":   status,
            "detail":   detail,
        })

    # ------------------------------------------------------------------
    # Check 1 — Row count
    # ------------------------------------------------------------------
    n = len(df)
    if n == EXPECTED_ROWS:
        record(1, "Row count", "PASSED", f"{n} rows found (expected {EXPECTED_ROWS})")
    else:
        record(1, "Row count", "FAILED",
               f"Expected {EXPECTED_ROWS} rows, found {n}. "
               "Re-run database_loader.py and export_mart.py.")

    # ------------------------------------------------------------------
    # Check 2 — Column count
    # ------------------------------------------------------------------
    c = len(df.columns)
    if c == EXPECTED_COLS:
        record(2, "Column count", "PASSED",
               f"{c} columns found (expected {EXPECTED_COLS})")
    else:
        record(2, "Column count", "FAILED",
               f"Expected {EXPECTED_COLS} columns, found {c}. "
               f"Columns present: {list(df.columns)}")

    # ------------------------------------------------------------------
    # Check 3 — No nulls in raw metric columns
    # ------------------------------------------------------------------
    missing_raw = {col: int(df[col].isnull().sum())
                   for col in RAW_METRIC_COLS if col in df.columns}
    cols_with_nulls = {k: v for k, v in missing_raw.items() if v > 0}
    if not cols_with_nulls:
        record(3, "No nulls in raw metrics", "PASSED",
               "All 8 raw metric columns are fully populated.")
    else:
        record(3, "No nulls in raw metrics", "FAILED",
               f"Null values found: {cols_with_nulls}")

    # ------------------------------------------------------------------
    # Check 4 — No duplicate company-period combinations
    # ------------------------------------------------------------------
    dupes = df.duplicated(subset=["company_name", "period_label"]).sum()
    if dupes == 0:
        record(4, "No duplicate company-period rows", "PASSED",
               "Every (company_name, period_label) combination is unique.")
    else:
        record(4, "No duplicate company-period rows", "FAILED",
               f"{dupes} duplicate (company_name, period_label) pairs found.")

    # ------------------------------------------------------------------
    # Check 5 — All 3 companies present
    # ------------------------------------------------------------------
    actual_companies = df["company_name"].nunique()
    if actual_companies == EXPECTED_COMPANY_COUNT:
        names = sorted(df["company_name"].unique())
        record(5, "All companies present", "PASSED",
               f"{actual_companies} companies found: {names}")
    else:
        record(5, "All companies present", "FAILED",
               f"Expected {EXPECTED_COMPANY_COUNT} companies, "
               f"found {actual_companies}: {sorted(df['company_name'].unique())}")

    # ------------------------------------------------------------------
    # Check 6 — All 2 periods present
    # ------------------------------------------------------------------
    actual_periods = df["period_label"].nunique()
    if actual_periods == EXPECTED_PERIOD_COUNT:
        labels = sorted(df["period_label"].unique())
        record(6, "All periods present", "PASSED",
               f"{actual_periods} periods found: {labels}")
    else:
        record(6, "All periods present", "FAILED",
               f"Expected {EXPECTED_PERIOD_COUNT} periods, "
               f"found {actual_periods}: {sorted(df['period_label'].unique())}")

    # ------------------------------------------------------------------
    # Check 7 — Every company-period has exactly one row (grain check)
    # ------------------------------------------------------------------
    grain_counts = df.groupby(["company_name", "period_label"]).size()
    bad_grain = grain_counts[grain_counts != 1]
    if bad_grain.empty:
        record(7, "Grain integrity (one row per company-period)", "PASSED",
               "Every company-period combination has exactly 1 row.")
    else:
        record(7, "Grain integrity (one row per company-period)", "FAILED",
               f"Unexpected row counts for: {bad_grain.to_dict()}")

    # ------------------------------------------------------------------
    # Check 8 — gross_profit < revenue
    # ------------------------------------------------------------------
    if "gross_profit" in df.columns and "revenue" in df.columns:
        violated = df[df["gross_profit"] >= df["revenue"]]
        if violated.empty:
            record(8, "gross_profit < revenue", "PASSED",
                   "Gross profit is below revenue for all rows.")
        else:
            rows = violated[["company_name", "period_label"]].to_dict("records")
            record(8, "gross_profit < revenue", "FAILED",
                   f"gross_profit >= revenue in {len(violated)} rows: {rows}")
    else:
        record(8, "gross_profit < revenue", "WARNING",
               "Column missing — check skipped.")

    # ------------------------------------------------------------------
    # Check 9 — operating_profit < gross_profit
    # ------------------------------------------------------------------
    if "operating_profit" in df.columns and "gross_profit" in df.columns:
        violated = df[df["operating_profit"] >= df["gross_profit"]]
        if violated.empty:
            record(9, "operating_profit < gross_profit", "PASSED",
                   "Operating profit is below gross profit for all rows.")
        else:
            rows = violated[["company_name", "period_label"]].to_dict("records")
            record(9, "operating_profit < gross_profit", "FAILED",
                   f"operating_profit >= gross_profit in {len(violated)} rows: {rows}")
    else:
        record(9, "operating_profit < gross_profit", "WARNING",
               "Column missing — check skipped.")

    # ------------------------------------------------------------------
    # Check 10 — net_income < operating_profit
    # ------------------------------------------------------------------
    if "net_income" in df.columns and "operating_profit" in df.columns:
        violated = df[df["net_income"] >= df["operating_profit"]]
        if violated.empty:
            record(10, "net_income < operating_profit", "PASSED",
                   "Net income is below operating profit for all rows.")
        else:
            rows = violated[["company_name", "period_label"]].to_dict("records")
            record(10, "net_income < operating_profit", "FAILED",
                   f"net_income >= operating_profit in {len(violated)} rows: {rows}")
    else:
        record(10, "net_income < operating_profit", "WARNING",
               "Column missing — check skipped.")

    # ------------------------------------------------------------------
    # Check 11 — cash < total_assets
    # ------------------------------------------------------------------
    if "cash" in df.columns and "total_assets" in df.columns:
        violated = df[df["cash"] >= df["total_assets"]]
        if violated.empty:
            record(11, "cash < total_assets", "PASSED",
                   "Cash is below total assets for all rows.")
        else:
            rows = violated[["company_name", "period_label"]].to_dict("records")
            record(11, "cash < total_assets", "FAILED",
                   f"cash >= total_assets in {len(violated)} rows: {rows}")
    else:
        record(11, "cash < total_assets", "WARNING",
               "Column missing — check skipped.")

    # ------------------------------------------------------------------
    # Check 12 — total_debt < total_assets
    # ------------------------------------------------------------------
    if "total_debt" in df.columns and "total_assets" in df.columns:
        violated = df[df["total_debt"] >= df["total_assets"]]
        if violated.empty:
            record(12, "total_debt < total_assets", "PASSED",
                   "Total debt is below total assets for all rows.")
        else:
            rows = violated[["company_name", "period_label"]].to_dict("records")
            record(12, "total_debt < total_assets", "FAILED",
                   f"total_debt >= total_assets in {len(violated)} rows: {rows}")
    else:
        record(12, "total_debt < total_assets", "WARNING",
               "Column missing — check skipped.")

    # ------------------------------------------------------------------
    # Check 13 — FY2024 revenue_growth_pct is NULL
    # ------------------------------------------------------------------
    if "revenue_growth_pct" in df.columns:
        fy2024 = df[df["period_label"] == "FY2024"]
        if fy2024.empty:
            record(13, "FY2024 revenue_growth_pct is NULL", "WARNING",
                   "FY2024 rows not found — check skipped.")
        else:
            non_null = fy2024["revenue_growth_pct"].notna().sum()
            if non_null == 0:
                record(13, "FY2024 revenue_growth_pct is NULL", "PASSED",
                       "All FY2024 rows correctly have NULL revenue_growth_pct "
                       "(no prior period to compare against).")
            else:
                record(13, "FY2024 revenue_growth_pct is NULL", "FAILED",
                       f"{non_null} FY2024 rows have non-NULL revenue_growth_pct. "
                       "Check LAG() window function in mart SQL.")
    else:
        record(13, "FY2024 revenue_growth_pct is NULL", "WARNING",
               "Column missing — check skipped.")

    # ------------------------------------------------------------------
    # Check 14 — FY2025 revenue_growth_pct is populated
    # ------------------------------------------------------------------
    if "revenue_growth_pct" in df.columns:
        fy2025 = df[df["period_label"] == "FY2025"]
        if fy2025.empty:
            record(14, "FY2025 revenue_growth_pct is populated", "WARNING",
                   "FY2025 rows not found — check skipped.")
        else:
            null_count = fy2025["revenue_growth_pct"].isna().sum()
            if null_count == 0:
                values = fy2025.set_index("company_name")["revenue_growth_pct"].to_dict()
                record(14, "FY2025 revenue_growth_pct is populated", "PASSED",
                       f"All FY2025 growth values are present: "
                       f"{', '.join(f'{k}: {v}%' for k, v in values.items())}")
            else:
                record(14, "FY2025 revenue_growth_pct is populated", "FAILED",
                       f"{null_count} FY2025 rows have NULL revenue_growth_pct.")
    else:
        record(14, "FY2025 revenue_growth_pct is populated", "WARNING",
               "Column missing — check skipped.")

    # ------------------------------------------------------------------
    # Check 15 — risk_keyword_count is 0 (synthetic MVP)
    # ------------------------------------------------------------------
    if "risk_keyword_count" in df.columns:
        non_zero = (df["risk_keyword_count"] != 0).sum()
        if non_zero == 0:
            record(15, "risk_keyword_count is 0 (synthetic MVP)", "PASSED",
                   "All rows have risk_keyword_count = 0, as expected for the "
                   "synthetic MVP (fact_risk_keyword is empty).")
        else:
            record(15, "risk_keyword_count is 0 (synthetic MVP)", "WARNING",
                   f"{non_zero} rows have risk_keyword_count != 0. "
                   "Expected in synthetic MVP. Verify if real documents have been loaded.")
    else:
        record(15, "risk_keyword_count is 0 (synthetic MVP)", "WARNING",
               "Column missing — check skipped.")

    # ------------------------------------------------------------------
    # Check 16 — Percentage KPIs within reasonable ranges (0–100)
    # ------------------------------------------------------------------
    pct_cols = {
        "gross_margin_pct":     (0, 100),
        "operating_margin_pct": (0, 100),
        "net_margin_pct":       (0, 100),
        "debt_to_assets_pct":   (0, 100),
    }
    out_of_range: list[str] = []
    for col, (lo, hi) in pct_cols.items():
        if col not in df.columns:
            continue
        values = df[col].dropna()
        bad = values[(values < lo) | (values > hi)]
        if not bad.empty:
            out_of_range.append(f"{col}: {bad.tolist()}")

    if not out_of_range:
        record(16, "Percentage KPIs within 0–100 range", "PASSED",
               "gross_margin_pct, operating_margin_pct, net_margin_pct, "
               "debt_to_assets_pct are all within expected bounds.")
    else:
        record(16, "Percentage KPIs within 0–100 range", "WARNING",
               f"Values outside 0–100 range: {out_of_range}. "
               "Negative margins are possible for distressed companies but "
               "unexpected in this synthetic dataset.")

    return results


# =============================================================================
# Step 3 — Write report
# =============================================================================

def write_validation_report(results: list[dict], df: pd.DataFrame) -> None:
    """Write the validation results to reports/validation_report.md."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    passed  = [r for r in results if r["status"] == "PASSED"]
    warnings = [r for r in results if r["status"] == "WARNING"]
    failed  = [r for r in results if r["status"] == "FAILED"]

    if failed:
        verdict = "❌ FAILED — One or more critical checks did not pass. Pipeline output should not be used until resolved."
    elif warnings:
        verdict = "⚠️ PASSED WITH WARNINGS — All critical checks passed. Warnings are noted for future improvement."
    else:
        verdict = "✅ FULLY PASSED — All validation checks passed. Pipeline output is analytically safe."

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: list[str] = []

    lines += [
        "# Validation Report",
        "",
        f"**Generated:** {ts}",
        f"**Dataset:** `{MART_CSV.relative_to(PROJECT_ROOT).as_posix()}`",
        f"**Rows:** {len(df)}",
        f"**Columns:** {len(df.columns)}",
        f"**Checks run:** {len(results)}",
        "",
        "---",
        "",
        "## Results",
        "",
        "| # | Check | Status | Detail |",
        "|---|---|:---:|---|",
    ]

    for r in results:
        icon   = STATUS_ICON[r["status"]]
        detail = r["detail"].replace("|", "\\|")
        lines.append(
            f"| {r['check_id']} | {r['name']} | {icon} {r['status']} | {detail} |"
        )

    lines += ["", "---", ""]

    # Failed checks section
    lines += ["## Failed Checks", ""]
    if failed:
        for r in failed:
            lines += [
                f"### ❌ Check {r['check_id']}: {r['name']}",
                "",
                f"{r['detail']}",
                "",
            ]
    else:
        lines += ["No failed checks.", ""]

    lines += ["---", ""]

    # Warning checks section
    lines += ["## Warnings", ""]
    if warnings:
        for r in warnings:
            lines += [
                f"### ⚠️ Check {r['check_id']}: {r['name']}",
                "",
                f"{r['detail']}",
                "",
            ]
    else:
        lines += ["No warnings.", ""]

    lines += ["---", ""]

    # Summary counts
    lines += [
        "## Summary",
        "",
        f"| Status | Count |",
        f"|---|---|",
        f"| ✅ PASSED  | {len(passed)} |",
        f"| ⚠️ WARNING | {len(warnings)} |",
        f"| ❌ FAILED  | {len(failed)} |",
        f"| **Total**  | **{len(results)}** |",
        "",
        "---",
        "",
        "## Final Verdict",
        "",
        verdict,
        "",
        "---",
        "",
        "> *This report is generated automatically from the pipeline mart CSV.*  ",
        "> *All data is synthetic sample data and does not represent real financial results.*",
        "",
    ]

    VALIDATION_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


# =============================================================================
# Step 4 — Print summary
# =============================================================================

def print_validation_summary(results: list[dict]) -> None:
    """Print a concise terminal summary of the validation run."""
    passed   = [r for r in results if r["status"] == "PASSED"]
    warnings = [r for r in results if r["status"] == "WARNING"]
    failed   = [r for r in results if r["status"] == "FAILED"]

    print()
    print("--- Validation results ---")
    for r in results:
        icon = STATUS_ICON[r["status"]]
        print(f"  [{r['check_id']:>2}] {icon} {r['status']:<7}  {r['name']}")

    print()
    print(f"  PASSED : {len(passed)}")
    print(f"  WARNING: {len(warnings)}")
    print(f"  FAILED : {len(failed)}")

    if failed:
        print()
        print("  FAILED CHECKS:")
        for r in failed:
            print(f"    [{r['check_id']}] {r['name']}: {r['detail']}")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    print("=" * 60)
    print("Validation Report Generator")
    print("=" * 60)
    print(f"Reading : {MART_CSV}")
    print(f"Writing : {VALIDATION_REPORT_PATH}")
    print()

    df = load_mart_csv()
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns.")

    results = run_validation_checks(df)
    print_validation_summary(results)

    write_validation_report(results, df)

    failed_count = sum(1 for r in results if r["status"] == "FAILED")
    print()
    if failed_count == 0:
        print(f"Validation report written: {VALIDATION_REPORT_PATH}")
    else:
        print(f"Validation report written with {failed_count} FAILED checks: {VALIDATION_REPORT_PATH}")

    print("=" * 60)


if __name__ == "__main__":
    main()
