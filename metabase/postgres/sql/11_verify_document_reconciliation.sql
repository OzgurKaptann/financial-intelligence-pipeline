-- =============================================================================
-- 11_verify_document_reconciliation.sql
-- Phase 4 — Validation Checks for Document Reconciliation Tables
--
-- PURPOSE:
--   Validate that transforms.document_metric_reconciliation and
--   transforms.document_kpi_reconciliation_summary were created correctly
--   and contain the expected values for the current sample dataset
--   (Demo Manufacturing FY2025).
--
-- EXPECTED BEHAVIOR (current sample):
--   The sample document company is "Demo Manufacturing".
--   The synthetic benchmark companies are "Aurora Manufacturing",
--   "Nova Retail Group", and "Atlas Energy Systems".
--   Because "Demo Manufacturing" does not match any synthetic company,
--   ALL document records will have match_status = 'unmatched_company_or_period'.
--   This is CORRECT — the reconciliation layer handles unmatched records
--   safely and does not fail on them.
--
-- CHECKS:
--   1. document_metric_reconciliation row count = 1
--   2. document_kpi_reconciliation_summary row count = 1
--   3. matched_records = 0
--   4. unmatched_records = 1
--   5. match_rate_pct = 0.00
--   6. Demo Manufacturing FY2025 match_status = 'unmatched_company_or_period'
-- =============================================================================


-- Check 1: Reconciliation table row count
SELECT
    'document_metric_reconciliation_row_count'      AS check_name,
    COUNT(*)                                        AS actual_value,
    1                                               AS expected_value,
    CASE WHEN COUNT(*) = 1 THEN 'PASS' ELSE 'FAIL' END  AS result
FROM transforms.document_metric_reconciliation;


-- Check 2: Summary table row count
SELECT
    'document_kpi_reconciliation_summary_row_count' AS check_name,
    COUNT(*)                                        AS actual_value,
    1                                               AS expected_value,
    CASE WHEN COUNT(*) = 1 THEN 'PASS' ELSE 'FAIL' END  AS result
FROM transforms.document_kpi_reconciliation_summary;


-- Check 3: matched_records = 0
SELECT
    'matched_records'                                       AS check_name,
    matched_records                                         AS actual_value,
    0                                                       AS expected_value,
    CASE WHEN matched_records = 0 THEN 'PASS' ELSE 'FAIL' END  AS result
FROM transforms.document_kpi_reconciliation_summary;


-- Check 4: unmatched_records = 1
SELECT
    'unmatched_records'                                             AS check_name,
    unmatched_records                                               AS actual_value,
    1                                                               AS expected_value,
    CASE WHEN unmatched_records = 1 THEN 'PASS' ELSE 'FAIL' END    AS result
FROM transforms.document_kpi_reconciliation_summary;


-- Check 5: match_rate_pct = 0.00
SELECT
    'match_rate_pct'                                                    AS check_name,
    match_rate_pct                                                      AS actual_value,
    0.00                                                                AS expected_value,
    CASE WHEN match_rate_pct = 0.00 THEN 'PASS' ELSE 'FAIL' END        AS result
FROM transforms.document_kpi_reconciliation_summary;


-- Check 6: Demo Manufacturing FY2025 match_status
SELECT
    'demo_manufacturing_match_status'                   AS check_name,
    match_status                                        AS actual_value,
    'unmatched_company_or_period'                       AS expected_value,
    CASE
        WHEN match_status = 'unmatched_company_or_period' THEN 'PASS'
        ELSE 'FAIL'
    END                                                 AS result
FROM transforms.document_metric_reconciliation
WHERE document_company_name = 'Demo Manufacturing'
  AND document_period_label = 'FY2025';
