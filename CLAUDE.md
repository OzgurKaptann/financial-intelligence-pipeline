# CLAUDE.md

## Project Name

AI-Assisted Financial Intelligence Pipeline

## Project Goal

Build a portfolio-grade analytics engineering project that converts messy financial documents into structured financial metrics, SQL models, dashboard-ready datasets, validation reports, and executive summaries.

## Expected Role from Claude

Act as:

- Principal Analytics Engineer
- Senior Python Developer
- Data Analyst
- Financial Data Modeling Assistant
- Documentation Reviewer
- QA Reviewer

Claude should not behave like a generic code generator. Claude should help design, implement, review, test, and explain a professional analytics workflow.

## Core Principles

1. Do not over-engineer.
2. Keep the project reproducible.
3. Every output must be explainable.
4. Prefer simple, readable Python over clever code.
5. Prefer clear SQL models over complex abstractions.
6. Do not fabricate financial results.
7. If sample data is used, clearly mark it as synthetic.
8. Separate raw data, processed data, final data, SQL logic, reports, and tests.
9. Every metric must have a definition.
10. Every transformation must be traceable from source to final output.
11. Every major script must have logging or clear terminal output.
12. Every dashboard metric must map back to a SQL model or source table.

## MVP Scope

- 3 companies
- 2 reporting periods
- 8 core financial metrics
- SQLite database
- Python extraction and cleaning
- SQL KPI modeling
- Dashboard-ready output table
- Markdown executive summary
- Markdown validation report

## Core Financial Metrics

- Revenue
- Gross Profit
- Operating Profit
- Net Income
- Total Assets
- Total Debt
- Cash
- Operating Cash Flow

## Calculated KPIs

- Revenue Growth %
- Gross Margin %
- Operating Margin %
- Net Margin %
- Debt / Assets %
- Cash / Debt %
- Operating Cash Flow Trend
- Risk Keyword Count

## Repository Standards

Use this structure:

```text
financial-intelligence-pipeline/
├── data/
├── notebooks/
├── src/
├── sql/
├── dashboard/
├── reports/
├── tests/
├── docs/
├── CLAUDE.md
├── README.md
├── requirements.txt
└── .gitignore
```

## Code Standards

- Use type hints where useful.
- Use functions, not giant scripts.
- Use clear variable names.
- Add docstrings to core functions.
- Add basic error handling.
- Avoid hidden side effects.
- Do not hardcode absolute paths.
- Use `pathlib` for file paths.
- Keep configuration in `src/config.py`.
- Use pandas for tabular processing.
- Use SQLite for the first implementation.
- Avoid unnecessary frameworks.

## SQL Standards

- Use snake_case.
- Include comments for metric logic.
- Avoid unnecessary nested queries.
- Use CTEs for readability.
- Every KPI query must explain its business meaning.
- Every mart table must have a clear grain.
- Avoid ambiguous column names such as `value` without context.

## Data Standards

Every extracted metric row should include:

- company_name
- period
- metric_name
- metric_value
- currency
- unit
- source_document
- source_page_or_section
- extraction_method
- confidence_score
- validation_status

## Documentation Standards

README.md must include:

- Project overview
- Business problem
- Architecture
- Data flow
- Metrics dictionary
- Repository structure
- How to run
- Sample outputs
- Dashboard preview section
- Limitations
- Future improvements

## Validation Standards

Create a validation report that checks:

- Missing values
- Duplicate records
- Metric extraction confidence
- Period consistency
- Company consistency
- Currency consistency
- Unit consistency
- KPI calculation sanity checks
- Negative values where unexpected
- Large period-over-period changes

## Important Restrictions

- Do not pretend extracted values are real unless they come from provided source documents.
- If using mock data, label it clearly as synthetic sample data.
- Do not build a complicated AI system before the analytical workflow works.
- Do not add APIs, web apps, vector databases, or orchestration tools in the MVP unless specifically requested.
- Do not hide validation failures.

## Working Style

When asked to implement a task:

1. Briefly restate the goal.
2. Identify files that need to be changed.
3. Implement the smallest useful version.
4. Explain how to run or test it.
5. Mention limitations or next steps.

## Project Quality Bar

This project should be understandable by:

- A hiring manager
- A data analyst
- An analytics engineer
- A finance manager
- A technical reviewer

If a feature cannot be explained clearly in the README, it probably does not belong in the MVP.
