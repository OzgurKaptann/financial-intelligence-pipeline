# 16 - Claude Workflow Prompts

## Purpose

This document contains ready-to-use prompts for building the project with Claude Code or another AI coding assistant.

## How to Use These Prompts

Use one prompt at a time. Do not ask Claude to build the full project in one step.

The correct workflow is:

```text
small task → review output → run/test → commit → next task
```

## Prompt 1: Initialize Repository

```text
You are a Principal Analytics Engineer, Senior Python Developer, and Data Analyst.

Initialize the repository for the project "AI-Assisted Financial Intelligence Pipeline".

Create a clean, professional analytics engineering project structure.

Do not implement the full pipeline yet.

Create:
- README.md
- CLAUDE.md
- requirements.txt
- .gitignore
- folder structure
- placeholder Python modules
- placeholder SQL files
- placeholder notebook names
- dashboard specification file
- validation report template

The project should be designed for a data analyst / analytics engineer portfolio.

Keep the MVP focused:
3 companies, 2 periods, 8 financial metrics, SQLite, Python, SQL, dashboard-ready output, executive summary.

After creating the structure, explain what each folder and file is responsible for.
```

## Prompt 2: Generate Synthetic Data

```text
Create realistic synthetic financial metric data for 3 companies across 2 periods.

The dataset must include these metrics:
- revenue
- gross_profit
- operating_profit
- net_income
- total_assets
- total_debt
- cash
- operating_cash_flow

Required columns:
- company_name
- period
- period_start_date
- period_end_date
- metric_name
- metric_value
- currency
- unit
- source_document
- extraction_method
- confidence_score

Rules:
- Clearly label the data as synthetic.
- Keep values realistic and internally consistent.
- Revenue should generally be greater than gross_profit.
- Total assets should generally be greater than cash.
- Save output to data/synthetic/synthetic_financial_metrics.csv.
- Add a short explanation of the generated companies and periods.
```

## Prompt 3: Create SQLite Schema

```text
Create a clean SQLite schema for this project.

Tables:
- dim_company
- dim_period
- dim_metric
- fact_document_source
- fact_financial_metric
- fact_risk_keyword

Requirements:
- Use primary keys.
- Use foreign keys where appropriate.
- Include uniqueness constraints to prevent duplicate metric records.
- Add comments explaining the business meaning of each table.
- Save the SQL to sql/01_schema.sql.
```

## Prompt 4: Build Data Loader

```text
Create a Python script src/database_loader.py that loads data/synthetic/synthetic_financial_metrics.csv into SQLite.

Requirements:
- Use pathlib.
- Use pandas.
- Validate required columns.
- Create or connect to data/final/financial_intelligence.sqlite.
- Execute sql/01_schema.sql if tables do not exist.
- Load dimension tables first.
- Load fact_financial_metric after dimensions.
- Avoid duplicate inserts.
- Print a clear loading summary.
- Add useful docstrings.
```

## Prompt 5: Create KPI SQL

```text
Write SQL queries to calculate the financial KPIs for the project.

Create sql/03_financial_kpis.sql.

Required outputs:
- revenue_growth_pct
- gross_margin_pct
- operating_margin_pct
- net_margin_pct
- debt_to_assets_pct
- cash_to_debt_pct

Requirements:
- Use CTEs.
- Define output grain.
- Use null-safe division.
- Add comments explaining each KPI.
- Use period_sort_order for growth calculation.
```

## Prompt 6: Create Dashboard Mart

```text
Create sql/05_mart_company_financial_performance.sql.

The final table/view should be called mart_company_financial_performance.

Grain:
- one row per company and period

Columns:
- company_name
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

Add clear SQL comments.
```

## Prompt 7: Build Validation Report

```text
Create src/validation.py that validates the project data and generates reports/validation_report.md.

Validation checks:
- required files exist
- required columns exist
- all company-period combinations have 8 required metrics
- duplicate company-period-metric rows
- metric_value numeric and not null
- confidence_score between 0 and 1
- revenue not null
- cash <= total_assets warning
- gross_profit <= revenue warning
- first period revenue growth can be null

The report should separate errors, warnings, and info messages.
```

## Prompt 8: Build Executive Summary Generator

```text
Create src/report_generator.py.

The script should read mart_company_financial_performance from SQLite or exported CSV and generate reports/executive_summary.md.

The summary must include:
- reporting scope
- top growth company
- highest net margin company
- highest debt risk company
- cash position overview
- risk keyword overview if available
- recommended follow-up business questions
- limitations

Do not make unsupported claims.
Ground every statement in the final mart data.
```

## Prompt 9: Add Document Conversion Module

```text
Add src/document_converter.py.

The module should:
- read files from data/raw_documents
- convert supported documents to Markdown/text where possible
- save outputs to data/processed_markdown
- create data/processed_markdown/document_processing_log.csv
- log success and failures
- not extract financial metrics yet

Keep this module simple and separate from metric extraction.
```

## Prompt 10: Review Project Like a Hiring Manager

```text
Review this repository as a senior analytics engineering hiring manager.

Evaluate:
- business clarity
- technical structure
- SQL quality
- Python quality
- validation maturity
- dashboard readiness
- README quality
- portfolio strength

Give direct feedback.
Identify what is missing, what is weak, and what should be improved before publishing.
```

## Prompt Discipline Rule

Never give Claude a vague prompt like:

```text
Build the whole project.
```

That creates bloated, inconsistent work.

Use specific prompts with clear files, scope, and acceptance criteria.
