-- =============================================================================
-- 08_create_document_kpi_mart.sql
-- Phase 3.3 — Document-Derived KPI Mart
--
-- PURPOSE:
--   Build a transform-layer KPI mart from document-derived financial metrics
--   that were loaded into analytics.document_extracted_financial_metric in
--   Phase 3.2. This produces two tables:
--
--     transforms.document_financial_metric_pivot
--       Wide-format pivot of the 8 core metrics — one row per
--       source_file + company_name + period_label.
--
--     transforms.mart_document_company_financial_performance
--       KPI mart layered on top of the pivot — adds 7 calculated margin/
--       leverage ratios and a financial_health_flag per company-period.
--
-- SCHEMAS MODIFIED:
--   transforms — two new Phase 3.3 tables listed above
--
-- SCHEMAS NOT TOUCHED:
--   raw        — no changes
--   analytics  — no changes
--   transforms.mart_company_financial_performance — NOT modified (Phase 2.1)
--
-- IDEMPOTENCY:
--   Only the two Phase 3.3 tables are dropped and recreated.
--   All Phase 2 and Phase 2.1 tables are untouched.
--   Safe to rerun at any time.
--
-- GRAIN:
--   Both tables: one row per source_file + company_name + period_label
--
-- SOURCE:
--   analytics.document_extracted_financial_metric
--   (loaded by src/load_extracted_metrics_postgres.py in Phase 3.2)
--
-- DIVISION SAFETY:
--   All KPI divisions use NULLIF(denominator, 0) so zero denominators
--   yield NULL rather than a division-by-zero error.
-- =============================================================================


-- =============================================================================
-- Ensure the transforms schema exists
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS transforms;


-- =============================================================================
-- Drop Phase 3.3 tables only — in reverse dependency order
-- CASCADE removes any objects that depend on these specific tables.
-- Phase 2.1 table transforms.mart_company_financial_performance is NOT touched.
-- =============================================================================

DROP TABLE IF EXISTS transforms.mart_document_company_financial_performance CASCADE;
DROP TABLE IF EXISTS transforms.document_financial_metric_pivot             CASCADE;


-- =============================================================================
-- transforms.document_financial_metric_pivot
--
-- Rotates analytics.document_extracted_financial_metric from long format
-- (one row per metric name) to wide format (one row per document-company-period,
-- each of the 8 core metrics as its own column).
--
-- MAX(CASE WHEN ...) pattern is standard conditional aggregation that works on
-- all PostgreSQL versions and is consistent with the Phase 2 mart approach in
-- 04_create_transform_mart.sql.
--
-- Columns that did not appear in the source document will be NULL.
-- source_file is preserved as the primary document lineage key.
-- =============================================================================

CREATE TABLE transforms.document_financial_metric_pivot AS
SELECT
    source_file,
    company_name,
    period_label,

    -- Core metric columns — NULL when not extracted for this document
    MAX(CASE WHEN metric_name = 'revenue'
        THEN metric_value END)              AS revenue,

    MAX(CASE WHEN metric_name = 'gross_profit'
        THEN metric_value END)              AS gross_profit,

    MAX(CASE WHEN metric_name = 'operating_profit'
        THEN metric_value END)              AS operating_profit,

    MAX(CASE WHEN metric_name = 'net_income'
        THEN metric_value END)              AS net_income,

    MAX(CASE WHEN metric_name = 'total_assets'
        THEN metric_value END)              AS total_assets,

    MAX(CASE WHEN metric_name = 'total_debt'
        THEN metric_value END)              AS total_debt,

    MAX(CASE WHEN metric_name = 'cash'
        THEN metric_value END)              AS cash,

    MAX(CASE WHEN metric_name = 'operating_cash_flow'
        THEN metric_value END)              AS operating_cash_flow

FROM analytics.document_extracted_financial_metric
GROUP BY source_file, company_name, period_label
ORDER BY company_name, period_label;

COMMENT ON TABLE transforms.document_financial_metric_pivot IS
    'Wide-format pivot of document-derived financial metrics (Phase 3.3). '
    'Grain: one row per source_file + company_name + period_label. '
    'Source: analytics.document_extracted_financial_metric.';

COMMENT ON COLUMN transforms.document_financial_metric_pivot.source_file IS
    'Originating Markdown filename — primary document lineage key.';


-- =============================================================================
-- transforms.mart_document_company_financial_performance
--
-- KPI mart built on top of the pivot table above.
-- Calculates 7 margin/leverage ratios and classifies each company-period with
-- a financial_health_flag based on simple threshold rules.
--
-- KPI formulas (all rounded to 2 decimal places):
--   gross_margin_pct               = gross_profit        / revenue        * 100
--   operating_margin_pct           = operating_profit    / revenue        * 100
--   net_margin_pct                 = net_income          / revenue        * 100
--   debt_to_assets_pct             = total_debt          / total_assets   * 100
--   cash_to_debt_pct               = cash                / total_debt     * 100
--   operating_cash_flow_margin_pct = operating_cash_flow / revenue        * 100
--   cash_conversion_pct            = operating_cash_flow / net_income     * 100
--
-- financial_health_flag priority order:
--   1. 'negative_income'  — net_income < 0
--   2. 'high_debt'        — debt_to_assets_pct > 50
--   3. 'low_cash_buffer'  — cash_to_debt_pct   < 20
--   4. 'stable'           — all thresholds pass
--   NULL when insufficient data to evaluate
-- =============================================================================

CREATE TABLE transforms.mart_document_company_financial_performance AS
WITH pivot AS (
    SELECT *
    FROM transforms.document_financial_metric_pivot
),

kpis AS (
    SELECT
        source_file,
        company_name,
        period_label,

        -- Raw metrics passed through unchanged
        revenue,
        gross_profit,
        operating_profit,
        net_income,
        total_assets,
        total_debt,
        cash,
        operating_cash_flow,

        -- KPI 1: Gross Margin %
        ROUND(gross_profit / NULLIF(revenue, 0) * 100, 2)              AS gross_margin_pct,

        -- KPI 2: Operating Margin %
        ROUND(operating_profit / NULLIF(revenue, 0) * 100, 2)          AS operating_margin_pct,

        -- KPI 3: Net Margin %
        ROUND(net_income / NULLIF(revenue, 0) * 100, 2)                AS net_margin_pct,

        -- KPI 4: Debt / Assets %
        ROUND(total_debt / NULLIF(total_assets, 0) * 100, 2)           AS debt_to_assets_pct,

        -- KPI 5: Cash / Debt %
        ROUND(cash / NULLIF(total_debt, 0) * 100, 2)                   AS cash_to_debt_pct,

        -- KPI 6: Operating Cash Flow Margin %
        ROUND(operating_cash_flow / NULLIF(revenue, 0) * 100, 2)       AS operating_cash_flow_margin_pct,

        -- KPI 7: Cash Conversion % — operating_cash_flow relative to net_income
        ROUND(operating_cash_flow / NULLIF(net_income, 0) * 100, 2)    AS cash_conversion_pct

    FROM pivot
)

SELECT
    source_file,
    company_name,
    period_label,

    -- Raw metrics
    revenue,
    gross_profit,
    operating_profit,
    net_income,
    total_assets,
    total_debt,
    cash,
    operating_cash_flow,

    -- Calculated KPIs
    gross_margin_pct,
    operating_margin_pct,
    net_margin_pct,
    debt_to_assets_pct,
    cash_to_debt_pct,
    operating_cash_flow_margin_pct,
    cash_conversion_pct,

    -- Financial health classification
    -- Evaluated only when the required columns are not NULL.
    -- Priority: negative income > high debt > low cash buffer > stable.
    CASE
        WHEN net_income IS NULL AND debt_to_assets_pct IS NULL
            THEN NULL
        WHEN net_income < 0
            THEN 'negative_income'
        WHEN debt_to_assets_pct > 50
            THEN 'high_debt'
        WHEN cash_to_debt_pct < 20
            THEN 'low_cash_buffer'
        ELSE
            'stable'
    END                                                                 AS financial_health_flag,

    NOW()                                                               AS mart_created_at

FROM kpis
ORDER BY company_name, period_label;

COMMENT ON TABLE transforms.mart_document_company_financial_performance IS
    'Document-derived KPI mart (Phase 3.3). '
    'Grain: one row per source_file + company_name + period_label. '
    'Source: transforms.document_financial_metric_pivot. '
    'Contains 7 calculated KPI ratios and a financial_health_flag.';

COMMENT ON COLUMN transforms.mart_document_company_financial_performance.financial_health_flag IS
    'Classification based on KPI thresholds. '
    'Values: stable | negative_income | high_debt | low_cash_buffer | NULL (insufficient data).';

COMMENT ON COLUMN transforms.mart_document_company_financial_performance.mart_created_at IS
    'Timestamp when this row was materialized into the mart table.';
