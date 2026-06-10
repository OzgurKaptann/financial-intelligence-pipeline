-- =============================================================================
-- Phase 2.1: Create Materialized Transform Mart
--
-- TABLE:   transforms.mart_company_financial_performance
-- GRAIN:   One row per company + period (6 rows in the MVP dataset)
--
-- PURPOSE:
--   Materialize the final dashboard mart (equivalent to Metabase Transform 03)
--   into a real PostgreSQL table under the transforms schema.
--   This makes the dashboard-ready output available as a persistent table that
--   can be queried directly without re-running the CTE chain at query time.
--
-- SOURCE:
--   analytics.fact_financial_metric + analytics.dim_* (star schema)
--   analytics.fact_risk_keyword (empty in synthetic MVP → 0 for all rows)
--
-- IDEMPOTENT:
--   Safe to rerun. DROP IF EXISTS + CREATE TABLE AS ensures a clean rebuild
--   on every execution.
--
-- OUTPUT COLUMNS: 20
--   Identifiers    (3): company_name, period_id, fiscal_period
--   Raw metrics    (9): revenue, previous_revenue, gross_profit,
--                       operating_profit, net_income, total_assets,
--                       total_debt, cash, operating_cash_flow
--   Calculated KPIs(8): revenue_growth_pct, gross_margin_pct,
--                       operating_margin_pct, net_margin_pct,
--                       debt_to_assets_pct, cash_to_debt_pct,
--                       operating_cash_flow_to_net_income, risk_keyword_count
-- =============================================================================

-- Ensure the transforms schema exists before creating the table
CREATE SCHEMA IF NOT EXISTS transforms;

-- Drop existing table so the script is fully idempotent
DROP TABLE IF EXISTS transforms.mart_company_financial_performance;

-- ── CTE 1: metric_pivot ──────────────────────────────────────────────────────
-- Rotate fact_financial_metric from long format (one row per metric) to wide
-- format (one row per company-period, each metric as a column).
CREATE TABLE transforms.mart_company_financial_performance AS
WITH metric_pivot AS (
    SELECT
        ffm.company_id,
        ffm.period_id,

        MAX(CASE WHEN dm.metric_name = 'revenue'
            THEN ffm.metric_value END)              AS revenue,

        MAX(CASE WHEN dm.metric_name = 'gross_profit'
            THEN ffm.metric_value END)              AS gross_profit,

        MAX(CASE WHEN dm.metric_name = 'operating_profit'
            THEN ffm.metric_value END)              AS operating_profit,

        MAX(CASE WHEN dm.metric_name = 'net_income'
            THEN ffm.metric_value END)              AS net_income,

        MAX(CASE WHEN dm.metric_name = 'total_assets'
            THEN ffm.metric_value END)              AS total_assets,

        MAX(CASE WHEN dm.metric_name = 'total_debt'
            THEN ffm.metric_value END)              AS total_debt,

        MAX(CASE WHEN dm.metric_name = 'cash'
            THEN ffm.metric_value END)              AS cash,

        MAX(CASE WHEN dm.metric_name = 'operating_cash_flow'
            THEN ffm.metric_value END)              AS operating_cash_flow

    FROM  analytics.fact_financial_metric  ffm
    JOIN  analytics.dim_metric             dm   ON dm.metric_id = ffm.metric_id
    GROUP BY ffm.company_id, ffm.period_id
),

-- ── CTE 2: kpi_base ──────────────────────────────────────────────────────────
-- Attach dimension labels (company name, fiscal period) to the pivoted metrics.
-- risk_keyword_count is hardcoded to 0: fact_risk_keyword has no rows in the
-- synthetic MVP and does not expose a mention_count column at this stage.
kpi_base AS (
    SELECT
        c.company_id,
        c.company_name,
        p.period_id,
        p.period_label                              AS fiscal_period,

        mp.revenue,
        mp.gross_profit,
        mp.operating_profit,
        mp.net_income,
        mp.total_assets,
        mp.total_debt,
        mp.cash,
        mp.operating_cash_flow,

        0::INTEGER                                  AS risk_keyword_count

    FROM  metric_pivot            mp
    JOIN  analytics.dim_company   c   ON c.company_id = mp.company_id
    JOIN  analytics.dim_period    p   ON p.period_id  = mp.period_id
),

-- ── CTE 3: with_prior_revenue ────────────────────────────────────────────────
-- Add the prior period's revenue for each company using LAG().
-- PARTITION BY company_id ensures growth is calculated within-company only.
-- ORDER BY period_id (integer) guarantees correct chronological ordering.
-- NULL for the first period → revenue_growth_pct will be NULL (correct).
with_prior_revenue AS (
    SELECT
        *,
        LAG(revenue) OVER (
            PARTITION BY company_id
            ORDER BY     period_id
        ) AS previous_revenue
    FROM kpi_base
)

-- ── Final SELECT — Materialized Mart ─────────────────────────────────────────
-- All 8 raw metrics passed through unchanged.
-- All 8 KPIs calculated with NULLIF division-by-zero protection.
-- NUMERIC columns preserve precision through all arithmetic.
SELECT

    -- Identifiers
    company_name,
    period_id,
    fiscal_period,

    -- Raw metrics (millions, synthetic data)
    revenue,
    previous_revenue,

    -- KPI 1: Revenue Growth %
    -- NULL for FY2024 (no prior period). Formula: (rev - prev) / prev * 100
    ROUND(
        (revenue - previous_revenue)
        / NULLIF(previous_revenue, 0)
        * 100,
        2
    )                                                       AS revenue_growth_pct,

    gross_profit,

    -- KPI 2: Gross Margin % — gross_profit / revenue * 100
    ROUND(gross_profit / NULLIF(revenue, 0) * 100, 2)      AS gross_margin_pct,

    operating_profit,

    -- KPI 3: Operating Margin % — operating_profit / revenue * 100
    ROUND(operating_profit / NULLIF(revenue, 0) * 100, 2)  AS operating_margin_pct,

    net_income,

    -- KPI 4: Net Margin % — net_income / revenue * 100
    ROUND(net_income / NULLIF(revenue, 0) * 100, 2)        AS net_margin_pct,

    total_assets,
    total_debt,

    -- KPI 5: Debt / Assets % — total_debt / total_assets * 100
    ROUND(total_debt / NULLIF(total_assets, 0) * 100, 2)   AS debt_to_assets_pct,

    cash,

    -- KPI 6: Cash / Debt % — cash / total_debt * 100
    ROUND(cash / NULLIF(total_debt, 0) * 100, 2)           AS cash_to_debt_pct,

    operating_cash_flow,

    -- KPI 7: Operating Cash Flow / Net Income — operating_cash_flow / net_income
    ROUND(operating_cash_flow / NULLIF(net_income, 0), 2)  AS operating_cash_flow_to_net_income,

    -- KPI 8: Risk Keyword Count — 0 for all rows in the synthetic MVP
    risk_keyword_count

FROM with_prior_revenue
ORDER BY company_name, period_id;
