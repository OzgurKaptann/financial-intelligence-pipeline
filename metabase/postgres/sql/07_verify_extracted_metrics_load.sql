-- =============================================================================
-- 07_verify_extracted_metrics_load.sql
-- Phase 3.2 — Validate extracted metrics load into PostgreSQL
--
-- PURPOSE:
--   Query row counts and data quality checks for the three Phase 3.2 tables.
--   Run after src/load_extracted_metrics_postgres.py to confirm the load succeeded.
--
-- TABLES QUERIED:
--   raw.extracted_financial_metrics
--   analytics.document_extracted_financial_metric
--
-- EXPECTED VALUES (sample dataset — 1 document, Demo Manufacturing, FY2025):
--   raw.extracted_financial_metrics row count            = 8
--   analytics.document_extracted_financial_metric count  = 8
--   distinct companies                                   = 1
--   distinct periods                                     = 1
--   distinct metrics                                     = 8
--   failed extraction rows                               = 0
--   null metric_value rows                               = 0
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 1. Raw table row count
--    Expected: 8 rows for the sample dataset
-- ---------------------------------------------------------------------------
SELECT
    'raw.extracted_financial_metrics'       AS check_name,
    COUNT(*)                                AS row_count,
    8                                       AS expected,
    CASE WHEN COUNT(*) = 8 THEN 'PASS' ELSE 'FAIL' END AS status
FROM raw.extracted_financial_metrics

UNION ALL

-- ---------------------------------------------------------------------------
-- 2. Analytics table row count
--    Expected: 8 rows (only success rows with non-null metric_value are promoted)
-- ---------------------------------------------------------------------------
SELECT
    'analytics.document_extracted_financial_metric' AS check_name,
    COUNT(*)                                         AS row_count,
    8                                                AS expected,
    CASE WHEN COUNT(*) = 8 THEN 'PASS' ELSE 'FAIL' END AS status
FROM analytics.document_extracted_financial_metric

UNION ALL

-- ---------------------------------------------------------------------------
-- 3. Distinct company count in analytics table
--    Expected: 1 (Demo Manufacturing for the sample dataset)
-- ---------------------------------------------------------------------------
SELECT
    'distinct companies'                    AS check_name,
    COUNT(DISTINCT company_name)            AS row_count,
    1                                       AS expected,
    CASE WHEN COUNT(DISTINCT company_name) = 1 THEN 'PASS' ELSE 'FAIL' END AS status
FROM analytics.document_extracted_financial_metric

UNION ALL

-- ---------------------------------------------------------------------------
-- 4. Distinct period count in analytics table
--    Expected: 1 (FY2025 for the sample dataset)
-- ---------------------------------------------------------------------------
SELECT
    'distinct periods'                      AS check_name,
    COUNT(DISTINCT period_label)            AS row_count,
    1                                       AS expected,
    CASE WHEN COUNT(DISTINCT period_label) = 1 THEN 'PASS' ELSE 'FAIL' END AS status
FROM analytics.document_extracted_financial_metric

UNION ALL

-- ---------------------------------------------------------------------------
-- 5. Distinct metric name count in analytics table
--    Expected: 8 (all 8 canonical metrics extracted from the sample document)
-- ---------------------------------------------------------------------------
SELECT
    'distinct metrics'                      AS check_name,
    COUNT(DISTINCT metric_name)             AS row_count,
    8                                       AS expected,
    CASE WHEN COUNT(DISTINCT metric_name) = 8 THEN 'PASS' ELSE 'FAIL' END AS status
FROM analytics.document_extracted_financial_metric

UNION ALL

-- ---------------------------------------------------------------------------
-- 6. Failed extraction rows in raw table
--    Expected: 0 (all rows in the sample dataset have extraction_status = 'success')
-- ---------------------------------------------------------------------------
SELECT
    'failed extraction rows'                AS check_name,
    COUNT(*)                                AS row_count,
    0                                       AS expected,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM raw.extracted_financial_metrics
WHERE extraction_status <> 'success'

UNION ALL

-- ---------------------------------------------------------------------------
-- 7. Null metric_value rows in raw table
--    Expected: 0 (all successfully extracted rows have a numeric value)
-- ---------------------------------------------------------------------------
SELECT
    'null metric_value rows'                AS check_name,
    COUNT(*)                                AS row_count,
    0                                       AS expected,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM raw.extracted_financial_metrics
WHERE metric_value IS NULL

ORDER BY check_name;
