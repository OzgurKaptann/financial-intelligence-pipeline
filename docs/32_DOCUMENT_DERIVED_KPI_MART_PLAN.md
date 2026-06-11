# 32 — Document-Derived KPI Mart Plan

Phase 3.3 of the Financial Intelligence Pipeline.

---

## Purpose

Phase 3.2 loaded document-extracted financial metrics into PostgreSQL as long-format rows
in `analytics.document_extracted_financial_metric`. Each row represents one metric value
(e.g. `revenue = 1,000,000`) for one company-period extracted from one source document.

Phase 3.3 materializes those rows into a KPI-ready transform mart — pivoting the long
format into wide columns, calculating 7 financial ratios, and classifying each company-period
with a financial health flag. The result is ready to query in Metabase or compare directly
against the Phase 2.1 synthetic data mart.

---

## Why Document-Derived Metrics Need Their Own Mart First

The Phase 2.1 mart (`transforms.mart_company_financial_performance`) is built from the
synthetic star schema (`analytics.fact_financial_metric` joined to `dim_company`,
`dim_period`, `dim_metric`). Document-derived metrics are not yet mapped to those
integer dimension keys.

Creating a separate document mart first achieves three things:

1. **Traceability.** `source_file` is preserved through every layer so each KPI value
   can be traced back to the originating Markdown file and source document.
2. **Isolation.** Synthetic and real/extracted data remain in separate marts, preventing
   accidental mixing before key alignment is validated.
3. **Incrementalism.** The mart can be built, tested, and exposed in Metabase
   independently of any changes to the existing synthetic pipeline.

---

## Input Table

| Table | Schema | Grain | Produced by |
|-------|--------|-------|-------------|
| `analytics.document_extracted_financial_metric` | analytics | One row per source_file + company_name + period_label + metric_name | `src/load_extracted_metrics_postgres.py` (Phase 3.2) |

### Input columns used

| Column | Type | Purpose |
|--------|------|---------|
| `source_file` | TEXT | Document lineage key |
| `company_name` | TEXT | Company identifier (free text) |
| `period_label` | TEXT | Reporting period (e.g. `FY2025`) |
| `metric_name` | TEXT | One of 8 canonical metric names |
| `metric_value` | NUMERIC | Extracted numeric value |

---

## Transform Tables Created

### `transforms.document_financial_metric_pivot`

Wide-format pivot of the 8 core metrics.

| Column | Type | Description |
|--------|------|-------------|
| `source_file` | TEXT | Document lineage key |
| `company_name` | TEXT | Company name |
| `period_label` | TEXT | Reporting period |
| `revenue` | NUMERIC | Pivoted from `metric_name = 'revenue'` |
| `gross_profit` | NUMERIC | Pivoted from `metric_name = 'gross_profit'` |
| `operating_profit` | NUMERIC | Pivoted from `metric_name = 'operating_profit'` |
| `net_income` | NUMERIC | Pivoted from `metric_name = 'net_income'` |
| `total_assets` | NUMERIC | Pivoted from `metric_name = 'total_assets'` |
| `total_debt` | NUMERIC | Pivoted from `metric_name = 'total_debt'` |
| `cash` | NUMERIC | Pivoted from `metric_name = 'cash'` |
| `operating_cash_flow` | NUMERIC | Pivoted from `metric_name = 'operating_cash_flow'` |

**Grain:** One row per `source_file + company_name + period_label`.

---

### `transforms.mart_document_company_financial_performance`

KPI mart layered on top of the pivot. Adds calculated ratios and classification.

| Column | Type | Description |
|--------|------|-------------|
| `source_file` | TEXT | Document lineage key |
| `company_name` | TEXT | Company name |
| `period_label` | TEXT | Reporting period |
| `revenue` … `operating_cash_flow` | NUMERIC | Raw metrics (8 columns) |
| `gross_margin_pct` | NUMERIC | Gross profit as % of revenue |
| `operating_margin_pct` | NUMERIC | Operating profit as % of revenue |
| `net_margin_pct` | NUMERIC | Net income as % of revenue |
| `debt_to_assets_pct` | NUMERIC | Total debt as % of total assets |
| `cash_to_debt_pct` | NUMERIC | Cash as % of total debt |
| `operating_cash_flow_margin_pct` | NUMERIC | Operating cash flow as % of revenue |
| `cash_conversion_pct` | NUMERIC | Operating cash flow as % of net income |
| `financial_health_flag` | TEXT | Classification: `stable` / `negative_income` / `high_debt` / `low_cash_buffer` / NULL |
| `mart_created_at` | TIMESTAMPTZ | Materialization timestamp |

**Grain:** One row per `source_file + company_name + period_label`.

---

## KPI Formulas

All ratios are rounded to 2 decimal places. All divisions use `NULLIF(denominator, 0)` to
return NULL instead of a division-by-zero error when the denominator is zero.

| KPI | Formula | Business meaning |
|-----|---------|-----------------|
| `gross_margin_pct` | `gross_profit / revenue × 100` | Profitability after direct costs |
| `operating_margin_pct` | `operating_profit / revenue × 100` | Profitability after operating expenses |
| `net_margin_pct` | `net_income / revenue × 100` | Final bottom-line profitability |
| `debt_to_assets_pct` | `total_debt / total_assets × 100` | Leverage — debt relative to asset base |
| `cash_to_debt_pct` | `cash / total_debt × 100` | Liquidity — cash available per unit of debt |
| `operating_cash_flow_margin_pct` | `operating_cash_flow / revenue × 100` | Cash generation efficiency |
| `cash_conversion_pct` | `operating_cash_flow / net_income × 100` | How much net income converts to cash |

---

## Financial Health Flag Logic

Evaluated in priority order. The first matching condition is applied.

| Condition | Flag | Interpretation |
|-----------|------|----------------|
| `net_income < 0` | `negative_income` | Company is losing money |
| `debt_to_assets_pct > 50` | `high_debt` | More than half of assets are debt-financed |
| `cash_to_debt_pct < 20` | `low_cash_buffer` | Less than 20% cash coverage of debt |
| None of the above | `stable` | No major red flags detected |
| `net_income IS NULL AND debt_to_assets_pct IS NULL` | NULL | Insufficient data to classify |

---

## Validation Strategy

`src/materialize_document_kpi_mart.py` executes the mart SQL and then runs 14 checks,
printing PASS/FAIL for each:

| # | Check | Expected (sample) |
|---|-------|-------------------|
| 1 | `document_financial_metric_pivot` row count | 1 |
| 2 | `mart_document_company_financial_performance` row count | 1 |
| 3 | Distinct companies | 1 |
| 4 | Distinct periods | 1 |
| 5 | Null revenue rows | 0 |
| 6 | Null net_income rows | 0 |
| 7 | `gross_margin_pct` for Demo Manufacturing FY2025 | 30.00 |
| 8 | `operating_margin_pct` | 18.00 |
| 9 | `net_margin_pct` | 12.00 |
| 10 | `debt_to_assets_pct` | 32.00 |
| 11 | `cash_to_debt_pct` | 37.50 |
| 12 | `operating_cash_flow_margin_pct` | 15.00 |
| 13 | `cash_conversion_pct` | 125.00 |
| 14 | `financial_health_flag` | `stable` |

The same SQL checks are available as a standalone script:

```bash
psql -h localhost -p 5433 -U analytics_user -d financial_analytics \
  -f metabase/postgres/sql/09_verify_document_kpi_mart.sql
```

---

## How to Run

Ensure the Docker stack is running and Phase 3.2 has been loaded:

```bash
docker compose --env-file metabase/.env -f metabase/docker-compose.yml up -d
python src/load_extracted_metrics_postgres.py
```

Then materialize the KPI mart:

```bash
python src/materialize_document_kpi_mart.py
```

---

## Current Limitations

- **Sample data only.** The current dataset contains one document
  (`sample_financial_note.md`) for one company (`Demo Manufacturing`) in one period
  (`FY2025`). All extracted values are synthetic, not real financial figures.

- **Free-text company and period keys.** `company_name` and `period_label` are not
  yet aligned to `analytics.dim_company` or `analytics.dim_period` integer keys from
  the Phase 2 star schema. Direct JOIN with synthetic data requires a manual mapping step.

- **No multi-period trend analysis.** Revenue growth percentage requires at least two
  periods. The current mart has one period per company, so no growth KPI is calculated.
  This will be added when more documents covering multiple periods are processed.

- **No currency or unit normalisation.** Phase 3.1 does not extract currency or unit
  metadata, so all values are treated as absolute numbers. Currency context must be
  applied by the analyst from external knowledge.

---

## Next Steps

1. **Expose in Metabase.** Connect Metabase to `transforms.mart_document_company_financial_performance`
   and build a Document-Derived Financial Performance dashboard alongside the Phase 2 synthetic dashboard.

2. **Compare against synthetic mart.** Join this table with
   `transforms.mart_company_financial_performance` on normalised company/period keys to
   produce a side-by-side document vs. synthetic comparison report.

3. **Add more documents.** Process additional financial documents covering multiple companies
   and periods to enable revenue growth, period-over-period trend analysis, and
   cross-company KPI benchmarking.
