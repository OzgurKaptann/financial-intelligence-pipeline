# 12 - Validation and QA Plan

## Purpose

This project must show that the analyst does not blindly trust extracted data. Validation is one of the most important portfolio signals.

## Validation Output

```text
reports/validation_report.md
```

## Validation Levels

## Level 1: File Validation

Checks whether expected files exist.

Examples:

- synthetic CSV exists
- SQLite database exists
- SQL files exist
- final mart table exists

## Level 2: Schema Validation

Checks whether datasets contain required columns.

For synthetic metrics:

- company_name
- period
- metric_name
- metric_value
- currency
- unit
- source_document
- extraction_method
- confidence_score

## Level 3: Completeness Validation

Checks whether every company-period has all required metrics.

Required MVP metrics:

- revenue
- gross_profit
- operating_profit
- net_income
- total_assets
- total_debt
- cash
- operating_cash_flow

## Level 4: Duplicate Validation

Checks duplicate records by:

```text
company_name + period + metric_name + source_document
```

Duplicates should be reviewed or removed.

## Level 5: Numeric Validation

Checks:

- metric_value is numeric
- revenue is not null
- total_assets is positive
- cash is not greater than total_assets
- debt is not negative unless specifically allowed
- confidence_score is between 0 and 1

## Level 6: Business Logic Validation

Checks business relationships:

| Rule | Type |
|---|---|
| gross_profit should generally be <= revenue | warning |
| cash should generally be <= total_assets | error |
| total_debt should generally be <= total_assets or flagged | warning |
| revenue growth above 100% should be flagged | warning |
| margin above 100% should be flagged | warning |
| negative operating cash flow should be flagged but not rejected | warning |

## Level 7: KPI Validation

Checks whether KPI outputs are reasonable.

Examples:

- division by zero handled
- revenue growth null for first period
- margin calculations use revenue denominator
- debt_to_assets uses total_assets denominator
- cash_to_debt handles zero debt

## Level 8: Extraction Confidence Validation

For real documents:

| Confidence Score | Action |
|---:|---|
| >= 0.90 | pass automatically if numeric checks pass |
| 0.75 - 0.89 | pass with warning |
| 0.50 - 0.74 | manual review required |
| < 0.50 | exclude from final mart |

## Validation Report Structure

```md
# Validation Report

## Summary

- Total records checked:
- Passed checks:
- Warnings:
- Errors:

## Completeness Checks

...

## Duplicate Checks

...

## Numeric Checks

...

## Business Rule Checks

...

## KPI Sanity Checks

...

## Issues Requiring Review

...
```

## Severity Levels

### Error

Must be fixed before final output.

Examples:

- missing revenue
- non-numeric metric value
- duplicate core metric
- missing company name

### Warning

Should be reviewed but may be valid.

Examples:

- negative operating cash flow
- revenue growth above 100%
- net margin below 0%

### Info

Useful context.

Examples:

- synthetic data used
- first period has null revenue growth

## Acceptance Criteria

Validation is acceptable when:

- It runs after data loading.
- It produces a readable Markdown report.
- It separates errors from warnings.
- It does not silently ignore suspicious data.
- It explains what must be reviewed.

## Portfolio Message

Validation shows analytical maturity. The goal is not to pretend data is perfect. The goal is to prove that quality issues are visible, explainable, and controlled.
