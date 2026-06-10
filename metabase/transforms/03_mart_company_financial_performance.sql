-- =============================================================================
-- Metabase Transform 03: Mart — Company Financial Performance
-- Phase 2 — Metabase Transforms Experiment
--
-- HOW TO CREATE THIS IN METABASE:
--   1. Open Metabase → New → Model (or Transform).
--   2. Select the connected database.
--   3. Paste this SQL into the SQL editor.
--   4. Name the model: "Mart — Company Financial Performance".
--   5. Save. This model becomes the single source of truth for all
--      Metabase questions and dashboards in this project.
--
-- DEPENDENCY:
--   This transform is the third and final layer. It is equivalent to
--   Transform 02 (Financial KPI Model) exposed as a named mart model.
--   In a mature Metabase implementation, this transform would reference
--   Transform 02 directly. For standalone validation it is self-contained.
--
-- PURPOSE:
--   Dashboard mart — the single source of truth for BI consumption.
--   Collapses the star schema into one flat, wide table that Metabase
--   questions and dashboards can consume without writing additional SQL.
--
-- BUSINESS PURPOSE:
--   Provide a pre-calculated, labelled, human-readable dataset that a
--   hiring manager, finance manager, or analyst can use to build
--   charts and cross-company comparisons without understanding the
--   underlying data model.
--
-- MART GRAIN:
--   One row per company + period (6 rows in the MVP dataset).
--
-- OUTPUT COLUMNS: 22
--   Identifiers    (6): company_id, company_name, sector, country,
--                       period_id, period_label
--   Raw metrics    (8): revenue, gross_profit, operating_profit, net_income,
--                       total_assets, total_debt, cash, operating_cash_flow
--   Calculated KPIs(8): revenue_growth_pct, gross_margin_pct,
--                       operating_margin_pct, net_margin_pct,
--                       debt_to_assets_pct, cash_to_debt_pct,
--                       operating_cash_flow_to_net_income, risk_keyword_count
--
-- MVP EQUIVALENT:
--   This transform reproduces the output of:
--     sql/05_mart_company_financial_performance.sql  (CREATE VIEW)
--   and the CSV exported to:
--     dashboard/mart_company_financial_performance.csv
--
-- VALIDATION:
--   Row counts, column names, and numeric values should match exactly
--   against the MVP mart CSV when both use the same underlying database.
-- =============================================================================

-- ── CTE 1: metric_pivot ───────────────────────────────────────────────────────
-- Rotate fact_financial_metric from long format (one row per metric) to
-- wide format (one row per company-period, each metric as a column).
-- In a live Metabase implementation, reference Transform 01 as a saved model.
WITH metric_pivot AS (
    SELECT
        ffm.company_id,
        ffm.period_id,

        MAX(CASE WHEN dm.metric_name = 'revenue'
            THEN ffm.metric_value END)             AS revenue,

        MAX(CASE WHEN dm.metric_name = 'gross_profit'
            THEN ffm.metric_value END)             AS gross_profit,

        MAX(CASE WHEN dm.metric_name = 'operating_profit'
            THEN ffm.metric_value END)             AS operating_profit,

        MAX(CASE WHEN dm.metric_name = 'net_income'
            THEN ffm.metric_value END)             AS net_income,

        MAX(CASE WHEN dm.metric_name = 'total_assets'
            THEN ffm.metric_value END)             AS total_assets,

        MAX(CASE WHEN dm.metric_name = 'total_debt'
            THEN ffm.metric_value END)             AS total_debt,

        MAX(CASE WHEN dm.metric_name = 'cash'
            THEN ffm.metric_value END)             AS cash,

        MAX(CASE WHEN dm.metric_name = 'operating_cash_flow'
            THEN ffm.metric_value END)             AS operating_cash_flow

    FROM  fact_financial_metric ffm
    JOIN  dim_metric             dm  ON dm.metric_id = ffm.metric_id
    GROUP BY ffm.company_id, ffm.period_id
),

-- ── CTE 2: risk_counts ────────────────────────────────────────────────────────
-- Aggregate risk keyword mentions per company-period.
-- Empty in the synthetic MVP — every LEFT JOIN below produces 0 via COALESCE.
-- Will populate automatically when Phase 8+ document processing begins.
risk_counts AS (
    SELECT
        company_id,
        period_id,
        SUM(mention_count) AS total_risk_mentions
    FROM  fact_risk_keyword
    GROUP BY company_id, period_id
),

-- ── CTE 3: kpi_base ───────────────────────────────────────────────────────────
-- Attach dimension labels (company name, sector, country, period label)
-- and risk keyword counts to the pivoted metrics.
kpi_base AS (
    SELECT
        c.company_id,
        c.company_name,
        c.sector,
        c.country,
        p.period_id,
        p.period_label,

        mp.revenue,
        mp.gross_profit,
        mp.operating_profit,
        mp.net_income,
        mp.total_assets,
        mp.total_debt,
        mp.cash,
        mp.operating_cash_flow,

        COALESCE(rk.total_risk_mentions, 0) AS risk_keyword_count

    FROM  metric_pivot mp
    JOIN  dim_company  c   ON c.company_id = mp.company_id
    JOIN  dim_period   p   ON p.period_id  = mp.period_id
    LEFT  JOIN risk_counts rk
               ON  rk.company_id = mp.company_id
               AND rk.period_id  = mp.period_id
),

-- ── CTE 4: with_prior_revenue ─────────────────────────────────────────────────
-- Add the prior period's revenue for each company using LAG().
-- PARTITION BY company_id ensures growth is calculated within-company only.
-- ORDER BY period_id (integer) guarantees correct chronological order.
-- NULL for first period → revenue_growth_pct will be NULL (correct behaviour).
with_prior_revenue AS (
    SELECT
        *,
        LAG(revenue) OVER (
            PARTITION BY company_id
            ORDER BY     period_id
        ) AS prior_period_revenue
    FROM kpi_base
)

-- ── Final SELECT — Dashboard Mart ─────────────────────────────────────────────
-- All 8 raw metrics passed through unchanged.
-- All 8 KPIs calculated with NULLIF division-by-zero protection.
-- This output is the Metabase equivalent of the MVP mart view and CSV export.
SELECT

    -- Identifiers
    company_id,
    company_name,
    sector,
    country,
    period_id,
    period_label,

    -- Raw metrics (millions USD, synthetic data)
    revenue,
    gross_profit,
    operating_profit,
    net_income,
    total_assets,
    total_debt,
    cash,
    operating_cash_flow,

    -- KPI 1: Revenue Growth %
    -- NULL for the first period (no prior period to compare against).
    -- Formula: (current_revenue - prior_revenue) / prior_revenue * 100
    ROUND(
        (revenue - prior_period_revenue)
        / NULLIF(prior_period_revenue, 0)
        * 100,
        2
    ) AS revenue_growth_pct,

    -- KPI 2: Gross Margin %
    -- Formula: gross_profit / revenue * 100
    ROUND(gross_profit / NULLIF(revenue, 0) * 100, 2)      AS gross_margin_pct,

    -- KPI 3: Operating Margin %
    -- Formula: operating_profit / revenue * 100
    ROUND(operating_profit / NULLIF(revenue, 0) * 100, 2)  AS operating_margin_pct,

    -- KPI 4: Net Margin %
    -- Formula: net_income / revenue * 100
    ROUND(net_income / NULLIF(revenue, 0) * 100, 2)        AS net_margin_pct,

    -- KPI 5: Debt / Assets %
    -- Formula: total_debt / total_assets * 100
    ROUND(total_debt / NULLIF(total_assets, 0) * 100, 2)   AS debt_to_assets_pct,

    -- KPI 6: Cash / Debt %
    -- Formula: cash / total_debt * 100
    ROUND(cash / NULLIF(total_debt, 0) * 100, 2)           AS cash_to_debt_pct,

    -- KPI 7: Operating Cash Flow / Net Income
    -- Formula: operating_cash_flow / net_income
    ROUND(operating_cash_flow / NULLIF(net_income, 0), 2)  AS operating_cash_flow_to_net_income,

    -- KPI 8: Risk Keyword Count
    -- 0 for all rows in the synthetic MVP. Populated in Phase 8+.
    risk_keyword_count

FROM with_prior_revenue
ORDER BY company_name, period_id;
