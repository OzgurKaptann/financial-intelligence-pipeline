# 02 - Product Requirements Document

## 1. Overview

The Financial Intelligence Pipeline helps transform messy financial source material into reliable analytical outputs. The first version uses synthetic data to prove the data model, SQL logic, validation rules, and reporting structure. Later versions can add real PDF, Excel, and presentation parsing.

## 2. Users

### Primary User

A data analyst or analytics engineer who wants to analyze company performance from financial documents.

### Secondary Users

- Finance manager
- CFO
- Investment analyst
- BI developer
- Hiring manager reviewing the portfolio

## 3. User Stories

### Analyst User Stories

- As an analyst, I want to load financial metric data into a structured database so I can query it consistently.
- As an analyst, I want every metric to have a clear definition so I can avoid interpretation errors.
- As an analyst, I want SQL KPI models so I can calculate margins, growth, debt ratios, and rankings.
- As an analyst, I want dashboard-ready tables so I can build BI visuals without reshaping data repeatedly.
- As an analyst, I want validation checks so I can detect missing values, duplicate records, and suspicious metrics.

### Executive User Stories

- As an executive, I want a short summary of company performance so I can understand key signals quickly.
- As an executive, I want to know which company is growing fastest.
- As an executive, I want to know which company has higher debt risk.
- As an executive, I want to see cash and profitability trends.

### Portfolio Reviewer User Stories

- As a reviewer, I want to see clean project structure.
- As a reviewer, I want to understand the business problem.
- As a reviewer, I want to inspect SQL models and metric definitions.
- As a reviewer, I want to see that the candidate understands validation and limitations.

## 4. Functional Requirements

### FR-001: Synthetic Data Generation

The system must generate or accept synthetic financial metric data for 3 companies across 2 periods.

Required fields:

- company_name
- period
- metric_name
- metric_value
- currency
- unit
- source_document
- extraction_method
- confidence_score

### FR-002: Database Schema

The system must create a SQLite database with dimension and fact tables.

Required tables:

- dim_company
- dim_period
- dim_metric
- fact_financial_metric
- fact_risk_keyword
- fact_document_source

### FR-003: Data Loading

The system must load synthetic financial data into SQLite.

The loader must:

- Validate required columns
- Handle missing values
- Avoid duplicates
- Print loading summary
- Use relative paths

### FR-004: KPI Modeling

The system must calculate:

- Revenue Growth %
- Gross Margin %
- Operating Margin %
- Net Margin %
- Debt / Assets %
- Cash / Debt %
- Operating Cash Flow Trend

### FR-005: Dashboard Mart

The system must create a table called:

```text
mart_company_financial_performance
```

Grain:

```text
one row per company per period
```

### FR-006: Executive Summary

The system must generate a Markdown summary including:

- Top growth company
- Most profitable company
- Highest debt risk company
- Cash position overview
- Key risks
- Recommended follow-up questions

### FR-007: Validation Report

The system must generate a validation report that checks:

- Missing values
- Duplicate records
- Period consistency
- Metric completeness
- Outlier values
- Confidence score distribution

## 5. Non-Functional Requirements

### NFR-001: Reproducibility

The project must run from local files without requiring paid services in the MVP.

### NFR-002: Explainability

Every calculated KPI must be traceable to source metric values.

### NFR-003: Simplicity

The MVP must avoid unnecessary frameworks and infrastructure.

### NFR-004: Portfolio Readability

The README and documentation must explain the project clearly to a non-technical reviewer.

### NFR-005: Extensibility

The design should allow future migration from synthetic data to real documents.

## 6. Acceptance Criteria

The MVP is accepted when:

- The repository structure is clean.
- Synthetic data exists and is clearly labeled.
- SQLite schema exists.
- Data can be loaded into the database.
- KPI SQL files are understandable.
- Mart table is dashboard-ready.
- Executive summary is generated.
- Validation report is generated.
- README explains how to run the project.

## 7. Priority

| Priority | Requirement |
|---|---|
| P0 | Synthetic data, schema, loader, KPI SQL, mart table |
| P1 | Executive summary, validation report, dashboard spec |
| P2 | Real document conversion |
| P3 | Metric extraction from real documents |
| P4 | Advanced AI summarization and cloud deployment |
