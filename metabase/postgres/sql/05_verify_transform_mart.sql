-- =============================================================================
-- Phase 2.1: Verify Materialized Transform Mart
--
-- TABLE:   transforms.mart_company_financial_performance
--
-- PURPOSE:
--   Validate the materialized mart against expected row counts, FY2025
--   revenue growth values, FY2024 NULL growth behaviour, and risk keyword
--   counts.  Each check returns PASS or FAIL in the status column.
--
-- EXPECTED RESULTS:
--   All 6 checks should return PASS on a correctly loaded dataset.
-- =============================================================================

-- Check 1: Total row count must equal 6 (3 companies × 2 periods)
SELECT
    'row_count'                                         AS check_name,
    COUNT(*)::NUMERIC                                   AS actual_value,
    6::NUMERIC                                          AS expected_value,
    CASE WHEN COUNT(*) = 6 THEN 'PASS' ELSE 'FAIL' END AS status
FROM transforms.mart_company_financial_performance

UNION ALL

-- Check 2: FY2025 revenue_growth_pct — Atlas Energy Systems = 8.00
SELECT
    'atlas_fy2025_revenue_growth_pct',
    revenue_growth_pct,
    8.00,
    CASE WHEN revenue_growth_pct = 8.00 THEN 'PASS' ELSE 'FAIL' END
FROM transforms.mart_company_financial_performance
WHERE company_name  = 'Atlas Energy Systems'
  AND fiscal_period = 'FY2025'

UNION ALL

-- Check 3: FY2025 revenue_growth_pct — Aurora Manufacturing = 18.00
SELECT
    'aurora_fy2025_revenue_growth_pct',
    revenue_growth_pct,
    18.00,
    CASE WHEN revenue_growth_pct = 18.00 THEN 'PASS' ELSE 'FAIL' END
FROM transforms.mart_company_financial_performance
WHERE company_name  = 'Aurora Manufacturing'
  AND fiscal_period = 'FY2025'

UNION ALL

-- Check 4: FY2025 revenue_growth_pct — Nova Retail Group = 12.00
SELECT
    'nova_fy2025_revenue_growth_pct',
    revenue_growth_pct,
    12.00,
    CASE WHEN revenue_growth_pct = 12.00 THEN 'PASS' ELSE 'FAIL' END
FROM transforms.mart_company_financial_performance
WHERE company_name  = 'Nova Retail Group'
  AND fiscal_period = 'FY2025'

UNION ALL

-- Check 5: FY2024 revenue_growth_pct must be NULL for all companies
-- Returns count of rows where it is unexpectedly non-NULL (expected: 0)
SELECT
    'fy2024_revenue_growth_is_null',
    COUNT(*)::NUMERIC,
    0::NUMERIC,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM transforms.mart_company_financial_performance
WHERE fiscal_period        = 'FY2024'
  AND revenue_growth_pct  IS NOT NULL

UNION ALL

-- Check 6: risk_keyword_count = 0 for every row (synthetic MVP has no keywords)
-- Returns count of rows where it is unexpectedly non-zero (expected: 0)
SELECT
    'risk_keyword_count_all_zero',
    COUNT(*)::NUMERIC,
    0::NUMERIC,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM transforms.mart_company_financial_performance
WHERE risk_keyword_count <> 0

ORDER BY check_name;
