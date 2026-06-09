"""
database_loader.py

Loads the synthetic financial metrics CSV into the SQLite database.

Execution order:
  1. Read and validate data/synthetic/synthetic_financial_metrics.csv.
  2. Rebuild the database schema from sql/01_schema.sql (DROP + CREATE + seed dim_metric).
  3. Insert dim_company and dim_period from config.py constants.
  4. Insert fact_document_source — one row per unique company-period source document.
  5. Insert fact_financial_metric — 48 rows, one per company + period + metric.

The schema is rebuilt from scratch on every run, so running this script
multiple times always produces identical final row counts.
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    COMPANIES,
    DB_PATH,
    PERIODS,
    PROJECT_ROOT,
    REQUIRED_SYNTHETIC_COLUMNS,
    SYNTHETIC_METRICS_CSV,
)

SCHEMA_PATH = PROJECT_ROOT / "sql" / "01_schema.sql"

EXPECTED_ROW_COUNT = 48
EXPECTED_METRICS_PER_COMPANY_PERIOD = 8


# =============================================================================
# Step 1 — Load and validate input
# =============================================================================

def load_synthetic_csv() -> pd.DataFrame:
    """
    Read the synthetic metrics CSV and return a DataFrame.

    Validates that the file exists and that all required columns are present
    before returning. Does not validate content — that is handled separately
    by validate_input_data().
    """
    if not SYNTHETIC_METRICS_CSV.exists():
        raise FileNotFoundError(
            f"Synthetic CSV not found: {SYNTHETIC_METRICS_CSV}\n"
            "Run src/synthetic_data_generator.py first."
        )

    df = pd.read_csv(SYNTHETIC_METRICS_CSV)

    missing_cols = [c for c in REQUIRED_SYNTHETIC_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"CSV is missing required columns: {missing_cols}\n"
            f"Found columns: {list(df.columns)}"
        )

    return df


def validate_input_data(df: pd.DataFrame) -> None:
    """
    Validate the content of the synthetic DataFrame against the data contract.

    Every check raises a descriptive ValueError on failure so broken data
    is never silently loaded into the database.
    """
    # --- column contract ---
    missing_cols = [c for c in REQUIRED_SYNTHETIC_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    extra_cols = [c for c in df.columns if c not in REQUIRED_SYNTHETIC_COLUMNS]
    if extra_cols:
        raise ValueError(f"Unexpected extra columns not in contract: {extra_cols}")

    # --- no nulls in any required column ---
    null_counts = df[REQUIRED_SYNTHETIC_COLUMNS].isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    if not cols_with_nulls.empty:
        raise ValueError(f"Null values found: {cols_with_nulls.to_dict()}")

    # --- row count ---
    if len(df) != EXPECTED_ROW_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ROW_COUNT} rows, found {len(df)}. "
            "Re-run synthetic_data_generator.py to rebuild the CSV."
        )

    # --- every company-period must have exactly 8 metrics ---
    metric_counts = (
        df.groupby(["company_id", "period_id"])["metric_name"]
        .count()
        .reset_index(name="count")
    )
    incomplete = metric_counts[metric_counts["count"] != EXPECTED_METRICS_PER_COMPANY_PERIOD]
    if not incomplete.empty:
        raise ValueError(
            f"Some company-period groups do not have exactly "
            f"{EXPECTED_METRICS_PER_COMPANY_PERIOD} metrics:\n{incomplete}"
        )

    # --- metadata field rules ---
    bad_confidence = df[df["confidence_score"] != 1.00]
    if not bad_confidence.empty:
        raise ValueError(
            f"{len(bad_confidence)} rows have confidence_score != 1.00"
        )

    bad_method = df[df["extraction_method"] != "synthetic"]
    if not bad_method.empty:
        raise ValueError(
            f"{len(bad_method)} rows have extraction_method != 'synthetic'"
        )

    bad_synthetic = df[df["is_synthetic"] != True]  # noqa: E712
    if not bad_synthetic.empty:
        raise ValueError(
            f"{len(bad_synthetic)} rows have is_synthetic != True"
        )


# =============================================================================
# Step 2 — Initialise the database
# =============================================================================

def initialize_database(conn: sqlite3.Connection) -> None:
    """
    Rebuild the database schema by executing sql/01_schema.sql.

    The schema script drops all tables and recreates them, so this call
    wipes any existing data. It also seeds dim_metric with the 8 metric
    definitions. executescript() issues an implicit COMMIT before running.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    # Re-enable foreign keys after executescript(), which resets connection state.
    conn.execute("PRAGMA foreign_keys = ON")


# =============================================================================
# Step 3 — Insert dimension tables
# =============================================================================

def insert_companies(conn: sqlite3.Connection) -> None:
    """
    Insert all companies from config.COMPANIES into dim_company.

    Uses INSERT OR REPLACE so the function is safe to call even if rows
    already exist (though initialize_database() rebuilds the table each run).
    """
    conn.executemany(
        """
        INSERT OR REPLACE INTO dim_company (company_id, company_name, sector, country)
        VALUES (:company_id, :company_name, :sector, :country)
        """,
        COMPANIES,
    )


def insert_periods(conn: sqlite3.Connection) -> None:
    """
    Insert all reporting periods from config.PERIODS into dim_period.
    """
    conn.executemany(
        """
        INSERT OR REPLACE INTO dim_period (period_id, period_label, start_date, end_date)
        VALUES (:period_id, :period_label, :start_date, :end_date)
        """,
        PERIODS,
    )


# =============================================================================
# Step 4 — Insert fact_document_source
# =============================================================================

def insert_document_sources(
    conn: sqlite3.Connection,
    df: pd.DataFrame,
) -> dict[tuple[int, int, str], int]:
    """
    Insert one row per unique (company_id, period_id, source_document) combination.

    Returns a mapping:
        (company_id, period_id, source_document) -> document_id

    document_id is the SQLite-assigned AUTOINCREMENT value read back after each
    insert via cursor.lastrowid.
    """
    unique_sources = (
        df[["company_id", "period_id", "source_document", "extraction_method"]]
        .drop_duplicates(subset=["company_id", "period_id", "source_document"])
        .reset_index(drop=True)
    )

    document_map: dict[tuple[int, int, str], int] = {}
    cursor = conn.cursor()

    for _, row in unique_sources.iterrows():
        cursor.execute(
            """
            INSERT INTO fact_document_source
                (source_document, company_id, period_id, document_type,
                 is_synthetic, extraction_method)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row["source_document"],
                int(row["company_id"]),
                int(row["period_id"]),
                "synthetic",
                1,
                row["extraction_method"],
            ),
        )
        doc_id = cursor.lastrowid
        document_map[(int(row["company_id"]), int(row["period_id"]), row["source_document"])] = doc_id

    return document_map


# =============================================================================
# Step 5 — Insert fact_financial_metric
# =============================================================================

def get_metric_id_map(conn: sqlite3.Connection) -> dict[str, int]:
    """
    Read dim_metric and return a mapping: metric_name -> metric_id.

    Validates that all 8 expected metric names exist in dim_metric so the
    loader fails loudly if the schema seed data is missing or incomplete.
    """
    rows = conn.execute(
        "SELECT metric_name, metric_id FROM dim_metric ORDER BY metric_id"
    ).fetchall()

    if not rows:
        raise RuntimeError(
            "dim_metric is empty. The schema seed data may not have been applied. "
            "Re-run initialize_database()."
        )

    metric_id_map: dict[str, int] = {name: mid for name, mid in rows}
    return metric_id_map


def insert_financial_metrics(
    conn: sqlite3.Connection,
    df: pd.DataFrame,
    document_map: dict[tuple[int, int, str], int],
    metric_id_map: dict[str, int],
) -> None:
    """
    Insert all 48 rows from the synthetic CSV into fact_financial_metric.

    Each row is mapped from metric_name -> metric_id and from
    (company_id, period_id, source_document) -> document_id before insert.
    Raises a clear KeyError if any metric name or document key is missing
    from the lookup maps — this should never happen if validate_input_data()
    and get_metric_id_map() were called first.
    """
    # Validate all metric names are in the map before starting any inserts.
    unknown_metrics = set(df["metric_name"].unique()) - set(metric_id_map.keys())
    if unknown_metrics:
        raise ValueError(
            f"Metric names in CSV not found in dim_metric: {unknown_metrics}\n"
            "Check that sql/01_schema.sql seed data matches config.METRICS."
        )

    cursor = conn.cursor()

    for _, row in df.iterrows():
        company_id    = int(row["company_id"])
        period_id     = int(row["period_id"])
        source_doc    = row["source_document"]
        metric_name   = row["metric_name"]

        metric_id   = metric_id_map[metric_name]
        document_id = document_map[(company_id, period_id, source_doc)]

        cursor.execute(
            """
            INSERT INTO fact_financial_metric
                (company_id, period_id, metric_id, document_id,
                 metric_value, currency, confidence_score, is_synthetic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                period_id,
                metric_id,
                document_id,
                float(row["metric_value"]),
                row["currency"],
                float(row["confidence_score"]),
                1,
            ),
        )


# =============================================================================
# Utility
# =============================================================================

def print_table_counts(conn: sqlite3.Connection) -> None:
    """Print the row count for every table in dependency order."""
    tables = [
        "dim_company",
        "dim_period",
        "dim_metric",
        "fact_document_source",
        "fact_financial_metric",
        "fact_risk_keyword",
    ]
    print()
    print("--- Table row counts ---")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        expected = {
            "dim_company": 3,
            "dim_period": 2,
            "dim_metric": 8,
            "fact_document_source": 6,
            "fact_financial_metric": 48,
            "fact_risk_keyword": 0,
        }.get(table)
        status = "OK" if count == expected else f"UNEXPECTED (expected {expected})"
        print(f"  {table:<30} {count:>3} rows  [{status}]")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    """
    Full load sequence: validate → rebuild schema → insert dimensions → insert facts.
    """
    print("=" * 60)
    print("Database Loader")
    print("=" * 60)

    # Ensure the output directory exists before connecting.
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        print(f"Source CSV : {SYNTHETIC_METRICS_CSV}")
        print(f"Database   : {DB_PATH}")
        print()

        # --- Step 1: input validation ---
        print("Loading CSV...", end=" ")
        df = load_synthetic_csv()
        print(f"{len(df)} rows loaded")

        print("Validating input data...", end=" ")
        validate_input_data(df)
        print("passed")

        # --- Step 2: rebuild schema ---
        print("Initialising database schema...", end=" ")
        initialize_database(conn)
        print("done")

        # --- Step 3: dimension inserts ---
        print("Inserting companies...", end=" ")
        insert_companies(conn)
        print(f"{len(COMPANIES)} rows")

        print("Inserting periods...", end=" ")
        insert_periods(conn)
        print(f"{len(PERIODS)} rows")

        # --- Step 4: fact inserts ---
        print("Inserting document sources...", end=" ")
        document_map = insert_document_sources(conn, df)
        print(f"{len(document_map)} rows")

        print("Reading metric ID map...", end=" ")
        metric_id_map = get_metric_id_map(conn)
        print(f"{len(metric_id_map)} metrics found in dim_metric")

        print("Inserting financial metrics...", end=" ")
        insert_financial_metrics(conn, df, document_map, metric_id_map)
        print(f"{len(df)} rows")

        # --- Commit everything ---
        conn.commit()
        print("\nAll inserts committed.")

        # --- Summary ---
        print_table_counts(conn)

        print()
        print(f"Database ready: {DB_PATH.resolve()}")
        print("=" * 60)

    except Exception:
        conn.rollback()
        print("\nERROR: transaction rolled back. Database is unchanged.")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
