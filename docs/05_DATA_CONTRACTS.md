# 05 - Data Contracts

## Purpose

Data contracts define the expected structure, meaning, and quality rules for key datasets. They prevent the project from becoming a collection of unclear CSV files.

## Contract 1: Synthetic Financial Metrics

### File

```text
data/synthetic/synthetic_financial_metrics.csv
```

### Grain

```text
one row per company + period + metric
```

### Required Columns

| Column | Type | Required | Example | Description |
|---|---:|---:|---|---|
| company_name | string | yes | Alpha Retail Holding | Company name |
| period | string | yes | FY2024 | Reporting period |
| period_start_date | date | yes | 2024-01-01 | Start date |
| period_end_date | date | yes | 2024-12-31 | End date |
| metric_name | string | yes | revenue | Standard metric name |
| metric_value | numeric | yes | 125000000 | Metric value |
| currency | string | yes | TRY | Currency code |
| unit | string | yes | actual | Unit scale |
| source_document | string | yes | synthetic_sample_data.csv | Source name |
| extraction_method | string | yes | synthetic | Source method |
| confidence_score | numeric | yes | 1.00 | Confidence between 0 and 1 |

### Accepted Metric Names

Use snake_case metric names:

- revenue
- gross_profit
- operating_profit
- net_income
- total_assets
- total_debt
- cash
- operating_cash_flow

### Quality Rules

- `company_name` must not be null.
- `period` must not be null.
- `metric_name` must belong to accepted list.
- `metric_value` must be numeric.
- `confidence_score` must be between 0 and 1.
- Each company-period must have all 8 metrics in the MVP.

## Contract 2: Extracted Financial Metrics

### File

```text
data/extracted/extracted_financial_metrics.csv
```

### Grain

```text
one row per extracted metric candidate
```

### Required Columns

| Column | Type | Required | Example |
|---|---:|---:|---|
| company_name | string | yes | Alpha Retail Holding |
| period | string | yes | FY2024 |
| metric_name_raw | string | yes | Net Sales |
| metric_name_standardized | string | yes | revenue |
| metric_value_raw | string | yes | 125.0 million TRY |
| metric_value_numeric | numeric | yes | 125000000 |
| currency | string | yes | TRY |
| unit | string | yes | million |
| source_document | string | yes | alpha_annual_report_2024.pdf |
| source_page_or_section | string | no | page 42 |
| extraction_method | string | yes | regex/table_parser/llm_assisted/manual |
| confidence_score | numeric | yes | 0.86 |
| validation_status | string | yes | pending |

### Validation Status Values

- pending
- passed
- failed
- reviewed
- excluded

## Contract 3: Document Processing Log

### File

```text
data/processed_markdown/document_processing_log.csv
```

### Grain

```text
one row per processed source document
```

### Columns

| Column | Description |
|---|---|
| document_id | Unique document identifier |
| file_name | Original file name |
| file_type | pdf, xlsx, pptx, docx, html |
| company_name | Company if known |
| period | Reporting period if known |
| processing_status | success, failed, skipped |
| processed_output_path | Markdown/text output path |
| error_message | Error if failed |
| processed_at | Timestamp |

## Contract 4: Dashboard Mart

### Table / File

```text
mart_company_financial_performance
```

### Grain

```text
one row per company + period
```

### Required Columns

| Column | Description |
|---|---|
| company_name | Company name |
| period | Reporting period |
| revenue | Revenue |
| gross_profit | Gross profit |
| operating_profit | Operating profit |
| net_income | Net income |
| total_assets | Total assets |
| total_debt | Total debt |
| cash | Cash |
| operating_cash_flow | Operating cash flow |
| revenue_growth_pct | Period-over-period revenue growth |
| gross_margin_pct | Gross profit / revenue |
| operating_margin_pct | Operating profit / revenue |
| net_margin_pct | Net income / revenue |
| debt_to_assets_pct | Total debt / total assets |
| cash_to_debt_pct | Cash / total debt |
| risk_keyword_count | Count of risk keywords |

## Contract 5: Executive Summary Input

The executive summary should read only from final, validated data.

Allowed inputs:

- `mart_company_financial_performance`
- validation report summary
- risk keyword summary

The summary must not use raw unvalidated extraction candidates.

## Versioning Rule

If a contract changes, update:

- this document
- README
- validation rules
- tests
- dashboard data dictionary
