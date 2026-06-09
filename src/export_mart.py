"""
export_mart.py

Creates (or refreshes) the mart view in SQLite, reads it into a DataFrame,
validates the shape and content, then exports to the dashboard-ready CSV.

Output: data/final/mart_company_financial_performance.csv
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DB_PATH, MART_CSV, PROJECT_ROOT

MART_SQL_PATH = PROJECT_ROOT / "sql" / "05_mart_company_financial_performance.sql"
MART_VIEW_NAME = "mart_company_financial_performance"

EXPECTED_ROWS = 6
EXPECTED_COMPANIES = 3
EXPECTED_PERIODS = 2

MART_REQUIRED_COLUMNS: list[str] = [
    "company_id",
    "company_name",
    "sector",
    "country",
    "period_id",
    "period_label",
    "revenue",
    "gross_profit",
    "operating_profit",
    "net_income",
    "total_assets",
    "total_debt",
    "cash",
    "operating_cash_flow",
    "revenue_growth_pct",
    "gross_margin_pct",
    "operating_margin_pct",
    "net_margin_pct",
    "debt_to_assets_pct",
    "cash_to_debt_pct",
    "operating_cash_flow_to_net_income",
    "risk_keyword_count",
]

# Columns shown in the terminal preview
PREVIEW_COLUMNS: list[str] = [
    "company_name",
    "period_label",
    "revenue",
    "revenue_growth_pct",
    "gross_margin_pct",
    "net_margin_pct",
    "debt_to_assets_pct",
    "cash_to_debt_pct",
    "risk_keyword_count",
]


# =============================================================================
# Step 1 — Create or refresh the mart view
# =============================================================================

def create_or_refresh_mart_view(conn: sqlite3.Connection) -> None:
    """
    Execute sql/05_mart_company_financial_performance.sql to drop and recreate
    the mart view.

    Uses executescript() because the file contains two statements
    (DROP VIEW + CREATE VIEW). executescript() issues an implicit COMMIT
    first, then runs all statements sequentially.

    Foreign keys are re-enabled after executescript() resets connection state.
    """
    if not MART_SQL_PATH.exists():
        raise FileNotFoundError(
            f"Mart SQL file not found: {MART_SQL_PATH}\n"
            "Expected location: sql/05_mart_company_financial_performance.sql"
        )

    sql = MART_SQL_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.execute("PRAGMA foreign_keys = ON")


# =============================================================================
# Step 2 — Read the mart view into a DataFrame
# =============================================================================

def load_mart_dataframe(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Read all rows from the mart view into a pandas DataFrame.

    Raises RuntimeError if the view does not exist in the database, which
    would indicate create_or_refresh_mart_view() was not called first.
    """
    view_exists = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='view' AND name=?",
        (MART_VIEW_NAME,),
    ).fetchone()[0]

    if not view_exists:
        raise RuntimeError(
            f"View '{MART_VIEW_NAME}' does not exist. "
            "Call create_or_refresh_mart_view() first."
        )

    return pd.read_sql_query(
        f"SELECT * FROM {MART_VIEW_NAME}",
        conn,
    )


# =============================================================================
# Step 3 — Validate the mart DataFrame
# =============================================================================

def validate_mart_dataframe(df: pd.DataFrame) -> None:
    """
    Validate the mart DataFrame against the expected shape and business rules.

    Raises ValueError with a descriptive message on the first failure found.
    """
    # --- column contract ---
    missing_cols = [c for c in MART_REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Mart is missing required columns: {missing_cols}")

    extra_cols = [c for c in df.columns if c not in MART_REQUIRED_COLUMNS]
    if extra_cols:
        raise ValueError(f"Mart has unexpected extra columns: {extra_cols}")

    # --- row count ---
    if len(df) != EXPECTED_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_ROWS} rows, got {len(df)}. "
            "Re-run database_loader.py then export_mart.py."
        )

    # --- distinct companies and periods ---
    actual_companies = df["company_name"].nunique()
    if actual_companies != EXPECTED_COMPANIES:
        raise ValueError(
            f"Expected {EXPECTED_COMPANIES} distinct companies, "
            f"found {actual_companies}."
        )

    actual_periods = df["period_label"].nunique()
    if actual_periods != EXPECTED_PERIODS:
        raise ValueError(
            f"Expected {EXPECTED_PERIODS} distinct periods, "
            f"found {actual_periods}."
        )

    # --- risk_keyword_count must be 0 in synthetic MVP ---
    bad_risk = df[df["risk_keyword_count"] != 0]
    if not bad_risk.empty:
        raise ValueError(
            f"{len(bad_risk)} rows have risk_keyword_count != 0. "
            "Unexpected in synthetic MVP — check fact_risk_keyword."
        )

    # --- FY2024 revenue_growth_pct must be NULL (no prior period) ---
    fy2024_rows = df[df["period_label"] == "FY2024"]
    if fy2024_rows.empty:
        raise ValueError("No FY2024 rows found in mart.")
    non_null_growth = fy2024_rows["revenue_growth_pct"].notna().sum()
    if non_null_growth > 0:
        raise ValueError(
            f"{non_null_growth} FY2024 rows have a non-NULL revenue_growth_pct. "
            "First-period growth must be NULL — check the LAG() window in the mart SQL."
        )

    # --- FY2025 revenue_growth_pct must be populated ---
    fy2025_rows = df[df["period_label"] == "FY2025"]
    if fy2025_rows.empty:
        raise ValueError("No FY2025 rows found in mart.")
    null_growth = fy2025_rows["revenue_growth_pct"].isna().sum()
    if null_growth > 0:
        raise ValueError(
            f"{null_growth} FY2025 rows have NULL revenue_growth_pct. "
            "Growth should be calculated for every company in the second period."
        )

    # --- no nulls in metric columns (raw values must always be present) ---
    raw_metric_cols = [
        "revenue", "gross_profit", "operating_profit", "net_income",
        "total_assets", "total_debt", "cash", "operating_cash_flow",
    ]
    null_counts = df[raw_metric_cols].isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    if not cols_with_nulls.empty:
        raise ValueError(
            f"NULL values found in raw metric columns: {cols_with_nulls.to_dict()}"
        )


# =============================================================================
# Step 4 — Export to CSV
# =============================================================================

def export_mart_csv(df: pd.DataFrame) -> None:
    """
    Save the validated mart DataFrame to MART_CSV.

    Creates the target directory if it does not exist.
    Does not write the DataFrame index.
    Column order matches MART_REQUIRED_COLUMNS exactly.
    """
    MART_CSV.parent.mkdir(parents=True, exist_ok=True)
    df[MART_REQUIRED_COLUMNS].to_csv(MART_CSV, index=False)


# =============================================================================
# Step 5 — Print summary
# =============================================================================

def print_mart_summary(df: pd.DataFrame) -> None:
    """Print a human-readable summary of the exported mart."""
    print()
    print("--- Export summary ---")
    print(f"Output path   : {MART_CSV}")
    print(f"Rows          : {len(df)}")
    print(f"Columns       : {len(df.columns)}")
    print()

    print("--- Column list ---")
    for col in MART_REQUIRED_COLUMNS:
        print(f"  {col}")

    print()
    print("--- Dashboard preview (key KPI columns) ---")
    preview = df[PREVIEW_COLUMNS].copy()

    # Format revenue as integer with thousands separator
    preview["revenue"] = preview["revenue"].map("{:,.0f}".format)

    # Format percentage columns
    for col in ["revenue_growth_pct", "gross_margin_pct", "net_margin_pct",
                "debt_to_assets_pct", "cash_to_debt_pct"]:
        preview[col] = preview[col].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "—"
        )

    print(preview.to_string(index=False))


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    """
    Full export sequence:
      1. Create / refresh the mart view in SQLite.
      2. Read the view into a DataFrame.
      3. Validate shape and business rules.
      4. Export to CSV.
      5. Print summary.
    """
    print("=" * 60)
    print("Mart Export")
    print("=" * 60)
    print(f"Database  : {DB_PATH}")
    print(f"Mart SQL  : {MART_SQL_PATH}")
    print(f"Output    : {MART_CSV}")
    print()

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}\n"
            "Run src/database_loader.py first."
        )

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        print("Creating mart view...", end=" ")
        create_or_refresh_mart_view(conn)
        print("done")

        print("Loading mart data...", end=" ")
        df = load_mart_dataframe(conn)
        print(f"{len(df)} rows, {len(df.columns)} columns")

        print("Validating mart...", end=" ")
        validate_mart_dataframe(df)
        print("passed")

        print("Exporting CSV...", end=" ")
        export_mart_csv(df)
        print("done")

        print_mart_summary(df)

        print()
        print("Mart export complete.")
        print("=" * 60)

    except Exception:
        print("\nERROR: mart export failed.")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
