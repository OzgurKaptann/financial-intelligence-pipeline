# 07 - Database Design

## Purpose

This document defines the database design for the MVP. The first implementation uses SQLite, but the model should be clean enough to migrate to PostgreSQL later.

## Modeling Approach

The model uses simple dimensional modeling:

- Dimension tables describe business entities.
- Fact tables store measurable events or values.
- Mart tables prepare analytics-ready outputs.

## Entity Relationship Overview

```text
dim_company           dim_period           dim_metric
     |                    |                    |
     +---------+----------+----------+---------+
               |                     
               v
      fact_financial_metric
               |
               v
mart_company_financial_performance

fact_document_source
fact_risk_keyword
```

## Tables

## 1. dim_company

### Grain

```text
one row per company
```

### Columns

| Column | Type | Description |
|---|---|---|
| company_id | integer primary key | Unique company ID |
| company_name | text | Company name |
| sector | text | Optional sector |
| country | text | Optional country |
| created_at | text | Insert timestamp |

## 2. dim_period

### Grain

```text
one row per reporting period
```

### Columns

| Column | Type | Description |
|---|---|---|
| period_id | integer primary key | Unique period ID |
| period_label | text | FY2024, FY2025, Q1 2025 |
| period_type | text | fiscal_year, quarter, month |
| period_start_date | date | Start date |
| period_end_date | date | End date |
| period_sort_order | integer | Sort order for analysis |

## 3. dim_metric

### Grain

```text
one row per standardized metric
```

### Columns

| Column | Type | Description |
|---|---|---|
| metric_id | integer primary key | Unique metric ID |
| metric_name | text | Snake_case metric name |
| metric_display_name | text | Human-readable name |
| metric_category | text | income_statement, balance_sheet, cash_flow, risk |
| metric_description | text | Definition |

## 4. fact_document_source

### Grain

```text
one row per source document
```

### Columns

| Column | Type | Description |
|---|---|---|
| document_id | integer primary key | Unique document ID |
| company_id | integer | FK to dim_company |
| period_id | integer | FK to dim_period |
| file_name | text | Source file name |
| file_type | text | pdf, xlsx, pptx, csv |
| source_type | text | annual_report, investor_presentation, synthetic |
| processing_status | text | success, failed, pending |

## 5. fact_financial_metric

### Grain

```text
one row per company + period + metric + source_document
```

### Columns

| Column | Type | Description |
|---|---|---|
| financial_metric_id | integer primary key | Unique fact ID |
| company_id | integer | FK to dim_company |
| period_id | integer | FK to dim_period |
| metric_id | integer | FK to dim_metric |
| document_id | integer | FK to fact_document_source |
| metric_value | real | Numeric metric value |
| currency | text | Currency code |
| unit | text | actual, thousand, million, billion |
| extraction_method | text | synthetic, manual, regex, table_parser, llm_assisted |
| confidence_score | real | 0 to 1 |
| validation_status | text | pending, passed, failed, reviewed |

## 6. fact_risk_keyword

### Grain

```text
one row per company + period + risk keyword + source document
```

### Columns

| Column | Type | Description |
|---|---|---|
| risk_keyword_id | integer primary key | Unique ID |
| company_id | integer | FK to dim_company |
| period_id | integer | FK to dim_period |
| document_id | integer | FK to fact_document_source |
| risk_keyword | text | Keyword or phrase |
| risk_category | text | macro, liquidity, operational, regulatory |
| mention_count | integer | Count of mentions |

## 7. mart_company_financial_performance

### Grain

```text
one row per company + period
```

### Purpose

Final table for dashboard and reporting.

### Columns

| Column | Description |
|---|---|
| company_name | Company name |
| period_label | Reporting period |
| revenue | Revenue |
| gross_profit | Gross profit |
| operating_profit | Operating profit |
| net_income | Net income |
| total_assets | Total assets |
| total_debt | Total debt |
| cash | Cash |
| operating_cash_flow | Operating cash flow |
| revenue_growth_pct | Revenue growth |
| gross_margin_pct | Gross margin |
| operating_margin_pct | Operating margin |
| net_margin_pct | Net margin |
| debt_to_assets_pct | Debt / Assets |
| cash_to_debt_pct | Cash / Debt |
| risk_keyword_count | Risk keyword mentions |

## Indexing Recommendations

For SQLite MVP:

- index on `fact_financial_metric(company_id, period_id, metric_id)`
- index on `dim_company(company_name)`
- index on `dim_period(period_label)`
- index on `dim_metric(metric_name)`

## Duplicate Prevention

The project should avoid duplicate metric rows for the same company-period-metric-source combination.

Suggested uniqueness rule:

```text
company_id + period_id + metric_id + document_id
```

## Migration to PostgreSQL

When migrating to PostgreSQL:

- Replace SQLite dynamic typing with explicit numeric types.
- Use `numeric(18,2)` for financial values.
- Add proper timestamps.
- Add schema namespace such as `analytics`.
- Consider dbt for transformation management.

## Database Design Principle

Do not store final KPIs only in dashboard tools. KPIs should be calculated in SQL so the logic is reviewable, testable, and reusable.
