#!/usr/bin/env python3
"""
materialize_document_kpi_mart.py

Phase 3.3: Materialize the document-derived KPI mart into PostgreSQL.

Reads connection settings from metabase/.env, connects to the analytics
PostgreSQL database, executes 08_create_document_kpi_mart.sql to create:

    transforms.document_financial_metric_pivot
    transforms.mart_document_company_financial_performance

Then runs validation checks and prints clear PASS/FAIL output for each.

Idempotent: safe to rerun. The SQL drops and recreates Phase 3.3 tables only.
Phase 2 and Phase 2.1 tables are not touched.

Usage:
    python src/materialize_document_kpi_mart.py

Prerequisites:
    - Docker stack must be running:
        docker compose -f metabase/docker-compose.yml up -d
    - Phase 3.2 extracted metrics must be loaded:
        python src/load_extracted_metrics_postgres.py
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
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE     = PROJECT_ROOT / "metabase" / ".env"
SQL_MART     = PROJECT_ROOT / "metabase" / "postgres" / "sql" / "08_create_document_kpi_mart.sql"

# ---------------------------------------------------------------------------
# Validation expectations for Demo Manufacturing FY2025 (sample dataset)
# ---------------------------------------------------------------------------
PIVOT_TABLE = "transforms.document_financial_metric_pivot"
MART_TABLE  = "transforms.mart_document_company_financial_performance"

EXPECTED_PIVOT_ROWS    = 1
EXPECTED_MART_ROWS     = 1
EXPECTED_COMPANIES     = 1
EXPECTED_PERIODS       = 1
EXPECTED_NULL_REVENUE  = 0
EXPECTED_NULL_INCOME   = 0

SAMPLE_COMPANY = "Demo Manufacturing"
SAMPLE_PERIOD  = "FY2025"

EXPECTED_KPIS: dict[str, float] = {
    "gross_margin_pct":               30.00,
    "operating_margin_pct":           18.00,
    "net_margin_pct":                 12.00,
    "debt_to_assets_pct":             32.00,
    "cash_to_debt_pct":               37.50,
    "operating_cash_flow_margin_pct": 15.00,
    "cash_conversion_pct":           125.00,
}
EXPECTED_FLAG = "stable"


# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------

def load_env() -> None:
    """Load database credentials from metabase/.env into the process environment."""
    if not ENV_FILE.exists():
        print(f"ERROR: environment file not found at {ENV_FILE}", file=sys.stderr)
        print("  Copy metabase/.env.example to metabase/.env and fill in passwords.",
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
    print(f"  {label:<46} = {str(actual):<10}  [{status}]  (expected {expected})")
    return ok


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def run_validations(conn: psycopg2.extensions.connection) -> bool:
    """Run all validation checks. Returns True if every check passes."""
    all_passed = True

    with conn.cursor() as cur:

        # -- structural checks -----------------------------------------------

        cur.execute(f"SELECT COUNT(*) FROM {PIVOT_TABLE};")
        pivot_rows = cur.fetchone()[0]
        all_passed &= _check(
            f"{PIVOT_TABLE} row count",
            pivot_rows,
            EXPECTED_PIVOT_ROWS,
        )

        cur.execute(f"SELECT COUNT(*) FROM {MART_TABLE};")
        mart_rows = cur.fetchone()[0]
        all_passed &= _check(
            f"{MART_TABLE} row count",
            mart_rows,
            EXPECTED_MART_ROWS,
        )

        cur.execute(
            f"SELECT COUNT(DISTINCT company_name) FROM {MART_TABLE};"
        )
        distinct_companies = cur.fetchone()[0]
        all_passed &= _check("distinct companies", distinct_companies, EXPECTED_COMPANIES)

        cur.execute(
            f"SELECT COUNT(DISTINCT period_label) FROM {MART_TABLE};"
        )
        distinct_periods = cur.fetchone()[0]
        all_passed &= _check("distinct periods", distinct_periods, EXPECTED_PERIODS)

        cur.execute(
            f"SELECT COUNT(*) FROM {MART_TABLE} WHERE revenue IS NULL;"
        )
        null_revenue = cur.fetchone()[0]
        all_passed &= _check("null revenue rows", null_revenue, EXPECTED_NULL_REVENUE)

        cur.execute(
            f"SELECT COUNT(*) FROM {MART_TABLE} WHERE net_income IS NULL;"
        )
        null_income = cur.fetchone()[0]
        all_passed &= _check("null net_income rows", null_income, EXPECTED_NULL_INCOME)

        # -- KPI value checks for sample company ------------------------------

        kpi_columns = ", ".join(EXPECTED_KPIS.keys()) + ", financial_health_flag"
        cur.execute(
            f"""
            SELECT {kpi_columns}
            FROM   {MART_TABLE}
            WHERE  company_name = %s
              AND  period_label = %s;
            """,
            (SAMPLE_COMPANY, SAMPLE_PERIOD),
        )
        row = cur.fetchone()

        if row is None:
            print(f"  ERROR: no row found for {SAMPLE_COMPANY} {SAMPLE_PERIOD}")
            all_passed = False
        else:
            kpi_names = list(EXPECTED_KPIS.keys())
            for i, col in enumerate(kpi_names):
                actual_val = round(_to_float(row[i]), 2) if row[i] is not None else None
                all_passed &= _check(col, actual_val, EXPECTED_KPIS[col])

            flag_actual = row[len(kpi_names)]
            all_passed &= _check("financial_health_flag", flag_actual, EXPECTED_FLAG)

    return all_passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("Phase 3.3: Materialize Document-Derived KPI Mart")
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
        print(
            "  Is the Docker stack running?  "
            "Try: docker compose -f metabase/docker-compose.yml up -d",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        execute_sql_file(conn, SQL_MART)
        print(f"  {PIVOT_TABLE}  created")
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
