-- =============================================================================
-- 03_financial_kpis.sql
-- Financial Intelligence Pipeline — KPI Model
--
-- Transforms the normalised fact table into one analytical row per
-- company + period with all 8 raw metrics and all 8 calculated KPIs.
--
-- Source tables:
--   fact_financial_metric  — 48 rows (3 companies × 2 periods × 8 metrics)
--   dim_company            — 3 rows
--   dim_period             — 2 rows
--   dim_metric             — 8 rows
--   fact_risk_keyword      — 0 rows in synthetic MVP
--
-- Expected output: 6 rows (3 companies × 2 periods)
--
-- KPI formulas are documented inline. All percentage outputs are rounded
-- to 2 decimal places. Division by zero is guarded with NULLIF().
-- =============================================================================

-- =============================================================================
-- CTE 1: metric_pivot
--
-- Purpose:
--   Rotate fact_financial_metric from long format (one row per metric) to
--   wide format (one row per company-period, each metric as its own column).
--
-- Technique:
--   Conditional aggregation — MAX(CASE WHEN metric_name = '...' THEN value END).
--   MAX() is safe here because the UNIQUE constraint on
--   (company_id, period_id, metric_id) guarantees at most one value per cell.
--
-- Grain: one row per company_id + period_id
-- =============================================================================
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

-- =============================================================================
-- CTE 2: risk_counts
--
-- Purpose:
--   Aggregate risk keyword mentions per company-period from fact_risk_keyword.
--
-- In the synthetic MVP this table is empty, so every company-period will
-- receive a count of 0 via the LEFT JOIN + COALESCE in the next CTE.
-- When real document processing is added (Phase 8+), this CTE will
-- automatically pick up keyword counts without any SQL changes.
--
-- Grain: one row per company_id + period_id
-- =============================================================================
risk_counts AS (
    SELECT
        company_id,
        period_id,
        SUM(mention_count) AS total_risk_mentions
    FROM  fact_risk_keyword
    GROUP BY company_id, period_id
),

-- =============================================================================
-- CTE 3: kpi_base
--
-- Purpose:
--   Attach company and period labels to the pivoted metrics and bring in
--   the risk keyword count. This is the clean, labelled source for all
--   KPI calculations in the next CTE.
--
-- The LEFT JOIN to risk_counts means companies with no keyword data are
-- kept in the result with a 0 count rather than being dropped.
--
-- Grain: one row per company_id + period_id
-- =============================================================================
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

        -- COALESCE converts NULL (no keywords found) to 0
        COALESCE(rk.total_risk_mentions, 0) AS risk_keyword_count

    FROM  metric_pivot  mp
    JOIN  dim_company   c   ON c.company_id = mp.company_id
    JOIN  dim_period    p   ON p.period_id  = mp.period_id
    LEFT  JOIN risk_counts rk
               ON  rk.company_id = mp.company_id
               AND rk.period_id  = mp.period_id
),

-- =============================================================================
-- CTE 4: with_prior_revenue
--
-- Purpose:
--   Use LAG() to carry each company's prior period revenue alongside the
--   current row. This isolates the window function in one place so the
--   final SELECT stays readable.
--
-- LAG(revenue) OVER (PARTITION BY company_id ORDER BY period_id):
--   - Partitions by company so growth is never calculated across companies.
--   - Orders by period_id (integer) so FY2024 (id=1) precedes FY2025 (id=2).
--   - Returns NULL for the first period — correctly leaves growth as NULL.
--
-- Requires SQLite >= 3.25.0. This environment uses 3.45.3.
--
-- Grain: one row per company_id + period_id (same as kpi_base)
-- =============================================================================
with_prior_revenue AS (
    SELECT
        *,
        LAG(revenue) OVER (
            PARTITION BY company_id
            ORDER BY     period_id
        ) AS prior_period_revenue
    FROM kpi_base
)

-- =============================================================================
-- FINAL SELECT — KPI Calculations
--
-- All raw metrics are passed through unchanged.
-- All KPI columns are calculated here.
--
-- Division-by-zero protection:
--   NULLIF(denominator, 0) returns NULL instead of raising a division error.
--   NULL propagates through arithmetic so the KPI column becomes NULL rather
--   than crashing, which is the correct analytical behaviour.
-- =============================================================================
SELECT

    -- ── Identifiers ─────────────────────────────────────────────────────────
    company_id,
    company_name,
    sector,
    country,
    period_id,
    period_label,

    -- ── Raw metrics (passed through as-is) ──────────────────────────────────
    revenue,
    gross_profit,
    operating_profit,
    net_income,
    total_assets,
    total_debt,
    cash,
    operating_cash_flow,

    -- ── KPI 1: Revenue Growth %  ─────────────────────────────────────────────
    -- Business meaning: top-line growth from one period to the next.
    -- NULL for the first period because there is no prior period to compare.
    -- Formula: (current_revenue - prior_revenue) / prior_revenue * 100
    ROUND(
        (revenue - prior_period_revenue)
        / NULLIF(prior_period_revenue, 0)
        * 100,
        2
    ) AS revenue_growth_pct,

    -- ── KPI 2: Gross Margin %  ───────────────────────────────────────────────
    -- Business meaning: profitability after direct production costs.
    -- Formula: gross_profit / revenue * 100
    ROUND(
        gross_profit / NULLIF(revenue, 0) * 100,
        2
    ) AS gross_margin_pct,

    -- ── KPI 3: Operating Margin %  ───────────────────────────────────────────
    -- Business meaning: operating efficiency before interest and tax.
    -- Formula: operating_profit / revenue * 100
    ROUND(
        operating_profit / NULLIF(revenue, 0) * 100,
        2
    ) AS operating_margin_pct,

    -- ── KPI 4: Net Margin %  ─────────────────────────────────────────────────
    -- Business meaning: final profitability after all expenses and taxes.
    -- Formula: net_income / revenue * 100
    ROUND(
        net_income / NULLIF(revenue, 0) * 100,
        2
    ) AS net_margin_pct,

    -- ── KPI 5: Debt / Assets %  ──────────────────────────────────────────────
    -- Business meaning: balance sheet leverage — how much of assets are debt.
    -- Higher values indicate greater financial risk.
    -- Formula: total_debt / total_assets * 100
    ROUND(
        total_debt / NULLIF(total_assets, 0) * 100,
        2
    ) AS debt_to_assets_pct,

    -- ── KPI 6: Cash / Debt %  ────────────────────────────────────────────────
    -- Business meaning: liquidity — how much of debt is covered by cash.
    -- Values above 100% mean cash exceeds total debt.
    -- Formula: cash / total_debt * 100
    ROUND(
        cash / NULLIF(total_debt, 0) * 100,
        2
    ) AS cash_to_debt_pct,

    -- ── KPI 7: Operating Cash Flow / Net Income  ─────────────────────────────
    -- Business meaning: cash conversion quality.
    -- Values consistently above 1.0 indicate earnings are backed by real cash.
    -- Values below 1.0 or negative require investigation.
    -- Formula: operating_cash_flow / net_income
    ROUND(
        operating_cash_flow / NULLIF(net_income, 0),
        2
    ) AS operating_cash_flow_to_net_income,

    -- ── KPI 8: Risk Keyword Count  ───────────────────────────────────────────
    -- Business meaning: proxy for management-disclosed risk intensity.
    -- 0 in the synthetic MVP; populated when real documents are processed.
    risk_keyword_count

FROM with_prior_revenue
ORDER BY company_name, period_id;
