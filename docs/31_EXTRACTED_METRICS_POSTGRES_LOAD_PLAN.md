# 31 — Extracted Metrics PostgreSQL Load Plan

Phase 3.2 of the Financial Intelligence Pipeline.

---

## Purpose

Phase 3.1 extracts structured financial metrics from Markdown documents and writes
them to local CSV files. Phase 3.2 loads those CSV files into PostgreSQL, connecting
document-derived metrics to the analytics warehouse path.

After Phase 3.2, extracted metrics can be queried alongside synthetic data in
PostgreSQL and visualised in Metabase alongside Phase 2 dashboards.

---

## Input Files

| File | Produced by | Description |
|------|-------------|-------------|
| `data/extracted/extracted_financial_metrics.csv` | `src/extract_financial_metrics.py` | One row per extracted metric value |
| `data/extracted/extraction_manifest.csv` | `src/extract_financial_metrics.py` | One row per source document processed |

Both files are gitignored and must be regenerated locally by running Phase 3.1
before this loader is executed.

---

## PostgreSQL Target Tables

### `raw.extracted_financial_metrics`

Landing table that mirrors the CSV structure. One row per extracted metric value.
No transformations are applied — raw values are preserved exactly as extracted.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | Auto-generated row identifier |
| `source_file` | TEXT | Markdown filename — primary lineage key |
| `company_name` | TEXT | Extracted company name |
| `period_label` | TEXT | Extracted reporting period (e.g. FY2025) |
| `metric_name` | TEXT | Canonical metric name (e.g. `gross_profit`) |
| `metric_value` | NUMERIC | Parsed numeric value; NULL on extraction failure |
| `extraction_status` | TEXT | `success`, `failed`, `no_metrics`, or `error` |
| `error_message` | TEXT | Reason for non-success; NULL on success |
| `extracted_at` | TIMESTAMP | UTC timestamp from the extractor |
| `loaded_at` | TIMESTAMPTZ | Timestamp when row was inserted into PostgreSQL |

### `raw.extraction_manifest`

Document-level audit trail. One row per source file processed by the extractor.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | Auto-generated row identifier |
| `source_file` | TEXT | Markdown filename |
| `company_name` | TEXT | Extracted company name; NULL if not found |
| `period_label` | TEXT | Extracted period; NULL if not found |
| `metrics_extracted` | INTEGER | Number of metric rows written for this document |
| `missing_metrics` | TEXT | Pipe-separated list of metrics not found |
| `extraction_status` | TEXT | `success`, `failed`, `no_metrics`, or `error` |
| `error_message` | TEXT | Reason for non-success; NULL on success |
| `extracted_at` | TIMESTAMP | UTC timestamp from the extractor |
| `loaded_at` | TIMESTAMPTZ | Timestamp when row was inserted into PostgreSQL |

### `analytics.document_extracted_financial_metric`

Analytics-layer table. Populated from `raw.extracted_financial_metrics` by
promoting only rows where `extraction_status = 'success'` and `metric_value IS NOT NULL`.
This is the analytics warehouse entry point for document-derived data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | Auto-generated row identifier |
| `source_file` | TEXT | Originating Markdown filename — preserved for lineage |
| `company_name` | TEXT | Company name |
| `period_label` | TEXT | Reporting period |
| `metric_name` | TEXT | Canonical metric name |
| `metric_value` | NUMERIC | Validated numeric value |
| `loaded_at` | TIMESTAMPTZ | Timestamp when row entered the analytics layer |

---

## Data Lineage Strategy

Every row in `analytics.document_extracted_financial_metric` carries `source_file`,
which traces it back to the originating Markdown file in `data/processed_markdown/`.
That Markdown file was itself produced from a raw document in `data/raw_documents/`
by Phase 3 (`src/document_converter.py`).

The full lineage chain is:

```
data/raw_documents/<file>
  → data/processed_markdown/<file>.md          (Phase 3: document_converter.py)
    → data/extracted/extracted_financial_metrics.csv  (Phase 3.1: extract_financial_metrics.py)
      → raw.extracted_financial_metrics         (Phase 3.2: load_extracted_metrics_postgres.py)
        → analytics.document_extracted_financial_metric
```

Every metric value in the analytics layer can be traced to a specific line in a
specific Markdown file and, beyond that, to the original source document.

---

## Validation Checks

The loader script (`src/load_extracted_metrics_postgres.py`) runs seven validation
checks at the end of each load and prints PASS/FAIL for each:

| Check | Expected (sample dataset) |
|-------|--------------------------|
| `raw.extracted_financial_metrics` row count | 8 |
| `analytics.document_extracted_financial_metric` row count | 8 |
| Distinct companies in analytics table | 1 |
| Distinct periods in analytics table | 1 |
| Distinct metrics in analytics table | 8 |
| Failed extraction rows in raw table | 0 |
| Null `metric_value` rows in raw table | 0 |

The same checks are available as a standalone SQL script:

```bash
psql -h localhost -p 5433 -U analytics_user -d financial_analytics \
  -f metabase/postgres/sql/07_verify_extracted_metrics_load.sql
```

---

## How to Run

Ensure the Docker stack from Phase 2 is running:

```bash
docker compose --env-file metabase/.env -f metabase/docker-compose.yml up -d
```

Then run the loader:

```bash
python src/load_extracted_metrics_postgres.py
```

---

## Current Limitations

- **Sample data only.** The current test dataset contains one document
  (`sample_financial_note.md`) for one company (`Demo Manufacturing`) in one
  period (`FY2025`). All extracted values are synthetic sample data, not real
  financial figures.

- **No key alignment with synthetic data.** `analytics.document_extracted_financial_metric`
  uses free-text `company_name` and `period_label`. It is not yet joined to
  `analytics.dim_company` or `analytics.dim_period` from the Phase 2 star schema.
  A future phase will resolve this alignment.

- **No idempotency guard on re-extraction.** If Phase 3.1 is rerun and new rows
  are appended to the CSV, rerunning the loader will replace all Phase 3.2 table
  contents (tables are dropped and recreated). This is intentional for the MVP:
  Phase 3.1 should be rerun deliberately, not accidentally.

- **No currency or unit normalisation.** Currency and unit are not extracted from
  documents in Phase 3.1, so they are not stored in Phase 3.2 tables. The
  downstream analyst must apply currency context from external knowledge.

---

## Next Step

Compare document-derived metrics against the synthetic data model:

1. Add `company_name` and `period_label` alignment logic to map extracted values
   to `analytics.dim_company` and `analytics.dim_period` integer keys.
2. Join `analytics.document_extracted_financial_metric` with
   `analytics.fact_financial_metric` to produce a side-by-side comparison report.
3. Optionally load validated extracted metrics into the existing star schema fact
   tables so they appear in existing Metabase dashboards.
