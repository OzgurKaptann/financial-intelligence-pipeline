# 03 - Architecture

## Architecture Goal

The architecture should be simple enough to implement quickly, but structured enough to look like a professional analytics engineering project.

The key design principle:

> Separate ingestion, extraction, cleaning, storage, modeling, validation, and reporting.

## High-Level Architecture

```text
+-------------------------+
| Raw Documents / CSV     |
| PDF, Excel, PPTX, CSV   |
+-----------+-------------+
            |
            v
+-------------------------+
| Ingestion Layer         |
| document_converter.py   |
| synthetic_data_generator|
+-----------+-------------+
            |
            v
+-------------------------+
| Processing Layer        |
| metric_extractor.py     |
| data_cleaner.py         |
+-----------+-------------+
            |
            v
+-------------------------+
| Storage Layer           |
| SQLite database         |
| dimension/fact tables   |
+-----------+-------------+
            |
            v
+-------------------------+
| Modeling Layer          |
| SQL KPI queries         |
| mart tables             |
+-----------+-------------+
            |
            v
+-------------------------+
| Output Layer            |
| Dashboard-ready CSV     |
| Executive summary       |
| Validation report       |
+-------------------------+
```

## Layer Responsibilities

### 1. Source Layer

Contains raw input sources:

- Synthetic CSV files
- Raw PDF files
- Excel workbooks
- Investor presentations
- Markdown converted documents

MVP starts with synthetic CSV because this protects the project from early PDF extraction complexity.

### 2. Ingestion Layer

Responsible for bringing data into a usable intermediate format.

Files:

- `src/synthetic_data_generator.py`
- `src/document_converter.py`

MVP behavior:

- Generate or read synthetic financial metrics.
- Save them to `data/synthetic/`.

Future behavior:

- Convert PDF, Excel, Word, and PPTX files into Markdown/text.
- Save converted outputs into `data/processed_markdown/`.

### 3. Extraction Layer

Responsible for extracting structured financial values from text or synthetic sources.

Files:

- `src/metric_extractor.py`
- `src/data_cleaner.py`

MVP behavior:

- Read synthetic rows already structured.
- Normalize metric names, periods, currencies, and units.

Future behavior:

- Extract metrics from Markdown converted documents.
- Assign confidence scores.
- Capture source page or section.

### 4. Storage Layer

Responsible for storing normalized entities and facts.

Files:

- `sql/01_schema.sql`
- `src/database_loader.py`

Database:

- SQLite in MVP
- PostgreSQL in future version

Core model:

- Dimension tables for company, period, metric, document source
- Fact tables for financial metrics and risk keywords

### 5. Modeling Layer

Responsible for business calculations.

Files:

- `sql/03_financial_kpis.sql`
- `sql/04_peer_comparison.sql`
- `sql/05_mart_company_financial_performance.sql`

Outputs:

- KPI views
- Peer comparison tables
- Dashboard mart tables

### 6. Validation Layer

Responsible for quality control.

Files:

- `src/validation.py`
- `reports/validation_report.md`

Validation checks:

- Missing values
- Duplicate records
- Completeness by company-period
- Negative values
- Outlier period-over-period changes
- Low confidence extractions

### 7. Reporting Layer

Responsible for business-facing outputs.

Files:

- `src/report_generator.py`
- `reports/executive_summary.md`
- `dashboard/dashboard_spec.md`

Outputs:

- Markdown summary
- Dashboard-ready CSV
- BI dashboard screenshots

## Data Flow

```text
1. Raw files or synthetic data are placed in data/.
2. Python scripts convert or load the data.
3. Clean metric records are written to SQLite.
4. SQL queries calculate KPIs and mart tables.
5. Python exports final datasets and reports.
6. BI tool consumes mart_company_financial_performance.
```

## Why SQLite First?

SQLite is chosen for MVP because:

- No server setup
- Easy local reproducibility
- Good enough for portfolio-scale data
- Works well with Python
- Allows SQL modeling demonstration

PostgreSQL can be added later if the project needs stronger database realism.

## Extension Architecture

Future components can be added without breaking MVP:

| Future Feature | Where It Fits |
|---|---|
| Real PDF parsing | Ingestion layer |
| OCR for scanned PDFs | Ingestion layer |
| LLM-based extraction | Extraction layer |
| PostgreSQL migration | Storage layer |
| dbt models | Modeling layer |
| Power BI dashboard | Reporting layer |
| GitHub Actions | Orchestration layer |
| Streamlit app | Output layer |

## Anti-Overengineering Rule

Do not add orchestration, Docker, cloud, vector databases, or agents until the basic pipeline is complete.

A clean working MVP is more valuable than an impressive but broken architecture.
