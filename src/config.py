"""
Central configuration for the Financial Intelligence Pipeline.

All paths, constants, and business definitions live here.
No other module should hardcode paths, company names, or metric names.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DOCUMENTS_DIR = DATA_DIR / "raw_documents"
PROCESSED_MARKDOWN_DIR = DATA_DIR / "processed_markdown"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
EXTRACTED_DIR = DATA_DIR / "extracted"
FINAL_DIR = DATA_DIR / "final"

REPORTS_DIR = PROJECT_ROOT / "reports"

DB_PATH = FINAL_DIR / "financial_intelligence.sqlite"
SYNTHETIC_METRICS_CSV = SYNTHETIC_DIR / "synthetic_financial_metrics.csv"
MART_CSV = FINAL_DIR / "mart_company_financial_performance.csv"

# ---------------------------------------------------------------------------
# Business definitions
# ---------------------------------------------------------------------------

COMPANIES: list[dict] = [
    {
        "company_id": 1,
        "company_name": "Aurora Manufacturing",
        "sector": "Industrials",
        "country": "Turkey",
    },
    {
        "company_id": 2,
        "company_name": "Nova Retail Group",
        "sector": "Consumer Discretionary",
        "country": "Turkey",
    },
    {
        "company_id": 3,
        "company_name": "Atlas Energy Systems",
        "sector": "Energy",
        "country": "Turkey",
    },
]

PERIODS: list[dict] = [
    {
        "period_id": 1,
        "period_label": "FY2024",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
    },
    {
        "period_id": 2,
        "period_label": "FY2025",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
    },
]

METRICS: list[str] = [
    "revenue",
    "gross_profit",
    "operating_profit",
    "net_income",
    "total_assets",
    "total_debt",
    "cash",
    "operating_cash_flow",
]

CURRENCY: str = "TRY"

# ---------------------------------------------------------------------------
# Data contract — required columns for the synthetic metrics CSV.
# The loader validates this list before touching the database.
# ---------------------------------------------------------------------------

REQUIRED_SYNTHETIC_COLUMNS: list[str] = [
    "company_id",
    "company_name",
    "period_id",
    "period_label",
    "metric_name",
    "metric_value",
    "currency",
    "source_document",
    "extraction_method",
    "confidence_score",
    "is_synthetic",
]

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_config_summary() -> None:
    """Print a human-readable summary of the current configuration."""
    print("=" * 60)
    print("Financial Intelligence Pipeline — Configuration")
    print("=" * 60)
    print(f"Project root   : {PROJECT_ROOT}")
    print(f"Database path  : {DB_PATH}")
    print(f"Synthetic CSV  : {SYNTHETIC_METRICS_CSV}")
    print(f"Mart CSV       : {MART_CSV}")
    print()
    print("Companies:")
    for c in COMPANIES:
        print(f"  [{c['company_id']}] {c['company_name']} — {c['sector']} ({c['country']})")
    print()
    print("Periods:")
    for p in PERIODS:
        print(f"  [{p['period_id']}] {p['period_label']}  {p['start_date']} → {p['end_date']}")
    print()
    print("Metrics:")
    for m in METRICS:
        print(f"  - {m}")
    print()
    print(f"Currency       : {CURRENCY}")
    print(f"Expected rows  : {len(COMPANIES)} companies × {len(PERIODS)} periods × {len(METRICS)} metrics = {len(COMPANIES) * len(PERIODS) * len(METRICS)} rows")
    print("=" * 60)


if __name__ == "__main__":
    print_config_summary()
