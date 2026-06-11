#!/usr/bin/env python3
"""
materialize_document_reconciliation.py

Phase 4: Materialize the document-derived metrics reconciliation layer into PostgreSQL.

Reads connection settings from metabase/.env, connects to the analytics
PostgreSQL database, executes 10_create_document_reconciliation.sql to create:

    transforms.document_metric_reconciliation
    transforms.document_kpi_reconciliation_summary

Then runs validation checks and prints clear PASS/FAIL output for each.

Expected validation output (current sample — Demo Manufacturing FY2025):
  document_metric_reconciliation row count = 1    PASS
  document_kpi_reconciliation_summary row count = 1  PASS
  matched_records = 0                             PASS
  unmatched_records = 1                           PASS
  match_rate_pct = 0.00                           PASS
  Demo Manufacturing match_status = unmatched_company_or_period  PASS

Idempotent: safe to rerun. The SQL drops and recreates Phase 4 tables only.
Phase 2.1 and Phase 3.3 tables are not touched.

Usage:
    python src/materialize_document_reconciliation.py

Prerequisites:
    - Docker stack must be running:
        docker compose -f metabase/docker-compose.yml up -d
    - Phase 3.3 document KPI mart must be materialized:
        python src/materialize_document_kpi_mart.py
    - Phase 2.1 synthetic mart must be materialized:
        python src/materialize_postgres_mart.py
    - metabase/.env must exist with valid POSTGRES_ANALYTICS_* values
    - pip install psycopg2-binary python-dotenv
"""
from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extensions
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT   = Path(__file__).resolve().parent.parent
ENV_FILE       = PROJECT_ROOT / "metabase" / ".env"
SQL_RECONCILE  = (
    PROJECT_ROOT / "metabase" / "postgres" / "sql"
    / "10_create_document_reconciliation.sql"
)

# ---------------------------------------------------------------------------
# Table names
# ---------------------------------------------------------------------------
RECONCILE_TABLE = "transforms.document_metric_reconciliation"
SUMMARY_TABLE   = "transforms.document_kpi_reconciliation_summary"

# ---------------------------------------------------------------------------
# Validation expectations for current sample (Demo Manufacturing FY2025)
# ---------------------------------------------------------------------------
EXPECTED_RECONCILE_ROWS = 1
EXPECTED_SUMMARY_ROWS   = 1
EXPECTED_MATCHED        = 0
EXPECTED_UNMATCHED      = 1
EXPECTED_MATCH_RATE     = 0.00

SAMPLE_COMPANY = "Demo Manufacturing"
SAMPLE_PERIOD  = "FY2025"
EXPECTED_STATUS = "unmatched_company_or_period"


# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------

def load_env() -> None:
    """Load database credentials from metabase/.env into the process environment."""
    if not ENV_FILE.exists():
        print(f"ERROR: environment file not found at {ENV_FILE}", file=sys.stderr)
        print(
            "  Copy metabase/.env.example to metabase/.env and fill in passwords.",
            file=sys.stderr,
        )
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
# SQL execution
# ---------------------------------------------------------------------------

def execute_sql_file(conn: psycopg2.extensions.connection, path: Path) -> None:
    """Read a SQL file and execute it as a single statement block."""
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _to_float(value: Any) -> float | None:
    """Convert a database value (Decimal, int, float, or None) to float."""
    if value is None:
        return None
    return float(value)


def _check(label: str, actual: Any, expected: Any) -> bool:
    """Print a single PASS/FAIL validation line and return True if passed."""
    ok = actual == expected
    status = "PASS" if ok else "FAIL"
    print(f"  {label:<52} = {str(actual):<32}  [{status}]  (expected {expected})")
    return ok


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def run_validations(conn: psycopg2.extensions.connection) -> bool:
    """Run all Phase 4 validation checks. Returns True if every check passes."""
    all_passed = True

    with conn.cursor() as cur:

        # -- structural checks -----------------------------------------------

        cur.execute(f"SELECT COUNT(*) FROM {RECONCILE_TABLE};")
        reconcile_rows = cur.fetchone()[0]
        all_passed &= _check(
            f"{RECONCILE_TABLE} row count",
            reconcile_rows,
            EXPECTED_RECONCILE_ROWS,
        )

        cur.execute(f"SELECT COUNT(*) FROM {SUMMARY_TABLE};")
        summary_rows = cur.fetchone()[0]
        all_passed &= _check(
            f"{SUMMARY_TABLE} row count",
            summary_rows,
            EXPECTED_SUMMARY_ROWS,
        )

        # -- summary value checks --------------------------------------------

        cur.execute(
            f"""
            SELECT matched_records, unmatched_records, match_rate_pct
            FROM   {SUMMARY_TABLE};
            """
        )
        row = cur.fetchone()

        if row is None:
            print(f"  ERROR: no row found in {SUMMARY_TABLE}", file=sys.stderr)
            return False

        matched_records   = row[0]
        unmatched_records = row[1]
        match_rate_pct    = round(_to_float(row[2]), 2) if row[2] is not None else None

        all_passed &= _check("matched_records", matched_records, EXPECTED_MATCHED)
        all_passed &= _check("unmatched_records", unmatched_records, EXPECTED_UNMATCHED)
        all_passed &= _check("match_rate_pct", match_rate_pct, EXPECTED_MATCH_RATE)

        # -- per-company match status ----------------------------------------

        cur.execute(
            f"""
            SELECT match_status
            FROM   {RECONCILE_TABLE}
            WHERE  document_company_name = %s
              AND  document_period_label = %s;
            """,
            (SAMPLE_COMPANY, SAMPLE_PERIOD),
        )
        status_row = cur.fetchone()

        if status_row is None:
            print(
                f"  ERROR: no row found for {SAMPLE_COMPANY} {SAMPLE_PERIOD} "
                f"in {RECONCILE_TABLE}",
                file=sys.stderr,
            )
            all_passed = False
        else:
            actual_status = status_row[0]
            all_passed &= _check(
                f"{SAMPLE_COMPANY} match_status",
                actual_status,
                EXPECTED_STATUS,
            )

    return all_passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("Phase 4: Materialize Document Reconciliation Layer")
    print("=" * 60)

    print("\n[1/3] Loading credentials from metabase/.env ...")
    load_env()
    print(f"  database : {os.environ['POSTGRES_ANALYTICS_DB']}")
    print(f"  host     : localhost:{os.environ['POSTGRES_ANALYTICS_PORT']}")

    print("\n[2/3] Connecting to PostgreSQL and executing reconciliation SQL ...")
    try:
        conn = get_connection()
    except Exception as exc:
        print(f"ERROR: could not connect to PostgreSQL: {exc}", file=sys.stderr)
        print(
            "  Is the Docker stack running?  "
            "Try: docker compose -f metabase/docker-compose.yml up -d",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        execute_sql_file(conn, SQL_RECONCILE)
        print(f"  {RECONCILE_TABLE}  created")
        print(f"  {SUMMARY_TABLE}    created")
    except Exception as exc:
        conn.rollback()
        print(f"ERROR: failed to execute {SQL_RECONCILE.name}: {exc}", file=sys.stderr)
        conn.close()
        sys.exit(1)

    print("\n[3/3] Running validation checks ...")
    all_passed = run_validations(conn)

    conn.close()

    print()
    if all_passed:
        print("All validation checks PASSED.")
    else:
        print("ERROR: one or more validation checks FAILED.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
