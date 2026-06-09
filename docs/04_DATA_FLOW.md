# 04 - Data Flow

## Purpose

This document explains how data moves from raw input to final analytical output.

## MVP Data Flow

The MVP uses synthetic financial metric data. This allows the project to prove the SQL model, metric logic, validation process, and dashboard output before handling messy real documents.

```text
data/synthetic/synthetic_financial_metrics.csv
        ↓
src/database_loader.py
        ↓
SQLite tables
        ↓
sql/03_financial_kpis.sql
        ↓
sql/05_mart_company_financial_performance.sql
        ↓
data/final/mart_company_financial_performance.csv
        ↓
reports/executive_summary.md
reports/validation_report.md
dashboard tool
```

## Future Real Document Data Flow

```text
data/raw_documents/*.pdf, *.xlsx, *.pptx
        ↓
src/document_converter.py
        ↓
data/processed_markdown/*.md
        ↓
src/metric_extractor.py
        ↓
data/extracted/extracted_financial_metrics.csv
        ↓
src/data_cleaner.py
        ↓
SQLite tables
        ↓
SQL KPI layer
        ↓
Dashboard mart + reports
```

## Input Zones

### `data/raw_documents/`

Original documents. Never edit manually after saving.

Examples:

- annual_report_company_a_2024.pdf
- investor_presentation_company_b_2025.pptx
- financial_statements_company_c_2024.xlsx

### `data/processed_markdown/`

Markdown/text outputs created from raw documents.

Purpose:

- easier text search
- easier extraction
- easier audit trail
- easier LLM processing

### `data/synthetic/`

Synthetic sample data used to develop the pipeline before real extraction is reliable.

All synthetic files must be clearly labeled.

### `data/extracted/`

Structured metric candidates extracted from documents.

At this stage, values may still need validation.

### `data/final/`

Final cleaned and dashboard-ready outputs.

Only validated, modeled, presentation-ready datasets should live here.

## Standard Metric Record

Every financial metric should eventually look like this:

| Column | Description |
|---|---|
| company_name | Company name |
| period | Reporting period |
| metric_name | Standardized metric name |
| metric_value | Numeric value |
| currency | Currency code |
| unit | Actual, thousands, millions, billions |
| source_document | File name |
| source_page_or_section | Page or section where metric was found |
| extraction_method | synthetic, manual, regex, table_parser, llm_assisted |
| confidence_score | 0 to 1 score |
| validation_status | pending, passed, failed, reviewed |

## Data Flow Quality Rules

1. Raw data must not be overwritten.
2. Processed files must be reproducible from raw files.
3. Extracted values must include source traceability.
4. Final values must pass validation rules.
5. Dashboard tables must not include ambiguous metric names.
6. Reports must not invent explanations beyond the data.

## Key Grain Definitions

### Metric Fact Grain

```text
one row per company + period + metric
```

### Dashboard Mart Grain

```text
one row per company + period
```

### Risk Keyword Fact Grain

```text
one row per company + period + risk_keyword + source_document
```

## Common Failure Points

| Failure | Example | Mitigation |
|---|---|---|
| Duplicate metrics | Revenue appears in both summary and income statement | Use source priority and validation |
| Different units | TRY million vs TRY thousand | Store and normalize unit |
| Different currency | USD vs TRY | Store currency separately; avoid mixing without conversion |
| Period mismatch | FY2024 vs Q4 2024 | Standardize period type |
| Negative values | Cash flow may be negative legitimately | Validate by metric context |
| OCR errors | 8 becomes B, 0 becomes O | Require confidence and manual review |
| Ambiguous labels | Sales vs Revenue | Metric mapping dictionary |

## Final Output Contract

The final dashboard table must be stable enough for BI tools. It should not require complex reshaping inside Power BI or Tableau.

Expected final table:

```text
mart_company_financial_performance
```

Minimum columns:

- company_id
- company_name
- period_id
- period_label
- revenue
- gross_profit
- operating_profit
- net_income
- total_assets
- total_debt
- cash
- operating_cash_flow
- revenue_growth_pct
- gross_margin_pct
- operating_margin_pct
- net_margin_pct
- debt_to_assets_pct
- cash_to_debt_pct
- risk_keyword_count
