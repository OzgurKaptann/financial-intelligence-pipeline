#!/usr/bin/env python3
"""
load_postgres_analytics.py

Phase 2 PostgreSQL data loader.

Reads database connection values from metabase/.env, connects to the analytics
PostgreSQL database, creates all Phase 2 tables, loads synthetic financial
data from the source CSV, and populates the analytics star schema.

Idempotent: safe to rerun. Tables are dropped and recreated by the SQL script
on each run, so rerunning produces identical results.

Usage:
    python src/load_postgres_analytics.py

Prerequisites:
    - Docker stack must be running (financial_analytics_db container)
    - metabase/.env must exist with valid POSTGRES_ANALYTICS_* values
    - pip install psycopg2-binary python-dotenv pandas
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
import psycopg2.extensions
import psycopg2.extras
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths — all relative to project root so the script works from any cwd
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / "metabase" / ".env"
SQL_CREATE = PROJECT_ROOT / "metabase" / "postgres" / "sql" / "02_create_analytics_tables.sql"
CSV_SOURCE = PROJECT_ROOT / "data" / "synthetic" / "synthetic_financial_metrics.csv"

# Expected row counts used for end-of-run validation
EXPECTED_COUNTS: dict[str, int] = {
    "raw.synthetic_financial_metrics":  48,
    "analytics.dim_company":             3,
    "analytics.dim_period":              2,
    "analytics.dim_metric":              8,
    "analytics.fact_document_source":    6,
    "analytics.fact_financial_metric":  48,
    "analytics.fact_risk_keyword":       0,
}


# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------

def load_env() -> None:
    """Load database credentials from metabase/.env into the process environment."""
    if not ENV_FILE.exists():
        print(f"ERROR: environment file not found at {ENV_FILE}", file=sys.stderr)
        print("  Copy metabase/.env.example to metabase/.env and set passwords.",
              file=sys.stderr)
        sys.exit(1)
    load_dotenv(ENV_FILE)
    required = [
        "POSTGRES_ANALYTICS_DB",
        "POSTGRES_ANALYTICS_USER",
        "POSTGRES_ANALYTICS_PASSWORD",
        "POSTGRES_ANALYTICS_PORT",
    ]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"ERROR: missing variables in {ENV_FILE}: {missing}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

def get_connection() -> psycopg2.extensions.connection:
    """Open and return a psycopg2 connection to the analytics PostgreSQL database."""
    return psycopg2.connect(
        dbname=os.environ["POSTGRES_ANALYTICS_DB"],
        user=os.environ["POSTGRES_ANALYTICS_USER"],
        password=os.environ["POSTGRES_ANALYTICS_PASSWORD"],
        host="localhost",
        port=int(os.environ["POSTGRES_ANALYTICS_PORT"]),
    )


# ---------------------------------------------------------------------------
# SQL file execution
# ---------------------------------------------------------------------------

def execute_sql_file(conn: psycopg2.extensions.connection, path: Path) -> None:
    """Read a SQL file and execute it as a single statement block."""
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"  Executed {path.name}")


# ---------------------------------------------------------------------------
# Raw table load
# ---------------------------------------------------------------------------

def load_raw_table(conn: psycopg2.extensions.connection, df: pd.DataFrame) -> None:
    """Insert all rows from the source DataFrame into raw.synthetic_financial_metrics."""
    rows = [
        (
            int(row.company_id),
            str(row.company_name),
            int(row.period_id),
            str(row.period_label),
            str(row.metric_name),
            float(row.metric_value),
            str(row.currency),
            str(row.source_document),
            str(row.extraction_method),
            float(row.confidence_score),
            str(row.is_synthetic).strip().lower() == "true",
        )
        for row in df.itertuples(index=False)
    ]
    sql = """
        INSERT INTO raw.synthetic_financial_metrics (
            company_id, company_name, period_id, period_label, metric_name,
            metric_value, currency, source_document, extraction_method,
            confidence_score, is_synthetic
        ) VALUES %s
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows, page_size=100)
    conn.commit()
    print(f"  Inserted {len(rows)} rows into raw.synthetic_financial_metrics")


# ---------------------------------------------------------------------------
# Analytics dimension and fact table population
# ---------------------------------------------------------------------------

def populate_analytics_tables(conn: psycopg2.extensions.connection) -> None:
    """
    Populate all analytics dimension and fact tables from the raw table.

    Uses INSERT ... ON CONFLICT DO NOTHING so the function is safe to call
    on tables that already contain data (e.g. if only this step is rerun).
    """
    steps: list[tuple[str, str]] = [
        (
            "analytics.dim_company",
            """
            INSERT INTO analytics.dim_company (company_id, company_name)
            SELECT DISTINCT company_id, company_name
            FROM raw.synthetic_financial_metrics
            ORDER BY company_id
            ON CONFLICT (company_id) DO NOTHING
            """,
        ),
        (
            "analytics.dim_period",
            """
            INSERT INTO analytics.dim_period (period_id, period_label)
            SELECT DISTINCT period_id, period_label
            FROM raw.synthetic_financial_metrics
            ORDER BY period_id
            ON CONFLICT (period_id) DO NOTHING
            """,
        ),
        (
            "analytics.dim_metric",
            """
            INSERT INTO analytics.dim_metric (metric_name)
            SELECT DISTINCT metric_name
            FROM raw.synthetic_financial_metrics
            ORDER BY metric_name
            ON CONFLICT (metric_name) DO NOTHING
            """,
        ),
        (
            "analytics.fact_document_source",
            """
            INSERT INTO analytics.fact_document_source
                (company_id, period_id, source_document, extraction_method,
                 currency, confidence_score, is_synthetic)
            SELECT DISTINCT
                company_id,
                period_id,
                source_document,
                extraction_method,
                currency,
                confidence_score,
                is_synthetic
            FROM raw.synthetic_financial_metrics
            ORDER BY company_id, period_id
            ON CONFLICT (company_id, period_id) DO NOTHING
            """,
        ),
        (
            "analytics.fact_financial_metric",
            """
            INSERT INTO analytics.fact_financial_metric
                (company_id, period_id, metric_id, metric_value)
            SELECT
                r.company_id,
                r.period_id,
                m.metric_id,
                r.metric_value
            FROM raw.synthetic_financial_metrics r
            JOIN analytics.dim_metric m ON m.metric_name = r.metric_name
            ON CONFLICT (company_id, period_id, metric_id) DO NOTHING
            """,
        ),
    ]
    with conn.cursor() as cur:
        for table_name, sql in steps:
            cur.execute(sql)
            print(f"  Populated {table_name} — {cur.rowcount} rows inserted")
    conn.commit()


# ---------------------------------------------------------------------------
# Row count validation
# ---------------------------------------------------------------------------

def print_validation(conn: psycopg2.extensions.connection) -> None:
    """Query row counts for all Phase 2 tables and compare against expected values."""
    col_w = 44
    print()
    print("--- Row Count Validation " + "-" * 46)
    print(f"  {'Table':<{col_w}} {'Count':>6}  {'Expected':>8}  Status")
    print("  " + "-" * 66)

    all_pass = True
    with conn.cursor() as cur:
        for table, expected in EXPECTED_COUNTS.items():
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count: int = cur.fetchone()[0]  # type: ignore[index]
            status = "PASS" if count == expected else "FAIL"
            if status == "FAIL":
                all_pass = False
            print(f"  {table:<{col_w}} {count:>6}  {expected:>8}  {status}")

    print("  " + "-" * 66)
    if all_pass:
        print("  All validation checks PASSED.")
    else:
        print("  WARNING: One or more validation checks FAILED.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Phase 2 — PostgreSQL Analytics Data Loader")
    print("=" * 48)

    print("\n[1/5] Loading credentials from metabase/.env ...")
    load_env()
    print(f"  Target: {os.environ['POSTGRES_ANALYTICS_DB']} on "
          f"localhost:{os.environ['POSTGRES_ANALYTICS_PORT']}")

    print("\n[2/5] Connecting to PostgreSQL ...")
    conn = get_connection()
    print("  Connected.")

    print("\n[3/5] Creating Phase 2 analytics tables ...")
    execute_sql_file(conn, SQL_CREATE)

    print("\n[4/5] Loading CSV into raw.synthetic_financial_metrics ...")
    if not CSV_SOURCE.exists():
        print(f"ERROR: source CSV not found at {CSV_SOURCE}", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(CSV_SOURCE)
    print(f"  Read {len(df)} rows from {CSV_SOURCE.name}")
    load_raw_table(conn, df)

    print("\n[5/5] Populating analytics dimension and fact tables ...")
    populate_analytics_tables(conn)

    print_validation(conn)
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
