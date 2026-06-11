#!/usr/bin/env python3
"""
load_extracted_metrics_postgres.py

Phase 3.2 PostgreSQL loader for document-derived extracted metrics.

Reads database connection values from metabase/.env, connects to the analytics
PostgreSQL database, creates all Phase 3.2 tables, loads extracted financial
metrics from data/extracted/extracted_financial_metrics.csv, optionally loads
the extraction manifest, and promotes clean rows to the analytics layer.

Idempotent: safe to rerun. Phase 3.2 tables are dropped and recreated by the
SQL script on each run. Phase 2 tables are not touched.

Usage:
    python src/load_extracted_metrics_postgres.py

Prerequisites:
    - Docker stack must be running (financial_analytics_db container)
    - metabase/.env must exist with valid POSTGRES_ANALYTICS_* values
    - data/extracted/extracted_financial_metrics.csv must exist (run Phase 3.1 first)
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
PROJECT_ROOT   = Path(__file__).resolve().parent.parent
ENV_FILE       = PROJECT_ROOT / "metabase" / ".env"
SQL_CREATE     = PROJECT_ROOT / "metabase" / "postgres" / "sql" / "06_create_extracted_metrics_tables.sql"
CSV_METRICS    = PROJECT_ROOT / "data" / "extracted" / "extracted_financial_metrics.csv"
CSV_MANIFEST   = PROJECT_ROOT / "data" / "extracted" / "extraction_manifest.csv"

# Expected values for end-of-run validation (sample dataset)
EXPECTED: dict[str, int] = {
    "raw.extracted_financial_metrics row count":                     8,
    "analytics.document_extracted_financial_metric row count":       8,
    "distinct companies":                                            1,
    "distinct periods":                                              1,
    "distinct metrics":                                              8,
    "failed extraction rows":                                        0,
    "null metric_value rows":                                        0,
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
# Raw table loaders
# ---------------------------------------------------------------------------

def load_raw_metrics(
    conn: psycopg2.extensions.connection,
    df: pd.DataFrame,
) -> None:
    """Insert all rows from extracted_financial_metrics.csv into raw.extracted_financial_metrics."""
    rows = []
    for row in df.itertuples(index=False):
        metric_value = None
        if pd.notna(row.metric_value):
            try:
                metric_value = float(row.metric_value)
            except (ValueError, TypeError):
                metric_value = None

        extracted_at = None
        if pd.notna(row.extracted_at) and str(row.extracted_at).strip():
            extracted_at = str(row.extracted_at).strip()

        rows.append((
            str(row.source_file),
            str(row.company_name),
            str(row.period_label),
            str(row.metric_name),
            metric_value,
            str(row.extraction_status),
            str(row.error_message) if pd.notna(row.error_message) else None,
            extracted_at,
        ))

    sql = """
        INSERT INTO raw.extracted_financial_metrics (
            source_file, company_name, period_label, metric_name,
            metric_value, extraction_status, error_message, extracted_at
        ) VALUES %s
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows, page_size=100)
    conn.commit()
    print(f"  Inserted {len(rows)} rows into raw.extracted_financial_metrics")


def load_raw_manifest(
    conn: psycopg2.extensions.connection,
    df: pd.DataFrame,
) -> None:
    """Insert all rows from extraction_manifest.csv into raw.extraction_manifest."""
    rows = []
    for row in df.itertuples(index=False):
        # Map manifest CSV columns to table columns
        # CSV: total_rows_written  → table: metrics_extracted
        # CSV: metrics_missing     → table: missing_metrics
        metrics_extracted = None
        if hasattr(row, "total_rows_written") and pd.notna(row.total_rows_written):
            try:
                metrics_extracted = int(row.total_rows_written)
            except (ValueError, TypeError):
                metrics_extracted = None

        missing_metrics = None
        if hasattr(row, "metrics_missing") and pd.notna(row.metrics_missing):
            missing_metrics = str(row.metrics_missing).strip() or None

        extracted_at = None
        if pd.notna(row.extracted_at) and str(row.extracted_at).strip():
            extracted_at = str(row.extracted_at).strip()

        rows.append((
            str(row.source_file),
            str(row.company_name) if pd.notna(row.company_name) else None,
            str(row.period_label) if pd.notna(row.period_label) else None,
            metrics_extracted,
            missing_metrics,
            str(row.extraction_status),
            str(row.error_message) if pd.notna(row.error_message) else None,
            extracted_at,
        ))

    sql = """
        INSERT INTO raw.extraction_manifest (
            source_file, company_name, period_label, metrics_extracted,
            missing_metrics, extraction_status, error_message, extracted_at
        ) VALUES %s
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows, page_size=100)
    conn.commit()
    print(f"  Inserted {len(rows)} rows into raw.extraction_manifest")


# ---------------------------------------------------------------------------
# Analytics layer population
# ---------------------------------------------------------------------------

def populate_analytics_table(conn: psycopg2.extensions.connection) -> None:
    """
    Populate analytics.document_extracted_financial_metric from raw table.

    Promotes only rows where extraction_status = 'success' and metric_value
    is not NULL, preserving source_file for downstream lineage tracing.
    """
    sql = """
        INSERT INTO analytics.document_extracted_financial_metric
            (source_file, company_name, period_label, metric_name, metric_value)
        SELECT
            source_file,
            company_name,
            period_label,
            metric_name,
            metric_value
        FROM raw.extracted_financial_metrics
        WHERE extraction_status = 'success'
          AND metric_value IS NOT NULL
        ORDER BY source_file, company_name, period_label, metric_name
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        inserted = cur.rowcount
    conn.commit()
    print(f"  Inserted {inserted} rows into analytics.document_extracted_financial_metric")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def print_validation(conn: psycopg2.extensions.connection) -> None:
    """Query validation checks and compare against expected values."""
    checks: list[tuple[str, str]] = [
        (
            "raw.extracted_financial_metrics row count",
            "SELECT COUNT(*) FROM raw.extracted_financial_metrics",
        ),
        (
            "analytics.document_extracted_financial_metric row count",
            "SELECT COUNT(*) FROM analytics.document_extracted_financial_metric",
        ),
        (
            "distinct companies",
            "SELECT COUNT(DISTINCT company_name) FROM analytics.document_extracted_financial_metric",
        ),
        (
            "distinct periods",
            "SELECT COUNT(DISTINCT period_label) FROM analytics.document_extracted_financial_metric",
        ),
        (
            "distinct metrics",
            "SELECT COUNT(DISTINCT metric_name) FROM analytics.document_extracted_financial_metric",
        ),
        (
            "failed extraction rows",
            "SELECT COUNT(*) FROM raw.extracted_financial_metrics WHERE extraction_status <> 'success'",
        ),
        (
            "null metric_value rows",
            "SELECT COUNT(*) FROM raw.extracted_financial_metrics WHERE metric_value IS NULL",
        ),
    ]

    col_w = 52
    print()
    print("--- Validation " + "-" * 55)
    print(f"  {'Check':<{col_w}} {'Value':>6}  {'Expected':>8}  Status")
    print("  " + "-" * 74)

    all_pass = True
    with conn.cursor() as cur:
        for label, query in checks:
            cur.execute(query)
            value: int = cur.fetchone()[0]  # type: ignore[index]
            expected = EXPECTED.get(label, "?")
            if expected == "?":
                status = "?"
            else:
                status = "PASS" if value == expected else "FAIL"
                if status == "FAIL":
                    all_pass = False
            print(f"  {label:<{col_w}} {value:>6}  {str(expected):>8}  {status}")

    print("  " + "-" * 74)
    if all_pass:
        print("  All validation checks PASSED.")
    else:
        print("  WARNING: One or more validation checks FAILED.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Phase 3.2 — PostgreSQL Extracted Metrics Loader")
    print("=" * 50)

    print("\n[1/6] Loading credentials from metabase/.env ...")
    load_env()
    print(f"  Target: {os.environ['POSTGRES_ANALYTICS_DB']} on "
          f"localhost:{os.environ['POSTGRES_ANALYTICS_PORT']}")

    print("\n[2/6] Connecting to PostgreSQL ...")
    conn = get_connection()
    print("  Connected.")

    print("\n[3/6] Creating Phase 3.2 tables ...")
    execute_sql_file(conn, SQL_CREATE)

    print("\n[4/6] Loading extracted metrics into raw.extracted_financial_metrics ...")
    if not CSV_METRICS.exists():
        print(f"ERROR: metrics CSV not found at {CSV_METRICS}", file=sys.stderr)
        print("  Run python src/extract_financial_metrics.py first.", file=sys.stderr)
        sys.exit(1)
    df_metrics = pd.read_csv(CSV_METRICS)
    print(f"  Read {len(df_metrics)} rows from {CSV_METRICS.name}")
    load_raw_metrics(conn, df_metrics)

    print("\n[5/6] Loading extraction manifest ...")
    if CSV_MANIFEST.exists():
        df_manifest = pd.read_csv(CSV_MANIFEST)
        print(f"  Read {len(df_manifest)} rows from {CSV_MANIFEST.name}")
        load_raw_manifest(conn, df_manifest)
    else:
        print(f"  {CSV_MANIFEST.name} not found — skipping manifest load.")

    print("\n[6/6] Populating analytics.document_extracted_financial_metric ...")
    populate_analytics_table(conn)

    print_validation(conn)
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
