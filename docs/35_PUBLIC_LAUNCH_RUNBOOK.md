# Public Launch Runbook

## Purpose

This runbook helps anyone understand the project structure and run the full financial intelligence pipeline locally — from raw documents and synthetic data through to a validated Metabase-ready PostgreSQL warehouse.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | Install packages via `pip install -r requirements.txt` |
| Docker Desktop | Must be running before any PostgreSQL or Metabase steps |
| `metabase/.env` | Copy `metabase/.env.example` to `metabase/.env` and fill in credentials |
| PostgreSQL + Metabase | Provided via Docker Compose — no separate installation needed |

---

## Full Pipeline Run Order

### Step 1 — Start Docker services

```powershell
docker compose --env-file metabase/.env -f metabase/docker-compose.yml up -d
```

Starts three containers: Metabase OSS, PostgreSQL analytics DB, and the Metabase app DB.
Wait ~30 seconds for Metabase to initialise before connecting.

---

### Step 2 — Run the SQLite MVP pipeline

```powershell
python src/run_pipeline.py
```

Generates synthetic financial data, loads it into SQLite, exports the mart CSV, runs 16 validation checks, and generates the executive summary report. All five stages run in sequence.

---

### Step 3 — Convert raw financial documents to Markdown

```powershell
python src/document_converter.py
```

Converts all files in `data/raw_documents/` to Markdown using Microsoft MarkItDown. Produces a `conversion_manifest.csv`. Place `.pdf`, `.docx`, `.xlsx`, or `.pptx` files in `data/raw_documents/` before running.

---

### Step 4 — Extract structured metrics from Markdown

```powershell
python src/extract_financial_metrics.py
```

Reads `.md` files from `data/processed_markdown/` and extracts 8 core financial metrics using deterministic regex matching. Produces `extracted_financial_metrics.csv` and `extraction_manifest.csv` in `data/extracted/`.

---

### Step 5 — Load extracted metrics into PostgreSQL

```powershell
python src/load_extracted_metrics_postgres.py
```

Loads the extracted CSV into PostgreSQL `raw` and `analytics` schemas. Idempotent — safe to re-run. Requires Docker services to be running and `metabase/.env` to be present.

---

### Step 6 — Materialize the document-derived KPI mart

```powershell
python src/materialize_document_kpi_mart.py
```

Pivots the analytics table into a wide KPI mart under `transforms.mart_document_company_financial_performance`. Runs 14 PASS/FAIL SQL validation checks on completion.

---

### Step 7 — Materialize the reconciliation layer

```powershell
python src/materialize_document_reconciliation.py
```

Reconciles the document-derived KPI mart against the synthetic benchmark mart. Produces `transforms.document_metric_reconciliation` and `transforms.document_kpi_reconciliation_summary`. Runs 6 PASS/FAIL SQL validation checks on completion.

---

### Step 8 — Open Metabase

Navigate to [http://localhost:3000](http://localhost:3000).

Connect to the PostgreSQL analytics database using the credentials in `metabase/.env`. The `transforms` schema tables are ready to query and visualise.

---

## Expected Outputs

### File outputs

| Path | Description |
|---|---|
| `data/final/financial_intelligence.sqlite` | Normalized SQLite database (6 tables) |
| `data/final/mart_company_financial_performance.csv` | Dashboard-ready synthetic benchmark mart (6 rows) |
| `reports/validation_report.md` | 16-check SQLite validation report |
| `reports/executive_summary.md` | Auto-generated business narrative |
| `data/extracted/extracted_financial_metrics.csv` | Long-format document-derived metrics |
| `data/extracted/extraction_manifest.csv` | Per-file extraction status |

### PostgreSQL tables

| Table | Description | Expected rows (sample) |
|---|---|---|
| `transforms.mart_company_financial_performance` | Synthetic benchmark KPI mart | 6 |
| `transforms.mart_document_company_financial_performance` | Document-derived KPI mart | 1 |
| `transforms.document_metric_reconciliation` | Row-level reconciliation | 1 |
| `transforms.document_kpi_reconciliation_summary` | Aggregate reconciliation summary | 1 |

---

## Validation Expectations

| Check | Expected result |
|---|---|
| SQLite MVP validation | 16/16 PASS |
| Extracted metrics row count | 8 rows (one per core metric for the sample document) |
| Document KPI mart row count | 1 row (Demo Manufacturing, FY2025) |
| Reconciliation row count | 1 row |
| Reconciliation match status | `unmatched_company_or_period` |
| Match rate | 0.00% |

**The unmatched status for `Demo Manufacturing` is expected and correct.** The sample document company does not exist in the synthetic benchmark set (`Aurora Manufacturing`, `Nova Retail Group`, `Atlas Energy Systems`). This proves the reconciliation layer safely handles company-period mismatches without failing or producing NULL errors.

---

## Troubleshooting

| Symptom | Resolution |
|---|---|
| `ffmpeg` or `pydub` warning on startup | Not critical for text-based financial documents. MarkItDown uses these for audio files only — ignore for this workflow. |
| PostgreSQL connection refused | Docker must be running and containers must be healthy before running any loader script. Run `docker ps` to check container status. |
| `metabase/.env not found` | Copy `metabase/.env.example` to `metabase/.env` and fill in your credentials. The `.env` file is gitignored and must be created locally. |
| Generated data files missing | `data/final/`, `data/extracted/`, and `data/processed_markdown/` are gitignored. Only `.gitkeep` files are committed. Regenerate by running the pipeline. |
| Metabase shows no data | Ensure `load_extracted_metrics_postgres.py` and `materialize_document_kpi_mart.py` have been run successfully after Docker startup. |
| Row count is 0 after extraction | Verify that `.md` files exist in `data/processed_markdown/` and that the company name and period label are present in the document text. |
