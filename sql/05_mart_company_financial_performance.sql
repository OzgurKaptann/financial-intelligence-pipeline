-- =============================================================================
-- 05_mart_company_financial_performance.sql
-- Financial Intelligence Pipeline — Dashboard Mart View
--
-- Creates the mart view that acts as the single source of truth for
-- dashboards, executive summaries, and validation reports.
--
-- Mart grain: one row per company + period (6 rows in the MVP).
--
-- Business purpose:
--   Collapse the normalised star schema (fact + 3 dimensions) into one
--   flat, wide table that a BI tool (Power BI, Tableau, Metabase) or a
--   pandas DataFrame can consume without writing any additional SQL.
--
-- Why this is dashboard-ready:
--   - Every metric and KPI is pre-calculated and labelled.
--   - Column names are human-readable and snake_case for easy renaming.
--   - Division-by-zero is handled (NULLIF) so no runtime errors in BI tools.
--   - Revenue growth is NULL for the first period — tools will display this
--     cleanly rather than showing a misleading 0%.
--   - risk_keyword_count is 0 for all rows in the synthetic MVP because
--     fact_risk_keyword is empty. The column is already present so dashboards
--     built now will show real values automatically when Phase 8+ processing
--     populates the table.
--
-- Columns: 22
--   Identifiers   : company_id, company_name, sector, country,
--                   period_id, period_label
--   Raw metrics   : revenue, gross_profit, operating_profit, net_income,
--                   total_assets, total_debt, cash, operating_cash_flow
--   Calculated KPIs: revenue_growth_pct, gross_margin_pct,
--                    operating_margin_pct, net_margin_pct,
--                    debt_to_assets_pct, cash_to_debt_pct,
--                    operating_cash_flow_to_net_income, risk_keyword_count
--
-- Source tables:
--   fact_financial_metric, dim_company, dim_period,
--   dim_metric, fact_risk_keyword
-- =============================================================================

DROP VIEW IF EXISTS mart_company_financial_performance;

CREATE VIEW mart_company_financial_performance AS

-- ── CTE 1: metric_pivot ───────────────────────────────────────────────────────
-- Rotate fact_financial_metric from long format (one row per metric) to
-- wide format (one row per company-period, each metric as its own column).
-- MAX(CASE WHEN ...) is the standard SQLite conditional-aggregation pivot.
-- MAX() is safe because the UNIQUE constraint on (company_id, period_id, metric_id)
-- guarantees at most one value per cell.
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
-- Attach dimension labels (company name, sector, period label) and risk counts
-- to the pivoted metrics. This is the clean, labelled input for KPI formulas.
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
-- PARTITION BY company_id ensures growth is never calculated across companies.
-- ORDER BY period_id (integer) guarantees FY2024 (id=1) comes before FY2025 (id=2).
-- prior_period_revenue is NULL for the first period — revenue_growth_pct
-- will correctly be NULL rather than 0 for that row.
with_prior_revenue AS (
    SELECT
        *,
        LAG(revenue) OVER (
            PARTITION BY company_id
            ORDER BY     period_id
        ) AS prior_period_revenue
    FROM kpi_base
)

-- ── Final SELECT — KPI Calculations ──────────────────────────────────────────
-- All 8 raw metrics are passed through unchanged.
-- All 8 KPIs are calculated here with NULLIF division-by-zero protection.
-- Percentages are rounded to 2 decimal places.
SELECT

    -- Identifiers
    company_id,
    company_name,
    sector,
    country,
    period_id,
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

    -- KPI 1: Revenue Growth %
    -- Formula: (current_revenue - prior_revenue) / prior_revenue * 100
    -- NULL for the first period (no prior data to compare against).
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
    -- Values above 1.0 indicate strong cash conversion quality.
    ROUND(operating_cash_flow / NULLIF(net_income, 0), 2)  AS operating_cash_flow_to_net_income,

    -- KPI 8: Risk Keyword Count
    -- 0 for all rows in the synthetic MVP.
    -- Populated automatically when real documents are processed (Phase 8+).
    risk_keyword_count

FROM with_prior_revenue
ORDER BY company_name, period_id;
