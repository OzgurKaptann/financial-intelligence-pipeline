#!/usr/bin/env python3
"""
materialize_postgres_mart.py

Phase 2.1: Materialize the final dashboard mart into PostgreSQL.

Reads connection settings from metabase/.env, connects to the analytics
PostgreSQL database, executes 04_create_transform_mart.sql to create
transforms.mart_company_financial_performance, then runs validation checks
against the materialized table.

Idempotent: safe to rerun. The SQL script drops and recreates the table on
every execution.

Usage:
    python src/materialize_postgres_mart.py

Prerequisites:
    - Docker stack must be running:
        docker compose -f metabase/docker-compose.yml up -d
    - Analytics star schema must be loaded:
        python src/load_postgres_analytics.py
    - metabase/.env must exist with valid POSTGRES_ANALYTICS_* values
    - pip install psycopg2-binary python-dotenv
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extensions
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths — relative to project root so the script works from any cwd
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE     = PROJECT_ROOT / "metabase" / ".env"
SQL_MART     = PROJECT_ROOT / "metabase" / "postgres" / "sql" / "04_create_transform_mart.sql"

# ---------------------------------------------------------------------------
# Expected validation values
# ---------------------------------------------------------------------------
EXPECTED_ROW_COUNT = 6

EXPECTED_FY2025_GROWTH: dict[str, float] = {
    "Atlas Energy Systems": 8.00,
    "Aurora Manufacturing": 18.00,
    "Nova Retail Group":    12.00,
}

MART_TABLE = "transforms.mart_company_financial_performance"


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
# SQL execution
# ---------------------------------------------------------------------------

def execute_sql_file(conn: psycopg2.extensions.connection, path: Path) -> None:
    """Read a SQL file and execute it as a single statement block."""
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def run_validations(conn: psycopg2.extensions.connection) -> bool:
    """Run validation checks against the materialized mart. Returns True if all pass."""
    all_passed = True

    with conn.cursor() as cur:

        # Check 1: Row count
        cur.execute(f"SELECT COUNT(*) FROM {MART_TABLE};")
        row_count = cur.fetchone()[0]
        ok = row_count == EXPECTED_ROW_COUNT
        if not ok:
            all_passed = False
        print(f"  row count = {row_count}  "
              f"[{'PASS' if ok else 'FAIL'}]  (expected {EXPECTED_ROW_COUNT})")

        # Check 2: FY2025 revenue growth per company
        for company, expected in EXPECTED_FY2025_GROWTH.items():
            cur.execute(
                f"""
                SELECT revenue_growth_pct
                FROM   {MART_TABLE}
                WHERE  company_name  = %s
                  AND  fiscal_period = 'FY2025';
                """,
                (company,),
            )
            row = cur.fetchone()
            actual = float(row[0]) if row and row[0] is not None else None
            ok = actual == expected
            if not ok:
                all_passed = False
            print(f"  FY2025 revenue_growth_pct  {company:<28} = {actual}  "
                  f"[{'PASS' if ok else 'FAIL'}]  (expected {expected})")

        # Check 3: FY2024 revenue_growth_pct is NULL for all companies
        cur.execute(
            f"""
            SELECT COUNT(*)
            FROM   {MART_TABLE}
            WHERE  fiscal_period        = 'FY2024'
              AND  revenue_growth_pct  IS NOT NULL;
            """
        )
        non_null = cur.fetchone()[0]
        ok = non_null == 0
        if not ok:
            all_passed = False
        print(f"  FY2024 revenue_growth_pct is NULL for all rows  "
              f"[{'PASS' if ok else 'FAIL'}]  (non-null count = {non_null}, expected 0)")

        # Check 4: risk_keyword_count = 0 for all rows
        cur.execute(
            f"""
            SELECT COUNT(*)
            FROM   {MART_TABLE}
            WHERE  risk_keyword_count <> 0;
            """
        )
        non_zero = cur.fetchone()[0]
        ok = non_zero == 0
        if not ok:
            all_passed = False
        print(f"  risk_keyword_count = 0 for all rows  "
              f"[{'PASS' if ok else 'FAIL'}]  (non-zero count = {non_zero}, expected 0)")

    return all_passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("Phase 2.1: Materialize PostgreSQL Transform Mart")
    print("=" * 60)

    print("\n[1/3] Loading credentials from metabase/.env ...")
    load_env()
    print(f"  database : {os.environ['POSTGRES_ANALYTICS_DB']}")
    print(f"  host     : localhost:{os.environ['POSTGRES_ANALYTICS_PORT']}")

    print("\n[2/3] Connecting to PostgreSQL and executing mart SQL ...")
    try:
        conn = get_connection()
    except Exception as exc:
        print(f"ERROR: could not connect to PostgreSQL: {exc}", file=sys.stderr)
        print("  Is the Docker stack running?  "
              "Try: docker compose -f metabase/docker-compose.yml up -d",
              file=sys.stderr)
        sys.exit(1)

    try:
        execute_sql_file(conn, SQL_MART)
        print(f"  {MART_TABLE}  created")
    except Exception as exc:
        conn.rollback()
        print(f"ERROR: failed to execute {SQL_MART.name}: {exc}", file=sys.stderr)
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
