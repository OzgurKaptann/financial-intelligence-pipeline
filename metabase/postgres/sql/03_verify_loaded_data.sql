-- =============================================================================
-- 03_verify_loaded_data.sql
-- Phase 2 — Verify row counts after data load
--
-- Run this file after src/load_postgres_analytics.py to confirm all tables
-- were populated with the expected number of rows.
--
-- EXPECTED COUNTS (MVP synthetic dataset):
--   raw.synthetic_financial_metrics  : 48
--   analytics.dim_company            :  3
--   analytics.dim_period             :  2
--   analytics.dim_metric             :  8
--   analytics.fact_document_source   :  6
--   analytics.fact_financial_metric  : 48
--   analytics.fact_risk_keyword      :  0
-- =============================================================================

SELECT 'raw.synthetic_financial_metrics'  AS table_name,  COUNT(*)  AS row_count  FROM raw.synthetic_financial_metrics
UNION ALL
SELECT 'analytics.dim_company',           COUNT(*)  FROM analytics.dim_company
UNION ALL
SELECT 'analytics.dim_period',            COUNT(*)  FROM analytics.dim_period
UNION ALL
SELECT 'analytics.dim_metric',            COUNT(*)  FROM analytics.dim_metric
UNION ALL
SELECT 'analytics.fact_document_source',  COUNT(*)  FROM analytics.fact_document_source
UNION ALL
SELECT 'analytics.fact_financial_metric', COUNT(*)  FROM analytics.fact_financial_metric
UNION ALL
SELECT 'analytics.fact_risk_keyword',     COUNT(*)  FROM analytics.fact_risk_keyword
ORDER BY table_name;
