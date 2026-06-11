-- =============================================================================
-- 09_verify_document_kpi_mart.sql
-- Phase 3.3 — Verify Document-Derived KPI Mart
--
-- PURPOSE:
--   Validate that the two Phase 3.3 transform tables were created correctly
--   and that the sample dataset (Demo Manufacturing FY2025) produces the
--   expected KPI values.
--
-- RUN AFTER:
--   08_create_document_kpi_mart.sql
--
-- EXPECTED RESULTS (sample dataset — one document, one company, one period):
--   pivot row count                           = 1
--   mart row count                            = 1
--   distinct companies                        = 1
--   distinct periods                          = 1
--   null revenue rows                         = 0
--   null net_income rows                      = 0
--   gross_margin_pct                          = 30.00
--   operating_margin_pct                      = 18.00
--   net_margin_pct                            = 12.00
--   debt_to_assets_pct                        = 32.00
--   cash_to_debt_pct                          = 37.50
--   operating_cash_flow_margin_pct            = 15.00
--   cash_conversion_pct                       = 125.00
--   financial_health_flag                     = stable
--
-- HOW TO RUN:
--   psql -h localhost -p 5433 -U analytics_user -d financial_analytics \
--     -f metabase/postgres/sql/09_verify_document_kpi_mart.sql
-- =============================================================================


-- ---------------------------------------------------------------------------
-- Check 1: transforms.document_financial_metric_pivot row count
-- Expected: 1 (one company-period in the sample dataset)
-- ---------------------------------------------------------------------------
SELECT
    'pivot_row_count'                                       AS check_name,
    COUNT(*)                                                AS actual_value,
    1                                                       AS expected_value,
    CASE WHEN COUNT(*) = 1 THEN 'PASS' ELSE 'FAIL' END     AS result
FROM transforms.document_financial_metric_pivot;


-- ---------------------------------------------------------------------------
-- Check 2: transforms.mart_document_company_financial_performance row count
-- Expected: 1
-- ---------------------------------------------------------------------------
SELECT
    'mart_row_count'                                        AS check_name,
    COUNT(*)                                                AS actual_value,
    1                                                       AS expected_value,
    CASE WHEN COUNT(*) = 1 THEN 'PASS' ELSE 'FAIL' END     AS result
FROM transforms.mart_document_company_financial_performance;


-- ---------------------------------------------------------------------------
-- Check 3: Distinct companies in mart
-- Expected: 1
-- ---------------------------------------------------------------------------
SELECT
    'distinct_companies'                                    AS check_name,
    COUNT(DISTINCT company_name)                            AS actual_value,
    1                                                       AS expected_value,
    CASE WHEN COUNT(DISTINCT company_name) = 1
         THEN 'PASS' ELSE 'FAIL' END                        AS result
FROM transforms.mart_document_company_financial_performance;


-- ---------------------------------------------------------------------------
-- Check 4: Distinct periods in mart
-- Expected: 1
-- ---------------------------------------------------------------------------
SELECT
    'distinct_periods'                                      AS check_name,
    COUNT(DISTINCT period_label)                            AS actual_value,
    1                                                       AS expected_value,
    CASE WHEN COUNT(DISTINCT period_label) = 1
         THEN 'PASS' ELSE 'FAIL' END                        AS result
FROM transforms.mart_document_company_financial_performance;


-- ---------------------------------------------------------------------------
-- Check 5: Null revenue rows in mart
-- Expected: 0
-- ---------------------------------------------------------------------------
SELECT
    'null_revenue_rows'                                     AS check_name,
    COUNT(*)                                                AS actual_value,
    0                                                       AS expected_value,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END     AS result
FROM transforms.mart_document_company_financial_performance
WHERE revenue IS NULL;


-- ---------------------------------------------------------------------------
-- Check 6: Null net_income rows in mart
-- Expected: 0
-- ---------------------------------------------------------------------------
SELECT
    'null_net_income_rows'                                  AS check_name,
    COUNT(*)                                                AS actual_value,
    0                                                       AS expected_value,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END     AS result
FROM transforms.mart_document_company_financial_performance
WHERE net_income IS NULL;


-- ---------------------------------------------------------------------------
-- Checks 7–14: KPI values for Demo Manufacturing FY2025
-- ---------------------------------------------------------------------------
SELECT
    'gross_margin_pct'                                      AS check_name,
    gross_margin_pct                                        AS actual_value,
    30.00                                                   AS expected_value,
    CASE WHEN gross_margin_pct = 30.00
         THEN 'PASS' ELSE 'FAIL' END                        AS result
FROM transforms.mart_document_company_financial_performance
WHERE company_name = 'Demo Manufacturing'
  AND period_label = 'FY2025';

SELECT
    'operating_margin_pct'                                  AS check_name,
    operating_margin_pct                                    AS actual_value,
    18.00                                                   AS expected_value,
    CASE WHEN operating_margin_pct = 18.00
         THEN 'PASS' ELSE 'FAIL' END                        AS result
FROM transforms.mart_document_company_financial_performance
WHERE company_name = 'Demo Manufacturing'
  AND period_label = 'FY2025';

SELECT
    'net_margin_pct'                                        AS check_name,
    net_margin_pct                                          AS actual_value,
    12.00                                                   AS expected_value,
    CASE WHEN net_margin_pct = 12.00
         THEN 'PASS' ELSE 'FAIL' END                        AS result
FROM transforms.mart_document_company_financial_performance
WHERE company_name = 'Demo Manufacturing'
  AND period_label = 'FY2025';

SELECT
    'debt_to_assets_pct'                                    AS check_name,
    debt_to_assets_pct                                      AS actual_value,
    32.00                                                   AS expected_value,
    CASE WHEN debt_to_assets_pct = 32.00
         THEN 'PASS' ELSE 'FAIL' END                        AS result
FROM transforms.mart_document_company_financial_performance
WHERE company_name = 'Demo Manufacturing'
  AND period_label = 'FY2025';

SELECT
    'cash_to_debt_pct'                                      AS check_name,
    cash_to_debt_pct                                        AS actual_value,
    37.50                                                   AS expected_value,
    CASE WHEN cash_to_debt_pct = 37.50
         THEN 'PASS' ELSE 'FAIL' END                        AS result
FROM transforms.mart_document_company_financial_performance
WHERE company_name = 'Demo Manufacturing'
  AND period_label = 'FY2025';

SELECT
    'operating_cash_flow_margin_pct'                        AS check_name,
    operating_cash_flow_margin_pct                          AS actual_value,
    15.00                                                   AS expected_value,
    CASE WHEN operating_cash_flow_margin_pct = 15.00
         THEN 'PASS' ELSE 'FAIL' END                        AS result
FROM transforms.mart_document_company_financial_performance
WHERE company_name = 'Demo Manufacturing'
  AND period_label = 'FY2025';

SELECT
    'cash_conversion_pct'                                   AS check_name,
    cash_conversion_pct                                     AS actual_value,
    125.00                                                  AS expected_value,
    CASE WHEN cash_conversion_pct = 125.00
         THEN 'PASS' ELSE 'FAIL' END                        AS result
FROM transforms.mart_document_company_financial_performance
WHERE company_name = 'Demo Manufacturing'
  AND period_label = 'FY2025';

SELECT
    'financial_health_flag'                                 AS check_name,
    financial_health_flag                                   AS actual_value,
    'stable'                                                AS expected_value,
    CASE WHEN financial_health_flag = 'stable'
         THEN 'PASS' ELSE 'FAIL' END                        AS result
FROM transforms.mart_document_company_financial_performance
WHERE company_name = 'Demo Manufacturing'
  AND period_label = 'FY2025';
