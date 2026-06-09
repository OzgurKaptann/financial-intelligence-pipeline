# 14 - Implementation Roadmap

## Purpose

This roadmap prevents the project from becoming too large too early. Build the useful core first, then expand.

## Phase 0: Documentation and Repository Setup

### Goal

Create a clean project foundation.

### Tasks

- Create repository folders.
- Add README.md.
- Add CLAUDE.md.
- Add documentation files.
- Add requirements.txt.
- Add .gitignore.
- Add placeholder Python, SQL, report, and dashboard files.

### Exit Criteria

- Repository structure is clean.
- Project purpose is understandable.
- MVP scope is documented.

## Phase 1: Synthetic Data MVP

### Goal

Create realistic sample data before touching real documents.

### Tasks

- Generate synthetic data for 3 companies and 2 periods.
- Include 8 required metrics.
- Include source fields and confidence scores.
- Save data to `data/synthetic/`.

### Exit Criteria

- Synthetic CSV exists.
- Synthetic data is clearly labeled.
- Every company-period has all 8 metrics.

## Phase 2: SQLite Database Layer

### Goal

Create normalized database structure.

### Tasks

- Write `sql/01_schema.sql`.
- Create dimension tables.
- Create fact tables.
- Add primary keys and foreign keys.
- Create data loader.

### Exit Criteria

- SQLite database can be created.
- Synthetic data can be loaded.
- Row counts match expected values.

## Phase 3: SQL KPI Layer

### Goal

Turn raw financial metrics into business KPIs.

### Tasks

- Create financial metric pivot model.
- Calculate margins.
- Calculate growth.
- Calculate debt and cash ratios.
- Create peer comparison queries.

### Exit Criteria

- KPI queries run without error.
- KPI formulas are documented.
- Division by zero is handled.

## Phase 4: Dashboard Mart

### Goal

Create final table for BI tools.

### Tasks

- Build `mart_company_financial_performance`.
- Export final mart to CSV.
- Create dashboard data dictionary.

### Exit Criteria

- One row per company-period.
- All required KPI columns exist.
- File can be loaded into Power BI/Tableau/Metabase.

## Phase 5: Validation Report

### Goal

Prove data quality control.

### Tasks

- Validate completeness.
- Validate duplicates.
- Validate numeric fields.
- Validate business rules.
- Generate Markdown validation report.

### Exit Criteria

- Validation report exists.
- Errors and warnings are separated.
- Issues are explainable.

## Phase 6: Executive Summary

### Goal

Generate business-readable output.

### Tasks

- Read final mart table.
- Identify strongest growth.
- Identify highest profitability.
- Identify highest debt risk.
- Identify cash position signals.
- Generate Markdown summary.

### Exit Criteria

- Executive summary exists.
- Claims are grounded in metrics.
- Limitations are included.

## Phase 7: Dashboard Build

### Goal

Build a visual business layer.

### Tasks

- Build 4 dashboard pages.
- Add KPI cards and visuals.
- Add metric definitions.
- Export screenshots.
- Add screenshots to README.

### Exit Criteria

- Dashboard answers business questions.
- Screenshots are present.
- README includes dashboard preview.

## Phase 8: Real Document Conversion

### Goal

Add real source document processing.

### Tasks

- Add document converter.
- Convert PDF/Excel/PPTX to Markdown/text.
- Save conversion logs.
- Do not extract metrics yet.

### Exit Criteria

- Raw documents can be converted.
- Conversion outputs are saved.
- Processing log exists.

## Phase 9: Real Metric Extraction

### Goal

Extract financial metrics from converted documents.

### Tasks

- Build metric mapping dictionary.
- Add regex/table parser extraction.
- Add confidence score.
- Add manual review field.
- Load extracted metrics into database.

### Exit Criteria

- At least one real document is processed.
- Extracted metrics include source traceability.
- Validation report identifies extraction quality.

## Phase 10: Portfolio Polish

### Goal

Make the project presentation-ready.

### Tasks

- Clean README.
- Add architecture diagram.
- Add dashboard screenshots.
- Add sample executive summary.
- Add limitations.
- Add future improvements.
- Review all docs.

### Exit Criteria

- GitHub repo is understandable in 2 minutes.
- Technical depth is visible.
- Business value is clear.

## Recommended First Sprint

Build only Phases 0 to 4 first.

Do not move to real documents before the synthetic pipeline works.
