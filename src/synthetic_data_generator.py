"""
synthetic_data_generator.py

Generates synthetic financial metrics for 3 fictional companies across 2 periods.

IMPORTANT: All values in this file are synthetic and do not represent real companies
or real financial data. They exist solely to prove the pipeline before real documents
are connected.

Output: data/synthetic/synthetic_financial_metrics.csv
"""

import sys
from pathlib import Path

import pandas as pd

# When run as a script, Python adds the script's own directory (src/) to sys.path,
# so 'config' is importable directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    COMPANIES,
    CURRENCY,
    PERIODS,
    REQUIRED_SYNTHETIC_COLUMNS,
    SYNTHETIC_METRICS_CSV,
)

# ---------------------------------------------------------------------------
# Synthetic financial snapshots
#
# Each key is (company_id, period_id).
# Values map metric_name → metric_value (TRY, actual units).
#
# Coherence rules enforced by design:
#   gross_profit       < revenue
#   operating_profit   < gross_profit
#   net_income         < operating_profit
#   total_debt         < total_assets
#   cash               < total_assets
#   operating_cash_flow is a plausible multiple of net_income
#
# Revenue growth between FY2024 and FY2025 is intentionally different per company
# so the KPI layer can calculate meaningful growth rates.
# ---------------------------------------------------------------------------

_FINANCIALS: dict[tuple[int, int], dict[str, float]] = {

    # ------------------------------------------------------------------
    # Aurora Manufacturing — Industrials
    # FY2024 base | FY2025 +18% revenue growth
    # Gross margin ~30% | Operating margin ~14% | Net margin ~8%
    # ------------------------------------------------------------------
    (1, 1): {
        "revenue":              2_800_000_000,
        "gross_profit":           840_000_000,   # 30.0% gross margin
        "operating_profit":       392_000_000,   # 14.0% operating margin
        "net_income":             224_000_000,   #  8.0% net margin
        "total_assets":         5_600_000_000,
        "total_debt":           1_400_000_000,   # 25.0% debt/assets
        "cash":                   336_000_000,   # cash/debt = 24.0%
        "operating_cash_flow":    308_000_000,   # 1.37x net income
    },
    (1, 2): {
        "revenue":              3_304_000_000,   # +18.0% vs FY2024
        "gross_profit":           991_200_000,   # 30.0% gross margin
        "operating_profit":       462_560_000,   # 14.0% operating margin
        "net_income":             264_320_000,   #  8.0% net margin
        "total_assets":         6_440_000_000,
        "total_debt":           1_610_000_000,
        "cash":                   450_000_000,
        "operating_cash_flow":    363_440_000,
    },

    # ------------------------------------------------------------------
    # Nova Retail Group — Consumer Discretionary
    # FY2024 base | FY2025 +12% revenue growth
    # Gross margin ~24% | Operating margin ~8% | Net margin ~4%
    # Higher leverage typical for large-format retail
    # ------------------------------------------------------------------
    (2, 1): {
        "revenue":              4_200_000_000,
        "gross_profit":         1_008_000_000,   # 24.0% gross margin
        "operating_profit":       336_000_000,   #  8.0% operating margin
        "net_income":             168_000_000,   #  4.0% net margin
        "total_assets":         7_350_000_000,
        "total_debt":           2_940_000_000,   # 40.0% debt/assets
        "cash":                   588_000_000,   # cash/debt = 20.0%
        "operating_cash_flow":    252_000_000,   # 1.50x net income
    },
    (2, 2): {
        "revenue":              4_704_000_000,   # +12.0% vs FY2024
        "gross_profit":         1_128_960_000,   # 24.0% gross margin
        "operating_profit":       376_320_000,   #  8.0% operating margin
        "net_income":             188_160_000,   #  4.0% net margin
        "total_assets":         8_232_000_000,
        "total_debt":           3_292_800_000,
        "cash":                   705_600_000,
        "operating_cash_flow":    282_240_000,
    },

    # ------------------------------------------------------------------
    # Atlas Energy Systems — Energy
    # FY2024 base | FY2025 +8% revenue growth
    # Gross margin ~35% | Operating margin ~20% | Net margin ~13%
    # Capital-intensive balance sheet; assets ~2.8x revenue
    # ------------------------------------------------------------------
    (3, 1): {
        "revenue":              6_500_000_000,
        "gross_profit":         2_275_000_000,   # 35.0% gross margin
        "operating_profit":     1_300_000_000,   # 20.0% operating margin
        "net_income":             845_000_000,   # 13.0% net margin
        "total_assets":        18_200_000_000,
        "total_debt":           7_280_000_000,   # 40.0% debt/assets
        "cash":                 1_820_000_000,   # cash/debt = 25.0%
        "operating_cash_flow":  1_105_000_000,   # 1.31x net income
    },
    (3, 2): {
        "revenue":              7_020_000_000,   # +8.0% vs FY2024
        "gross_profit":         2_457_000_000,   # 35.0% gross margin
        "operating_profit":     1_404_000_000,   # 20.0% operating margin
        "net_income":             912_600_000,   # 13.0% net margin
        "total_assets":        19_656_000_000,
        "total_debt":           7_862_400_000,
        "cash":                 2_162_520_000,
        "operating_cash_flow":  1_186_260_000,
    },
}


def generate_synthetic_financial_data() -> pd.DataFrame:
    """
    Build the synthetic metrics DataFrame.

    Returns one row per company + period + metric (48 rows total).
    All metadata columns are populated according to the data contract in
    docs/05_DATA_CONTRACTS.md.
    """
    rows: list[dict] = []

    for company in COMPANIES:
        for period in PERIODS:
            key = (company["company_id"], period["period_id"])
            metric_values = _FINANCIALS[key]

            for metric_name, metric_value in metric_values.items():
                rows.append({
                    "company_id":        company["company_id"],
                    "company_name":      company["company_name"],
                    "period_id":         period["period_id"],
                    "period_label":      period["period_label"],
                    "metric_name":       metric_name,
                    "metric_value":      float(metric_value),
                    "currency":          CURRENCY,
                    "source_document":   f"synthetic_financial_statement_{period['period_label']}_{company['company_name'].lower().replace(' ', '_')}",
                    "extraction_method": "synthetic",
                    "confidence_score":  1.00,
                    "is_synthetic":      True,
                })

    return pd.DataFrame(rows, columns=REQUIRED_SYNTHETIC_COLUMNS)


def validate_synthetic_data(df: pd.DataFrame) -> None:
    """
    Validate the synthetic DataFrame against the data contract.

    Raises ValueError with a descriptive message on the first failure found.
    Does not silently pass over broken data.
    """
    expected_rows = len(COMPANIES) * len(PERIODS) * len(_FINANCIALS[(1, 1)])

    # --- column contract ---
    missing_cols = [c for c in REQUIRED_SYNTHETIC_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    extra_cols = [c for c in df.columns if c not in REQUIRED_SYNTHETIC_COLUMNS]
    if extra_cols:
        raise ValueError(f"Unexpected extra columns: {extra_cols}")

    # --- row count ---
    if len(df) != expected_rows:
        raise ValueError(
            f"Row count mismatch: expected {expected_rows}, got {len(df)}"
        )

    # --- no nulls in any required column ---
    null_counts = df[REQUIRED_SYNTHETIC_COLUMNS].isnull().sum()
    columns_with_nulls = null_counts[null_counts > 0]
    if not columns_with_nulls.empty:
        raise ValueError(
            f"Null values found in columns: {columns_with_nulls.to_dict()}"
        )

    # --- every company-period must have exactly 8 metrics ---
    metric_counts = (
        df.groupby(["company_id", "period_id"])["metric_name"]
        .count()
        .reset_index(name="count")
    )
    bad = metric_counts[metric_counts["count"] != 8]
    if not bad.empty:
        raise ValueError(
            f"Some company-period combinations do not have exactly 8 metrics:\n{bad}"
        )

    # --- confidence_score must be 1.00 for all rows ---
    bad_confidence = df[df["confidence_score"] != 1.00]
    if not bad_confidence.empty:
        raise ValueError(
            f"{len(bad_confidence)} rows have confidence_score != 1.00"
        )

    # --- is_synthetic must be True for all rows ---
    bad_synthetic = df[df["is_synthetic"] != True]  # noqa: E712
    if not bad_synthetic.empty:
        raise ValueError(
            f"{len(bad_synthetic)} rows have is_synthetic != True"
        )

    # --- financial coherence spot-checks ---
    pivot = df.pivot_table(
        index=["company_id", "period_id"],
        columns="metric_name",
        values="metric_value",
    )

    for (cid, pid), row in pivot.iterrows():
        label = f"company_id={cid}, period_id={pid}"

        if row["gross_profit"] >= row["revenue"]:
            raise ValueError(f"{label}: gross_profit must be less than revenue")

        if row["operating_profit"] >= row["gross_profit"]:
            raise ValueError(f"{label}: operating_profit must be less than gross_profit")

        if row["net_income"] >= row["operating_profit"]:
            raise ValueError(f"{label}: net_income must be less than operating_profit")

        if row["cash"] >= row["total_assets"]:
            raise ValueError(f"{label}: cash must be less than total_assets")

        if row["total_debt"] >= row["total_assets"]:
            raise ValueError(f"{label}: total_debt must be less than total_assets")


def save_synthetic_data(df: pd.DataFrame) -> None:
    """
    Save the validated DataFrame to SYNTHETIC_METRICS_CSV.

    Creates the target directory if it does not exist.
    Does not write the DataFrame index.
    """
    SYNTHETIC_METRICS_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SYNTHETIC_METRICS_CSV, index=False)


def main() -> None:
    """Generate, validate, save, and summarise the synthetic financial metrics."""
    print("=" * 60)
    print("Synthetic Data Generator")
    print("=" * 60)

    print("Generating data...", end=" ")
    df = generate_synthetic_financial_data()
    print("done")

    print("Validating data...", end=" ")
    validate_synthetic_data(df)
    print("passed")

    print("Saving CSV...", end=" ")
    save_synthetic_data(df)
    print("done")

    print()
    print("--- Output summary ---")
    print(f"Path       : {SYNTHETIC_METRICS_CSV}")
    print(f"Companies  : {df['company_name'].nunique()} ({', '.join(df['company_name'].unique())})")
    print(f"Periods    : {df['period_label'].nunique()} ({', '.join(df['period_label'].unique())})")
    print(f"Metrics    : {df['metric_name'].nunique()} ({', '.join(sorted(df['metric_name'].unique()))})")
    print(f"Total rows : {len(df)}")
    print()
    print("--- Columns ---")
    for col in df.columns:
        print(f"  {col}")
    print()
    print("--- Revenue by company and period ---")
    revenue_df = (
        df[df["metric_name"] == "revenue"]
        .pivot_table(index="company_name", columns="period_label", values="metric_value")
        .map(lambda x: f"{x:,.0f}")
    )
    print(revenue_df.to_string())
    print()
    print(f"All validation checks passed. File is ready at:\n{SYNTHETIC_METRICS_CSV}")
    print("=" * 60)


if __name__ == "__main__":
    main()
