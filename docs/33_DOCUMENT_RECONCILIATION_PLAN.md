# 33 — Document-Derived Metrics Reconciliation Plan

Phase 4 of the Financial Intelligence Pipeline.

---

## Purpose

Phase 3.3 produced a KPI mart of document-derived financial metrics
(`transforms.mart_document_company_financial_performance`). Phase 4 adds a
reconciliation layer that asks: how do those document-derived figures compare
to the existing synthetic benchmark mart?

Reconciliation answers four questions for every document company-period:

1. Does a matching company and period exist in the synthetic mart?
2. If it does, what are the differences in key KPI values?
3. How large are those differences in percentage terms?
4. What share of document records can be reconciled at all?

These questions matter before trusting document-derived data in a production
dashboard. Without reconciliation, there is no systematic way to detect
extraction errors, misaligned company names, or period label mismatches.

---

## Why Document-Derived Data Needs Comparison Against a Benchmark Mart

The synthetic mart was built from hand-authored, internally consistent data
and serves as the analytical ground truth for this project. When real documents
are processed, there is no guarantee that the extracted values match expectations:

- The extractor may misread a comma as a decimal separator.
- The document may report a different accounting basis or period definition.
- The company name in the document may differ from the name used in the
  analytics warehouse (e.g. "Demo Manufacturing Ltd" vs "Demo Manufacturing").
- The period label may use a different format ("FY 2025" vs "FY2025").

A reconciliation layer makes these discrepancies visible and measurable. It
does not block pipeline execution — it surfaces information.

---

## Current Limitation: Sample Document Company Does Not Match Synthetic Set

The current sample document contains data for **Demo Manufacturing** (FY2025).

The synthetic benchmark mart contains data for:
- Aurora Manufacturing
- Nova Retail Group
- Atlas Energy Systems

None of these names match "Demo Manufacturing", so the reconciliation join
produces zero matched records and one unmatched record. This is **expected and
correct behavior** — the reconciliation layer is not broken because there are
no matches. It is working exactly as designed.

---

## Why Unmatched Records Are Valuable

An `unmatched_company_or_period` record tells a data analyst:

- "I processed a document for Demo Manufacturing FY2025. It extracted 8 metrics
  and produced 7 KPI ratios. However, I cannot cross-check those values against
  a benchmark because this company is not in the synthetic reference set."

This is more informative than silently dropping the record or throwing an error.
It keeps the extracted data visible and flags the gap explicitly. When the
pipeline is extended with real matched documents, unmatched records become the
exception rather than the rule — and they remain auditable.

---

## Tables Created

### `transforms.document_metric_reconciliation`

Grain: one row per `source_file + document_company_name + document_period_label`.

| Column | Description |
|--------|-------------|
| `source_file` | Originating Markdown filename — primary document lineage key |
| `document_company_name` | Company name as it appears in the document |
| `document_period_label` | Period label as it appears in the document |
| `match_status` | `matched` or `unmatched_company_or_period` |
| `doc_revenue` | Revenue from the document mart |
| `doc_gross_margin_pct` | Gross margin % from the document mart |
| `doc_operating_margin_pct` | Operating margin % from the document mart |
| `doc_net_margin_pct` | Net margin % from the document mart |
| `doc_debt_to_assets_pct` | Debt/assets % from the document mart |
| `doc_cash_to_debt_pct` | Cash/debt % from the document mart |
| `syn_revenue` | Revenue from the synthetic mart (NULL if unmatched) |
| `syn_gross_margin_pct` | Gross margin % from synthetic mart (NULL if unmatched) |
| `syn_operating_margin_pct` | Operating margin % from synthetic mart (NULL if unmatched) |
| `syn_net_margin_pct` | Net margin % from synthetic mart (NULL if unmatched) |
| `syn_debt_to_assets_pct` | Debt/assets % from synthetic mart (NULL if unmatched) |
| `syn_cash_to_debt_pct` | Cash/debt % from synthetic mart (NULL if unmatched) |
| `revenue_difference` | `doc_revenue − syn_revenue` (NULL if unmatched) |
| `gross_margin_difference` | `doc − syn` difference (NULL if unmatched) |
| `operating_margin_difference` | `doc − syn` difference (NULL if unmatched) |
| `net_margin_difference` | `doc − syn` difference (NULL if unmatched) |
| `debt_to_assets_difference` | `doc − syn` difference (NULL if unmatched) |
| `cash_to_debt_difference` | `doc − syn` difference (NULL if unmatched) |
| `revenue_pct_difference` | `(doc − syn) / syn × 100` (NULL if unmatched or syn = 0) |
| `reconciliation_created_at` | Timestamp when this row was materialized |

### `transforms.document_kpi_reconciliation_summary`

Grain: one row (aggregate over all reconciliation records).

| Column | Description |
|--------|-------------|
| `total_document_records` | Total rows in `document_metric_reconciliation` |
| `matched_records` | Rows where `match_status = 'matched'` |
| `unmatched_records` | Rows where `match_status = 'unmatched_company_or_period'` |
| `match_rate_pct` | `matched / total × 100`; `0.00` when total = 0 |
| `avg_abs_revenue_difference` | Average `ABS(revenue_difference)` for matched rows; NULL when no matches |
| `avg_abs_net_margin_difference` | Average `ABS(net_margin_difference)` for matched rows; NULL when no matches |
| `summary_created_at` | Timestamp when this row was materialized |

---

## Matching Strategy

The join is a `LEFT JOIN` from the document mart to the synthetic mart on:

```sql
LOWER(TRIM(doc.company_name)) = LOWER(TRIM(syn.company_name))
AND LOWER(TRIM(doc.period_label)) = LOWER(TRIM(syn.fiscal_period))
```

Case normalisation (`LOWER`) and whitespace trimming (`TRIM`) make the match
robust to minor formatting differences between document-extracted names and
warehouse dimension values. The `LEFT JOIN` ensures all document records are
preserved regardless of whether a synthetic match is found.

---

## Difference Metrics

All difference fields are calculated as `document value − synthetic value`:

- A **positive** difference means the document figure is higher than synthetic.
- A **negative** difference means the document figure is lower than synthetic.
- A **NULL** difference means the record is unmatched — no comparison is possible.

`revenue_pct_difference` uses `NULLIF(syn_revenue, 0)` to prevent
division-by-zero. This returns NULL rather than an error when the synthetic
revenue is zero.

---

## Validation Strategy

Six checks are run after materialization:

| Check | Expected (current sample) | Rationale |
|-------|--------------------------|-----------|
| `document_metric_reconciliation` row count | 1 | One document processed |
| `document_kpi_reconciliation_summary` row count | 1 | Always a single summary row |
| `matched_records` | 0 | Demo Manufacturing is not in the synthetic set |
| `unmatched_records` | 1 | One unmatched record is expected |
| `match_rate_pct` | 0.00 | Zero matches → zero match rate |
| Demo Manufacturing match_status | `unmatched_company_or_period` | Expected for this sample |

None of these checks fail because there are no matches. Zero matches is the
correct and expected result for the current dataset — not an error condition.

---

## Next Steps

### Option A: Create a matched sample document

Write a new sample document for one of the synthetic companies (e.g. "Aurora
Manufacturing") with period "FY2025" and values that match or deliberately differ
from the synthetic mart. Running the full pipeline will then produce a
`matched` record and populate the difference fields with real values.

### Option B: Add a company alias mapping table

Create `analytics.company_alias_map` with columns `(alias_name, canonical_name)`
and update the reconciliation join to resolve aliases before matching. This
allows "Demo Manufacturing Ltd" → "Demo Manufacturing" without modifying source
documents or dimension tables.

### Option C: Expose reconciliation tables in Metabase

Add the reconciliation tables as data sources in Metabase and build a
reconciliation card that shows match rate, unmatched companies, and KPI
differences — turning the reconciliation layer into a live data quality
dashboard.

---

## Source Tables

| Table | Phase | Role |
|-------|-------|------|
| `transforms.mart_document_company_financial_performance` | Phase 3.3 | Left side of reconciliation join |
| `transforms.mart_company_financial_performance` | Phase 2.1 | Right side (synthetic benchmark) |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `metabase/postgres/sql/10_create_document_reconciliation.sql` | Creates both Phase 4 reconciliation tables |
| `metabase/postgres/sql/11_verify_document_reconciliation.sql` | 6 SQL validation checks |
| `src/materialize_document_reconciliation.py` | Python runner: executes SQL, runs PASS/FAIL validation |
