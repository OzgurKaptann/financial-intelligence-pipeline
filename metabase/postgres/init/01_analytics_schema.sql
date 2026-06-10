-- =============================================================================
-- 01_analytics_schema.sql
-- Phase 2 — Analytics PostgreSQL initialisation script
--
-- This script runs automatically when the analytics_postgres container starts
-- for the first time (PostgreSQL executes all files in
-- /docker-entrypoint-initdb.d/ in filename order on a fresh data volume).
--
-- It does NOT run again on subsequent container restarts — only on first
-- initialisation of an empty data volume.
--
-- PURPOSE:
--   Create the three schemas that organise the Phase 2 analytics database.
--   Tables are NOT created here — they are loaded in a later step by the
--   Phase 2 data loader script (src/phase2_load_postgres.py, not yet written).
--
-- SCHEMAS:
--   raw        — source data imported directly from CSV exports
--   analytics  — cleaned and modelled data (dim/fact tables)
--   transforms — output tables written by Metabase Transforms
-- =============================================================================

-- Ensure we are operating on the correct database.
-- PostgreSQL init scripts always connect to the database named in POSTGRES_DB.
-- This comment is a reminder, not executable SQL.

-- =============================================================================
-- Schema: raw
--
-- Purpose:
--   Landing zone for data loaded from the existing synthetic CSV exports.
--   Data here should be minimally transformed — column names and types match
--   the source CSVs as closely as possible.
--   Future use: raw tables will hold data loaded directly from extracted
--   financial documents when PDF processing is added (Phase 8+).
--
-- Grain: one row per source record, no deduplication applied at this layer.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS raw;

COMMENT ON SCHEMA raw IS
    'Landing zone for source data loaded from CSV exports. '
    'Minimally transformed; matches source file structure.';

-- =============================================================================
-- Schema: analytics
--
-- Purpose:
--   Cleaned, modelled, and validated data. This is where the star schema
--   tables live: dim_company, dim_period, dim_metric, fact_financial_metric,
--   fact_risk_keyword.
--   These tables mirror the SQLite MVP schema but use PostgreSQL-native types
--   (NUMERIC instead of REAL to avoid integer division truncation in KPIs).
--
-- Grain: same as the MVP SQLite schema — see sql/01_schema.sql for reference.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS analytics;

COMMENT ON SCHEMA analytics IS
    'Star schema tables: dim_company, dim_period, dim_metric, '
    'fact_financial_metric, fact_risk_keyword. '
    'Mirrors the SQLite MVP schema with PostgreSQL-compatible types.';

-- =============================================================================
-- Schema: transforms
--
-- Purpose:
--   Output tables written by Metabase Transforms or by the Phase 2 validation
--   scripts. When Metabase executes a Transform and saves the result as a
--   table (rather than a view), it will land here.
--
--   Also used to materialise Transform outputs for row-by-row comparison
--   against the MVP mart CSV (dashboard/mart_company_financial_performance.csv).
--
-- Grain: one row per company + period (6 rows in the MVP dataset).
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS transforms;

COMMENT ON SCHEMA transforms IS
    'Output tables from Metabase Transforms and Phase 2 validation. '
    'mart_company_financial_performance will be compared against the MVP CSV.';

-- =============================================================================
-- Grant usage on all schemas to the analytics_user role.
-- The analytics_user connects with POSTGRES_ANALYTICS_USER credentials.
-- This block uses a DO block so the username is not hardcoded here — it is
-- read from the current_user context, which is the POSTGRES_ANALYTICS_USER
-- because PostgreSQL init scripts run as the superuser that owns the DB.
-- =============================================================================
DO $$
DECLARE
    db_owner TEXT;
BEGIN
    SELECT pg_catalog.pg_get_userbyid(datdba)
    INTO   db_owner
    FROM   pg_catalog.pg_database
    WHERE  datname = current_database();

    EXECUTE format('GRANT USAGE ON SCHEMA raw        TO %I', db_owner);
    EXECUTE format('GRANT USAGE ON SCHEMA analytics  TO %I', db_owner);
    EXECUTE format('GRANT USAGE ON SCHEMA transforms TO %I', db_owner);

    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA raw        GRANT ALL ON TABLES TO %I', db_owner);
    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA analytics  GRANT ALL ON TABLES TO %I', db_owner);
    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA transforms GRANT ALL ON TABLES TO %I', db_owner);
END $$;
