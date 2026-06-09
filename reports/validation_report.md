# Validation Report

**Generated:** 2026-06-09 16:06:12
**Dataset:** `data/final/mart_company_financial_performance.csv`
**Rows:** 6
**Columns:** 22
**Checks run:** 16

---

## Results

| # | Check | Status | Detail |
|---|---|:---:|---|
| 1 | Row count | ✅ PASSED | 6 rows found (expected 6) |
| 2 | Column count | ✅ PASSED | 22 columns found (expected 22) |
| 3 | No nulls in raw metrics | ✅ PASSED | All 8 raw metric columns are fully populated. |
| 4 | No duplicate company-period rows | ✅ PASSED | Every (company_name, period_label) combination is unique. |
| 5 | All companies present | ✅ PASSED | 3 companies found: ['Atlas Energy Systems', 'Aurora Manufacturing', 'Nova Retail Group'] |
| 6 | All periods present | ✅ PASSED | 2 periods found: ['FY2024', 'FY2025'] |
| 7 | Grain integrity (one row per company-period) | ✅ PASSED | Every company-period combination has exactly 1 row. |
| 8 | gross_profit < revenue | ✅ PASSED | Gross profit is below revenue for all rows. |
| 9 | operating_profit < gross_profit | ✅ PASSED | Operating profit is below gross profit for all rows. |
| 10 | net_income < operating_profit | ✅ PASSED | Net income is below operating profit for all rows. |
| 11 | cash < total_assets | ✅ PASSED | Cash is below total assets for all rows. |
| 12 | total_debt < total_assets | ✅ PASSED | Total debt is below total assets for all rows. |
| 13 | FY2024 revenue_growth_pct is NULL | ✅ PASSED | All FY2024 rows correctly have NULL revenue_growth_pct (no prior period to compare against). |
| 14 | FY2025 revenue_growth_pct is populated | ✅ PASSED | All FY2025 growth values are present: Atlas Energy Systems: 8.0%, Aurora Manufacturing: 18.0%, Nova Retail Group: 12.0% |
| 15 | risk_keyword_count is 0 (synthetic MVP) | ✅ PASSED | All rows have risk_keyword_count = 0, as expected for the synthetic MVP (fact_risk_keyword is empty). |
| 16 | Percentage KPIs within 0–100 range | ✅ PASSED | gross_margin_pct, operating_margin_pct, net_margin_pct, debt_to_assets_pct are all within expected bounds. |

---

## Failed Checks

No failed checks.

---

## Warnings

No warnings.

---

## Summary

| Status | Count |
|---|---|
| ✅ PASSED  | 16 |
| ⚠️ WARNING | 0 |
| ❌ FAILED  | 0 |
| **Total**  | **16** |

---

## Final Verdict

✅ FULLY PASSED — All validation checks passed. Pipeline output is analytically safe.

---

> *This report is generated automatically from the pipeline mart CSV.*  
> *All data is synthetic sample data and does not represent real financial results.*
