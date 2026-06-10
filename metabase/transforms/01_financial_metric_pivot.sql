-- =============================================================================
-- Metabase Transform 01: Financial Metric Pivot
-- Phase 2 — Metabase Transforms Experiment
--
-- HOW TO CREATE THIS IN METABASE:
--   1. Open Metabase → New → Model (or Transform, depending on version).
--   2. Select the connected database (financial_intelligence or SQLite file).
--   3. Paste this SQL into the SQL editor.
--   4. Name the model: "Financial Metric Pivot".
--   5. Save. Other transforms will reference this model by name.
--
-- PURPOSE:
--   This is the first layer of the three-layer transform pipeline.
--   It rotates fact_financial_metric from long format (one row per metric)
--   into wide format (one row per company-period, each metric as a column).
--
-- SOURCE TABLES (must exist in the connected database):
--   fact_financial_metric  — 48 rows (3 companies × 2 periods × 8 metrics)
--   dim_metric             — 8 rows
--
-- OUTPUT GRAIN:
--   One row per company_id + period_id (6 rows in the MVP dataset)
--
-- OUTPUT COLUMNS:
--   company_id, period_id,
--   revenue, gross_profit, operating_profit, net_income,
--   total_assets, total_debt, cash, operating_cash_flow
--
-- TECHNIQUE:
--   Conditional aggregation — MAX(CASE WHEN metric_name = '...' THEN value END).
--   MAX() is safe here because the UNIQUE constraint on
--   (company_id, period_id, metric_id) guarantees at most one value per cell.
--
-- SOURCE: Adapted from CTE 1 (metric_pivot) in sql/03_financial_kpis.sql
--         and sql/05_mart_company_financial_performance.sql
-- =============================================================================

SELECT
    ffm.company_id,
    ffm.period_id,

    -- Revenue: total sales recognised in the period
    MAX(CASE WHEN dm.metric_name = 'revenue'
        THEN ffm.metric_value END)              AS revenue,

    -- Gross Profit: revenue minus cost of goods sold
    MAX(CASE WHEN dm.metric_name = 'gross_profit'
        THEN ffm.metric_value END)              AS gross_profit,

    -- Operating Profit: gross profit minus operating expenses (EBIT)
    MAX(CASE WHEN dm.metric_name = 'operating_profit'
        THEN ffm.metric_value END)              AS operating_profit,

    -- Net Income: bottom-line profit after interest and tax
    MAX(CASE WHEN dm.metric_name = 'net_income'
        THEN ffm.metric_value END)              AS net_income,

    -- Total Assets: all assets on the balance sheet
    MAX(CASE WHEN dm.metric_name = 'total_assets'
        THEN ffm.metric_value END)              AS total_assets,

    -- Total Debt: all interest-bearing liabilities
    MAX(CASE WHEN dm.metric_name = 'total_debt'
        THEN ffm.metric_value END)              AS total_debt,

    -- Cash: cash and cash equivalents
    MAX(CASE WHEN dm.metric_name = 'cash'
        THEN ffm.metric_value END)              AS cash,

    -- Operating Cash Flow: cash generated from core operations
    MAX(CASE WHEN dm.metric_name = 'operating_cash_flow'
        THEN ffm.metric_value END)              AS operating_cash_flow

FROM  fact_financial_metric ffm
JOIN  dim_metric             dm  ON dm.metric_id = ffm.metric_id
GROUP BY ffm.company_id, ffm.period_id
ORDER BY ffm.company_id, ffm.period_id;
