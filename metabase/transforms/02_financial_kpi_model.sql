-- =============================================================================
-- Metabase Transform 02: Financial KPI Model
-- Phase 2 — Metabase Transforms Experiment
--
-- HOW TO CREATE THIS IN METABASE:
--   1. Open Metabase → New → Model (or Transform).
--   2. Select the connected database.
--   3. Paste this SQL into the SQL editor.
--   4. Name the model: "Financial KPI Model".
--   5. Save.
--
-- DEPENDENCY:
--   This transform references Transform 01 (Financial Metric Pivot).
--   In Metabase, reference the saved model by its name using the
--   {{#model-id}} syntax or by selecting it from the model picker.
--   For development/validation against SQLite, the metric_pivot CTE
--   is embedded here directly so the file is self-contained.
--
-- PURPOSE:
--   Second layer of the three-layer transform pipeline.
--   Joins the metric pivot to dimension tables, attaches risk keyword counts,
--   and calculates all 8 KPIs including revenue growth via LAG().
--
-- SOURCE TABLES (must exist in the connected database):
--   fact_financial_metric  — via Transform 01 (or embedded CTE)
--   dim_metric             — 8 rows
--   dim_company            — 3 rows
--   dim_period             — 2 rows
--   fact_risk_keyword      — 0 rows in the synthetic MVP
--
-- OUTPUT GRAIN:
--   One row per company + period (6 rows in the MVP dataset)
--
-- OUTPUT COLUMNS:
--   Identifiers (6), raw metrics (8), calculated KPIs (8) = 22 columns
--
-- SOURCE: Adapted from CTEs 1–4 and final SELECT in sql/03_financial_kpis.sql
-- =============================================================================

-- ── Embedded CTE: metric_pivot ───────────────────────────────────────────────
-- In a live Metabase implementation this would reference Transform 01
-- as a saved model. Embedded here for standalone validation.
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

    FROM  fact_financial_metric ffm
    JOIN  dim_metric             dm  ON dm.metric_id = ffm.metric_id
    GROUP BY ffm.company_id, ffm.period_id
),

-- ── CTE: risk_counts ─────────────────────────────────────────────────────────
-- Aggregate risk keyword mentions per company-period.
-- fact_risk_keyword is empty in the synthetic MVP.
-- All rows will receive 0 via COALESCE in kpi_base.
-- Populates automatically when Phase 8+ real document processing is added.
risk_counts AS (
    SELECT
        company_id,
        period_id,
        SUM(mention_count) AS total_risk_mentions
    FROM  fact_risk_keyword
    GROUP BY company_id, period_id
),

-- ── CTE: kpi_base ────────────────────────────────────────────────────────────
-- Attach dimension labels and risk counts to the pivoted metrics.
-- This is the clean, labelled input for all KPI formulas.
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

        -- COALESCE converts NULL (no risk keywords found) to 0
        COALESCE(rk.total_risk_mentions, 0) AS risk_keyword_count

    FROM  metric_pivot mp
    JOIN  dim_company  c   ON c.company_id = mp.company_id
    JOIN  dim_period   p   ON p.period_id  = mp.period_id
    LEFT  JOIN risk_counts rk
               ON  rk.company_id = mp.company_id
               AND rk.period_id  = mp.period_id
),

-- ── CTE: with_prior_revenue ──────────────────────────────────────────────────
-- Use LAG() to carry the prior period's revenue alongside the current row.
-- PARTITION BY company_id ensures growth is never calculated across companies.
-- ORDER BY period_id (integer) guarantees FY2024 (id=1) precedes FY2025 (id=2).
-- prior_period_revenue is NULL for the first period — revenue_growth_pct
-- will correctly be NULL rather than showing a misleading 0%.
-- Requires SQLite >= 3.25.0 (window function support).
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

    -- ── Identifiers ──────────────────────────────────────────────────────────
    company_id,
    company_name,
    sector,
    country,
    period_id,
    period_label,

    -- ── Raw metrics (passed through unchanged) ────────────────────────────────
    revenue,
    gross_profit,
    operating_profit,
    net_income,
    total_assets,
    total_debt,
    cash,
    operating_cash_flow,

    -- ── KPI 1: Revenue Growth % ───────────────────────────────────────────────
    -- Business meaning: top-line growth from one period to the next.
    -- NULL for the first period — no prior period exists to compare against.
    -- Formula: (current_revenue - prior_revenue) / prior_revenue * 100
    ROUND(
        (revenue - prior_period_revenue)
        / NULLIF(prior_period_revenue, 0)
        * 100,
        2
    ) AS revenue_growth_pct,

    -- ── KPI 2: Gross Margin % ────────────────────────────────────────────────
    -- Business meaning: profitability after direct production costs.
    -- Formula: gross_profit / revenue * 100
    ROUND(
        gross_profit / NULLIF(revenue, 0) * 100,
        2
    ) AS gross_margin_pct,

    -- ── KPI 3: Operating Margin % ────────────────────────────────────────────
    -- Business meaning: operating efficiency before interest and tax.
    -- Formula: operating_profit / revenue * 100
    ROUND(
        operating_profit / NULLIF(revenue, 0) * 100,
        2
    ) AS operating_margin_pct,

    -- ── KPI 4: Net Margin % ──────────────────────────────────────────────────
    -- Business meaning: final profitability after all expenses and taxes.
    -- Formula: net_income / revenue * 100
    ROUND(
        net_income / NULLIF(revenue, 0) * 100,
        2
    ) AS net_margin_pct,

    -- ── KPI 5: Debt / Assets % ───────────────────────────────────────────────
    -- Business meaning: balance sheet leverage — what proportion of assets is
    -- funded by debt. Higher values indicate greater financial risk.
    -- Formula: total_debt / total_assets * 100
    ROUND(
        total_debt / NULLIF(total_assets, 0) * 100,
        2
    ) AS debt_to_assets_pct,

    -- ── KPI 6: Cash / Debt % ─────────────────────────────────────────────────
    -- Business meaning: liquidity — what proportion of total debt is covered
    -- by available cash. Values above 100% mean cash exceeds total debt.
    -- Formula: cash / total_debt * 100
    ROUND(
        cash / NULLIF(total_debt, 0) * 100,
        2
    ) AS cash_to_debt_pct,

    -- ── KPI 7: Operating Cash Flow / Net Income ───────────────────────────────
    -- Business meaning: cash conversion quality.
    -- Values consistently above 1.0 indicate earnings are backed by real cash.
    -- Values below 1.0 or negative require further investigation.
    -- Formula: operating_cash_flow / net_income
    ROUND(
        operating_cash_flow / NULLIF(net_income, 0),
        2
    ) AS operating_cash_flow_to_net_income,

    -- ── KPI 8: Risk Keyword Count ─────────────────────────────────────────────
    -- Business meaning: proxy for management-disclosed risk intensity.
    -- 0 for all rows in the synthetic MVP (fact_risk_keyword is empty).
    -- Populates automatically when real document processing is added.
    risk_keyword_count

FROM with_prior_revenue
ORDER BY company_name, period_id;
