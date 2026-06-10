-- =============================================================================
-- 02_create_analytics_tables.sql
-- Phase 2 — Create PostgreSQL analytics tables
--
-- PURPOSE:
--   Create all Phase 2 tables in the raw and analytics schemas.
--   This script is idempotent: it drops and recreates tables on every run.
--   Safe to rerun at any time — all drops are scoped to raw and analytics
--   schemas only. The transforms schema is not touched here.
--
-- SCHEMAS MODIFIED:
--   raw        — raw.synthetic_financial_metrics
--   analytics  — dim_company, dim_period, dim_metric,
--                fact_document_source, fact_financial_metric,
--                fact_risk_keyword
--
-- GRAIN:
--   raw.synthetic_financial_metrics  — one row per source CSV row (48 rows)
--   analytics.dim_company            — one row per company (3 rows)
--   analytics.dim_period             — one row per fiscal period (2 rows)
--   analytics.dim_metric             — one row per metric type (8 rows)
--   analytics.fact_document_source   — one row per company+period (6 rows)
--   analytics.fact_financial_metric  — one row per company+period+metric (48 rows)
--   analytics.fact_risk_keyword      — one row per company+period+keyword (0 in MVP)
--
-- TYPES:
--   NUMERIC is used for all financial values to avoid integer division
--   truncation when computing KPI ratios in downstream Metabase Transforms.
-- =============================================================================


-- =============================================================================
-- Drop existing tables in dependency order (fact tables before dimensions)
-- CASCADE removes any dependent objects (views, FK constraints).
-- Only raw and analytics schemas are touched.
-- =============================================================================

DROP TABLE IF EXISTS analytics.fact_risk_keyword    CASCADE;
DROP TABLE IF EXISTS analytics.fact_financial_metric CASCADE;
DROP TABLE IF EXISTS analytics.fact_document_source  CASCADE;
DROP TABLE IF EXISTS analytics.dim_metric            CASCADE;
DROP TABLE IF EXISTS analytics.dim_period            CASCADE;
DROP TABLE IF EXISTS analytics.dim_company           CASCADE;
DROP TABLE IF EXISTS raw.synthetic_financial_metrics CASCADE;


-- =============================================================================
-- raw.synthetic_financial_metrics
--
-- Landing table for data loaded directly from:
--   data/synthetic/synthetic_financial_metrics.csv
--
-- Column names and types mirror the CSV structure as closely as possible.
-- No transformations are applied at this layer.
-- The loaded_at column records when the row was inserted.
-- =============================================================================
CREATE TABLE raw.synthetic_financial_metrics (
    id                 SERIAL          PRIMARY KEY,
    company_id         INTEGER         NOT NULL,
    company_name       TEXT            NOT NULL,
    period_id          INTEGER         NOT NULL,
    period_label       TEXT            NOT NULL,
    metric_name        TEXT            NOT NULL,
    metric_value       NUMERIC         NOT NULL,
    currency           TEXT            NOT NULL,
    source_document    TEXT,
    extraction_method  TEXT,
    confidence_score   NUMERIC,
    is_synthetic       BOOLEAN,
    loaded_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE raw.synthetic_financial_metrics IS
    'Raw landing table for synthetic_financial_metrics.csv. '
    'One row per source CSV row. 48 rows expected for the MVP dataset.';


-- =============================================================================
-- analytics.dim_company
--
-- One row per unique company in the dataset.
-- company_id comes directly from the source CSV (not auto-generated).
-- Expected rows: 3 (Aurora Manufacturing, Nova Retail Group, Atlas Energy Systems)
-- =============================================================================
CREATE TABLE analytics.dim_company (
    company_id    INTEGER   PRIMARY KEY,
    company_name  TEXT      NOT NULL
);

COMMENT ON TABLE analytics.dim_company IS
    'Company dimension. One row per company. 3 rows expected.';


-- =============================================================================
-- analytics.dim_period
--
-- One row per unique fiscal period in the dataset.
-- period_id comes directly from the source CSV (not auto-generated).
-- Expected rows: 2 (FY2024, FY2025)
-- =============================================================================
CREATE TABLE analytics.dim_period (
    period_id     INTEGER   PRIMARY KEY,
    period_label  TEXT      NOT NULL
);

COMMENT ON TABLE analytics.dim_period IS
    'Fiscal period dimension. One row per period. 2 rows expected (FY2024, FY2025).';


-- =============================================================================
-- analytics.dim_metric
--
-- One row per unique metric type.
-- metric_id is auto-generated — join on metric_name to resolve IDs.
-- Expected rows: 8 (revenue, gross_profit, operating_profit, net_income,
--                   total_assets, total_debt, cash, operating_cash_flow)
-- =============================================================================
CREATE TABLE analytics.dim_metric (
    metric_id    SERIAL   PRIMARY KEY,
    metric_name  TEXT     NOT NULL  UNIQUE
);

COMMENT ON TABLE analytics.dim_metric IS
    'Metric type dimension. One row per metric name. 8 rows expected.';


-- =============================================================================
-- analytics.fact_document_source
--
-- One row per company + period combination recording the source document
-- metadata associated with that company-period slice.
-- Expected rows: 6 (3 companies × 2 periods)
--
-- FK references:
--   company_id → analytics.dim_company
--   period_id  → analytics.dim_period
-- =============================================================================
CREATE TABLE analytics.fact_document_source (
    id                 SERIAL      PRIMARY KEY,
    company_id         INTEGER     NOT NULL  REFERENCES analytics.dim_company(company_id),
    period_id          INTEGER     NOT NULL  REFERENCES analytics.dim_period(period_id),
    source_document    TEXT,
    extraction_method  TEXT,
    currency           TEXT,
    confidence_score   NUMERIC,
    is_synthetic       BOOLEAN,
    UNIQUE (company_id, period_id)
);

COMMENT ON TABLE analytics.fact_document_source IS
    'Source document metadata per company+period. 6 rows expected. '
    'Grain: one row per company+period.';


-- =============================================================================
-- analytics.fact_financial_metric
--
-- Core fact table. One row per company + period + metric combination.
-- Expected rows: 48 (3 companies × 2 periods × 8 metrics)
--
-- metric_value is NUMERIC to support precise ratio calculations downstream
-- (e.g., gross_profit / revenue) without integer division truncation.
--
-- FK references:
--   company_id → analytics.dim_company
--   period_id  → analytics.dim_period
--   metric_id  → analytics.dim_metric
-- =============================================================================
CREATE TABLE analytics.fact_financial_metric (
    id            SERIAL    PRIMARY KEY,
    company_id    INTEGER   NOT NULL  REFERENCES analytics.dim_company(company_id),
    period_id     INTEGER   NOT NULL  REFERENCES analytics.dim_period(period_id),
    metric_id     INTEGER   NOT NULL  REFERENCES analytics.dim_metric(metric_id),
    metric_value  NUMERIC   NOT NULL,
    UNIQUE (company_id, period_id, metric_id)
);

COMMENT ON TABLE analytics.fact_financial_metric IS
    'Core financial metric fact table. '
    'Grain: one row per company + period + metric. 48 rows expected.';


-- =============================================================================
-- analytics.fact_risk_keyword
--
-- Risk keyword counts per company + period.
-- In the current synthetic MVP dataset there are no risk keywords extracted,
-- so this table will contain 0 rows after the initial load.
-- The table is created here so that downstream Transforms can reference it.
--
-- FK references:
--   company_id → analytics.dim_company
--   period_id  → analytics.dim_period
-- =============================================================================
CREATE TABLE analytics.fact_risk_keyword (
    id             SERIAL    PRIMARY KEY,
    company_id     INTEGER   NOT NULL  REFERENCES analytics.dim_company(company_id),
    period_id      INTEGER   NOT NULL  REFERENCES analytics.dim_period(period_id),
    keyword        TEXT      NOT NULL,
    keyword_count  INTEGER   NOT NULL  DEFAULT 0,
    UNIQUE (company_id, period_id, keyword)
);

COMMENT ON TABLE analytics.fact_risk_keyword IS
    'Risk keyword counts per company+period. '
    '0 rows expected for the synthetic MVP dataset.';
