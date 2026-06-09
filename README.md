# AI-Assisted Financial Intelligence Pipeline

> **Note — Synthetic Data:** The current MVP uses fully synthetic, clearly labelled financial data for three fictional Turkish companies. No real financial documents or real company data are used at this stage. Real document ingestion is scoped for a future phase.

---

## Project Overview

An end-to-end analytics engineering portfolio project that converts financial data into structured metrics, SQL-based KPI models, dashboard-ready datasets, validation reports, and executive summaries.

The pipeline is intentionally built around clarity, traceability, and reproducibility rather than complexity. Every metric has a definition. Every transformation is traceable from source to final output. Every output can be explained to a non-technical stakeholder.

---

## Business Problem

A CFO, investment analyst, or BI team wants to compare multiple companies across reporting periods and answer questions such as:

- Which company is growing fastest?
- Which company is most profitable?
- Which company carries the most debt relative to assets?
- Is cash coverage of debt improving or deteriorating?
- Are management reports mentioning more risk language over time?

These questions require converting unstructured financial documents into a consistent analytical model — with validation to confirm the data can be trusted.

---

## Architecture

```
Synthetic CSV / Real Financial Documents (future)
        │
        ▼
  synthetic_data_generator.py
  (or: document extractor — Phase 2)
        │
        ▼
  database_loader.py
  → SQLite: dim_company, dim_period, dim_metric,
            fact_financial_metric, fact_document_source
        │
        ▼
  SQL KPI Models
  → sql/03_financial_kpis.sql
  → sql/05_mart_company_financial_performance.sql
        │
        ▼
  export_mart.py
  → data/final/mart_company_financial_performance.csv
        │
        ├──▶  validation.py        → reports/validation_report.md
        └──▶  report_generator.py  → reports/executive_summary.md
```

---

## Data Flow

| Step | Script | Input | Output |
|------|--------|-------|--------|
| 1 | `synthetic_data_generator.py` | Hard-coded definitions in `config.py` | `data/synthetic/synthetic_financial_metrics.csv` |
| 2 | `database_loader.py` | Synthetic CSV + `sql/01_schema.sql` | `data/final/financial_intelligence.sqlite` |
| 3 | `export_mart.py` | SQLite + `sql/05_mart_company_financial_performance.sql` | `data/final/mart_company_financial_performance.csv` |
| 4 | `validation.py` | Mart CSV | `reports/validation_report.md` |
| 5 | `report_generator.py` | Mart CSV | `reports/executive_summary.md` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Data processing | pandas |
| Database | SQLite (via Python `sqlite3`) |
| SQL modeling | Raw SQL with CTEs and window functions |
| Reporting | Markdown (auto-generated) |
| Path management | `pathlib` |
| Testing | pytest (future) |
| Dashboard (future) | Metabase or Power BI |

No orchestration frameworks, no vector databases, no external APIs in the MVP.

---

## Repository Structure

```
financial-intelligence-pipeline/
│
├── data/
│   ├── raw_documents/          ← Real PDFs/Excel go here (not committed)
│   ├── processed_markdown/     ← Converted documents (not committed)
│   ├── synthetic/              ← Synthetic CSV output
│   │   └── synthetic_financial_metrics.csv
│   ├── extracted/              ← AI-extracted metrics (future phase)
│   └── final/                  ← SQLite database + mart CSV (not committed)
│       ├── financial_intelligence.sqlite
│       └── mart_company_financial_performance.csv
│
├── src/
│   ├── config.py               ← All paths, companies, metrics, periods
│   ├── synthetic_data_generator.py
│   ├── database_loader.py
│   ├── export_mart.py
│   ├── validation.py
│   ├── report_generator.py
│   └── run_pipeline.py         ← Single command to run everything
│
├── sql/
│   ├── 01_schema.sql           ← Database schema + dimension seed data
│   ├── 03_financial_kpis.sql   ← KPI calculation query (8 KPIs)
│   └── 05_mart_company_financial_performance.sql  ← Dashboard mart view
│
├── dashboard/
│   └── screenshots/            ← Dashboard previews (placeholder)
│
├── reports/
│   ├── validation_report.md    ← Auto-generated, 16 checks
│   └── executive_summary.md    ← Auto-generated business narrative
│
├── docs/                       ← Full design documentation (25+ files)
│
├── tests/                      ← Test suite (future)
├── CLAUDE.md                   ← AI assistant instructions
├── README.md
├── requirements.txt
└── .gitignore
```

---

## How to Run

### Prerequisites

```bash
pip install -r requirements.txt
```

### Run the full pipeline

```bash
python src/run_pipeline.py
```

This runs all five stages in sequence and stops immediately if any stage fails.

### Run individual stages

```bash
python src/synthetic_data_generator.py
python src/database_loader.py
python src/export_mart.py
python src/validation.py
python src/report_generator.py
```

### Configuration

All companies, periods, metrics, paths, and currency are defined in `src/config.py`. No other file should hardcode these values.

---

## Expected Outputs

After a successful pipeline run:

| File | Description | Rows | Committed |
|------|-------------|------|-----------|
| `data/synthetic/synthetic_financial_metrics.csv` | Long-format raw metrics | 48 | Yes |
| `data/final/financial_intelligence.sqlite` | Normalized SQLite database (6 tables) | — | **No** |
| `data/final/mart_company_financial_performance.csv` | Dashboard-ready wide table | 6 | **No** |
| `reports/validation_report.md` | 16-check data quality report | — | Yes |
| `reports/executive_summary.md` | Business narrative | — | Yes |

The mart table has 6 rows (3 companies × 2 periods) and 22 columns (6 identifiers + 8 raw metrics + 8 KPIs).

> **`data/final/` is excluded from version control.** The SQLite database and mart CSV are generated artifacts — they are not committed to the repository. Regenerate them at any time by running `python src/run_pipeline.py`.

---

## Metrics Dictionary

### Core Metrics (extracted or generated)

| Metric | Definition | Unit |
|--------|-----------|------|
| `revenue` | Total sales revenue for the period | TRY (millions) |
| `gross_profit` | Revenue minus cost of goods sold | TRY (millions) |
| `operating_profit` | Gross profit minus operating expenses | TRY (millions) |
| `net_income` | Profit after all expenses, interest, and tax | TRY (millions) |
| `total_assets` | Total value of all assets on the balance sheet | TRY (millions) |
| `total_debt` | Total interest-bearing debt (short + long term) | TRY (millions) |
| `cash` | Cash and cash equivalents | TRY (millions) |
| `operating_cash_flow` | Net cash generated from operations | TRY (millions) |

### Calculated KPIs (SQL layer)

| KPI | Formula | Business Meaning |
|-----|---------|-----------------|
| `revenue_growth_pct` | (Current − Prior) / Prior × 100 | Year-over-year revenue change |
| `gross_margin_pct` | Gross Profit / Revenue × 100 | Production efficiency |
| `operating_margin_pct` | Operating Profit / Revenue × 100 | Operational profitability |
| `net_margin_pct` | Net Income / Revenue × 100 | Bottom-line profitability |
| `debt_to_assets_pct` | Total Debt / Total Assets × 100 | Leverage and solvency risk |
| `cash_to_debt_pct` | Cash / Total Debt × 100 | Short-term liquidity buffer |
| `operating_cash_flow_to_net_income` | Operating Cash Flow / Net Income | Earnings quality (cash conversion) |
| `risk_keyword_count` | Count of risk-related terms in source documents | Document-level risk signal |

All KPIs use `NULLIF` in SQL to prevent division-by-zero errors. `revenue_growth_pct` is NULL for the first period (no prior period exists).

---

## Validation Summary

The pipeline runs 16 automated data quality checks against the mart table:

| Category | Checks |
|----------|--------|
| Shape | Row count = 6, Column count = 22 |
| Completeness | No nulls in raw metric columns |
| Uniqueness | No duplicate company-period combinations |
| Coverage | All 3 companies present, all 2 periods present |
| Grain | One row per company-period |
| Financial coherence | gross_profit < revenue, operating_profit < gross_profit, net_income < operating_profit |
| Balance sheet coherence | cash < total_assets, total_debt < total_assets |
| KPI logic | FY2024 growth is NULL, FY2025 growth is populated |
| Synthetic marker | risk_keyword_count = 0 |
| KPI range | All percentage KPIs within 0–100 |

Current status: **16/16 checks passed.**

Full results: [reports/validation_report.md](reports/validation_report.md)

---

## Executive Summary Output

The auto-generated executive summary covers:

- Fastest-growing company by revenue
- Most profitable company by net margin
- Largest company by revenue
- Lowest leverage (debt/assets)
- Per-company KPI tables
- Growth and profitability trend analysis
- Balance sheet and leverage comparison
- Cash coverage analysis
- Limitations and recommended next questions

Full report: [reports/executive_summary.md](reports/executive_summary.md)

---

## Companies in the MVP

| Company | Sector | Country | Note |
|---------|--------|---------|------|
| Aurora Manufacturing | Industrials | Turkey | Fictional — synthetic data |
| Nova Retail Group | Consumer Discretionary | Turkey | Fictional — synthetic data |
| Atlas Energy Systems | Energy | Turkey | Fictional — synthetic data |

---

## Limitations

1. **Synthetic data only.** All financial figures are generated, not extracted from real documents. They are internally consistent but not real.
2. **Two periods only.** Revenue growth can only be calculated for FY2025 vs FY2024. Trend analysis is limited.
3. **No real document ingestion yet.** PDF/Excel extraction, AI-assisted parsing, and confidence scoring are scoped for Phase 2.
4. **SQLite only.** Suitable for local development. A production deployment would use PostgreSQL.
5. **No dashboard connected.** The mart CSV is dashboard-ready but no BI tool is connected in the MVP.
6. **Currency is TRY.** All figures are in Turkish Lira. No FX conversion is applied.
7. **Risk keyword count is 0.** The risk analysis module requires real document text. It is a placeholder in the MVP.

---

## Future Improvements

### Phase 2 — Real Document Ingestion
- PDF-to-Markdown conversion using `pymupdf` or `pdfplumber`
- Structured metric extraction using Claude API or regex patterns
- Confidence scoring and manual review queue for low-confidence extractions
- Support for Excel and CSV financial workbooks

### Phase 3 — Metabase Transforms Experiment
Evaluate whether Metabase Transforms can reproduce the SQL mart layer currently built in `sql/03_financial_kpis.sql` and `sql/05_mart_company_financial_performance.sql`.  
See [docs/25_METABASE_TRANSFORMS_EXPERIMENT.md](docs/25_METABASE_TRANSFORMS_EXPERIMENT.md) for the full experiment plan.

### Phase 4 — Expanded Coverage
- More companies and periods
- Quarterly reporting periods
- Multi-currency support with FX conversion
- Peer comparison benchmarks
- Automated anomaly detection

### Phase 5 — Production Deployment
- PostgreSQL backend
- dbt for SQL transformation management
- Airflow or Prefect for pipeline orchestration
- API layer for programmatic access
- Automated alert system for validation failures

---

## Portfolio Message

This project demonstrates:

- Clean, layered data pipeline architecture (extract → load → transform → validate → report)
- SQL-based KPI modeling with CTEs and window functions
- Data contract enforcement and automated validation
- Metric traceability from source CSV to executive summary
- Professional documentation standards
- Reproducible, single-command execution

The pipeline produces outputs that are directly useful to a finance team: a validated mart table, a quality report, and a business narrative — without requiring any dashboard tool to be open.
