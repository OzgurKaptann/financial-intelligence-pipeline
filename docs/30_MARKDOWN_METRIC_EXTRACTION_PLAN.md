# 30 — Markdown Metric Extraction Plan

Phase 3.1 of the Financial Intelligence Pipeline.

---

## Purpose

Phase 3 (MarkItDown) converts raw financial documents into Markdown text files.
Phase 3.1 reads those Markdown files and extracts structured financial metric rows
from them using deterministic regex-based rules — no LLM, no external API.

The extracted rows are written to `data/extracted/extracted_financial_metrics.csv`
in a long format compatible with the existing synthetic metrics data contract.

---

## How Markdown Input Is Produced

1. Place raw financial documents in `data/raw_documents/`.
2. Run `python src/document_converter.py` (Phase 3).
3. MarkItDown converts each file to a `.md` file in `data/processed_markdown/`.
4. Run `python src/extract_financial_metrics.py` (Phase 3.1) to extract metrics.

The extractor reads only from `data/processed_markdown/`. It never touches the
original source documents.

---

## What Fields Are Extracted

### Required context fields (must be present or the file is marked `failed`)

| Field | Example value | Pattern |
|-------|--------------|---------|
| `company_name` | `Demo Manufacturing` | `Company: <name>` or `Company Name: <name>` |
| `period_label` | `FY2025` | `Period: <label>` or `Reporting Period: <label>` |

### Financial metrics (eight canonical metrics)

| Canonical name | Accepted label aliases (case-insensitive) |
|----------------|------------------------------------------|
| `revenue` | revenue, total revenue, net revenue, net sales, sales, turnover, total sales |
| `gross_profit` | gross profit, gross income, gross margin value |
| `operating_profit` | operating profit, operating income, ebit, operating earnings, income from operations, profit from operations |
| `net_income` | net income, net profit, net earnings, profit after tax, net profit after tax, earnings after tax, bottom line |
| `total_assets` | total assets, assets total, total asset |
| `total_debt` | total debt, total borrowings, total liabilities, financial debt, interest bearing debt, net debt, borrowings, long-term debt, total financial debt |
| `cash` | cash, cash and cash equivalents, cash & cash equivalents, cash equivalents, cash and equivalents, liquid assets |
| `operating_cash_flow` | operating cash flow, cash flow from operations, cash flow from operating activities, net cash from operations, net cash from operating activities, operating activities |

---

## Supported Numeric Patterns

The value parser handles:

| Format | Example | Parsed as |
|--------|---------|-----------|
| Plain integer | `1000000` | `1000000.0` |
| Comma-separated thousands | `1,000,000` | `1000000.0` |
| Space-separated thousands | `1 000 000` | `1000000.0` |
| Decimal | `1500000.50` | `1500000.5` |
| European format | `1.000.000,50` | `1000000.5` |
| Currency symbol prefix | `₺1,500,000` | `1500000.0` |
| Parenthesised negative | `(500000)` | `500000.0`* |

\* Parenthesised values are parsed as positive. If a document uses parentheses
to signal a loss, the downstream analyst should interpret sign from context.
K/M/B suffixes are matched but not currently scaled (e.g. `1.5M` parses as `1.5`).
This is intentional — raw document values should be explicitly stated in full.

---

## Output Files

### `data/extracted/extracted_financial_metrics.csv`

Long-format table — one row per successfully extracted metric value.

| Column | Description |
|--------|-------------|
| `source_file` | Markdown filename the metric was extracted from |
| `company_name` | Extracted company name |
| `period_label` | Extracted reporting period |
| `metric_name` | Canonical metric name (e.g. `gross_profit`) |
| `metric_value` | Parsed numeric value |
| `extraction_status` | `success` |
| `error_message` | Empty on success |
| `extracted_at` | UTC timestamp |

### `data/extracted/extraction_manifest.csv`

One row per Markdown file processed.

| Column | Description |
|--------|-------------|
| `source_file` | Markdown filename |
| `company_name` | Extracted company name (empty if not found) |
| `period_label` | Extracted period (empty if not found) |
| `metrics_found` | Pipe-separated list of successfully extracted metrics |
| `metrics_missing` | Pipe-separated list of metrics not found in the file |
| `total_rows_written` | Number of rows written to the metrics CSV for this file |
| `extraction_status` | `success`, `failed`, `no_metrics`, or `error` |
| `error_message` | Reason for non-success status |
| `extracted_at` | UTC timestamp |

---

## Extraction Status Values

| Status | Meaning |
|--------|---------|
| `success` | Company, period, and at least one metric extracted |
| `failed` | Company or period could not be found; no rows written |
| `no_metrics` | Company and period found but no metric values matched any alias |
| `error` | File could not be read (I/O error) |

---

## Why Deterministic Before LLM

1. **Reproducibility.** The same document always produces the same output.
   No API keys, rate limits, costs, or response variability.

2. **Auditability.** Every extracted value can be traced to a specific regex match
   in the source text. A reviewer can verify any number by reading the document.

3. **Baseline first.** A regex baseline establishes which documents are well-structured
   (high regex coverage) vs. which need LLM assistance. This prevents over-engineering
   before the problem is understood.

4. **Privacy by default.** No document content leaves the machine.

---

## Current Limitations

- **Structured text only.** The extractor relies on labelled key-value pairs
  (`Revenue: 1,000,000`). Financial statements buried in narrative prose, tables
  without clear labels, or scanned images will not extract well.
- **K/M/B suffixes not scaled.** `1.5M` parses as `1.5`, not `1500000`. Documents
  should use full numeric values for reliable extraction.
- **First match only.** If the same metric label appears multiple times in a document
  (e.g. a comparison table), only the first occurrence is extracted.
- **No currency inference.** Currency is not extracted from the document; downstream
  code should enforce a consistent currency assumption.
- **No confidence score.** All successful extractions are treated equally. A future
  phase can add a confidence score based on alias specificity and numeric format quality.

---

## Phase 3.2: Load Extracted Metrics into PostgreSQL

Phase 3.2 loads `data/extracted/extracted_financial_metrics.csv` directly into PostgreSQL,
connecting document-derived metrics to the analytics warehouse path.

Three tables are created and populated:

| Table | Layer | Purpose |
|-------|-------|---------|
| `raw.extracted_financial_metrics` | raw | Landing table — mirrors CSV, one row per extracted metric |
| `raw.extraction_manifest` | raw | Document-level audit trail, one row per source file |
| `analytics.document_extracted_financial_metric` | analytics | Clean analytics view, success rows only |

Run with:

```bash
python src/load_extracted_metrics_postgres.py
```

See `docs/31_EXTRACTED_METRICS_POSTGRES_LOAD_PLAN.md` for full details.

---

## Next Phase: Integrate with Analytics Star Schema

A future phase will:

1. Validate rows against the data contract in `docs/05_DATA_CONTRACTS.md`.
2. Align company and period keys between document-derived and synthetic data.
3. Produce a side-by-side comparison between extracted and synthetic figures.
4. Load validated extracted metrics into the existing star schema fact tables.
