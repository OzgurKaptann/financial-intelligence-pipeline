# 25 — Metabase Transforms Experiment Plan

**Status:** Planned — Phase 3  
**Author:** Analytics Engineering  
**Date:** 2026-06-09  
**Scope:** Evaluation and design only. No implementation in MVP.

---

## 1. What This Document Covers

This document outlines a future Phase 3 experiment to evaluate whether Metabase Transforms can reproduce the SQL mart layer currently built in:

- `sql/03_financial_kpis.sql`
- `sql/05_mart_company_financial_performance.sql`

The goal is not to replace the existing pipeline but to assess whether Metabase Transforms is a viable lighter-weight alternative to dbt for this project's SQL modeling layer.

---

## 2. Why Metabase Transforms Is Relevant

The current pipeline maintains SQL models as standalone `.sql` files executed directly via Python (`sqlite3`). This works well for the MVP but has limitations as the project grows:

- No lineage tracking between SQL models
- No automated documentation of model dependencies
- No incremental refresh support
- Changes to mart logic require manual re-execution of the full pipeline

Metabase Transforms allows analysts to define SQL models inside Metabase itself, schedule refreshes, and expose results directly to dashboards without building a separate dbt project or orchestration layer.

For a small analytics project with a single analyst, this could replace the SQL modeling layer with significantly less operational overhead than dbt.

---

## 3. What Part of the Current Pipeline Could Move Into Metabase

The following SQL objects are candidates for replication inside Metabase Transforms:

| Current File | SQL Object | Metabase Candidate |
|---|---|---|
| `sql/03_financial_kpis.sql` | KPI calculation query | Metabase Transform model |
| `sql/05_mart_company_financial_performance.sql` | Dashboard mart view | Metabase Transform model |

The following would **not** move into Metabase:

| Layer | Stays Where |
|---|---|
| Synthetic data generation | Python (`src/synthetic_data_generator.py`) |
| Database schema creation | Python + SQL (`src/database_loader.py`, `sql/01_schema.sql`) |
| Raw data loading | Python (`src/database_loader.py`) |
| Validation checks | Python (`src/validation.py`) |
| Executive summary generation | Python (`src/report_generator.py`) |

The experiment is specifically about the **SQL transformation layer**, not the extraction, loading, or reporting layers.

---

## 4. Proposed Metabase Transform Flow

```
fact_financial_metric  (SQLite / PostgreSQL)
        │
        ▼
[Metabase Transform 1: metric_pivot]
  Pivots long-format metrics to wide format
  (Replicates the metric_pivot CTE from sql/03_financial_kpis.sql)
        │
        ▼
[Metabase Transform 2: kpi_base]
  Joins pivoted metrics with dim_company and dim_period
  Calculates gross_margin_pct, operating_margin_pct,
  net_margin_pct, debt_to_assets_pct, cash_to_debt_pct
        │
        ▼
[Metabase Transform 3: mart_company_financial_performance]
  Adds revenue_growth_pct via LAG() window function
  Produces the final 22-column mart table
  (Replicates sql/05_mart_company_financial_performance.sql)
        │
        ▼
Metabase Dashboard
  (Revenue, margins, leverage, cash coverage by company and period)
```

Each Metabase Transform corresponds to one CTE or view in the current SQL layer.

---

## 5. Metabase vs dbt-Light Evaluation Criteria

| Criterion | Metabase Transforms | dbt (Core) |
|---|---|---|
| Setup complexity | Low — runs inside Metabase UI | Medium — requires dbt project structure |
| SQL authoring | In-browser SQL editor | Local `.sql` files with Jinja templating |
| Model dependencies | Manual ordering in UI | Defined via `ref()` function, auto-resolved |
| Lineage documentation | Basic (Metabase shows upstream tables) | Full DAG with `dbt docs generate` |
| Incremental refresh | Scheduled in Metabase | `dbt run --select model+ --incremental` |
| Testing / assertions | No built-in data tests | `dbt test` with schema.yml assertions |
| Version control | Not natively (SQL lives in Metabase DB) | Full Git history for all `.sql` files |
| Dashboard integration | Native — transforms feed directly to charts | Separate step (connect BI tool to dbt output) |
| Cost | Included in Metabase license | Free (dbt Core), paid (dbt Cloud) |
| Best for | Small teams, rapid iteration, BI-first workflow | Larger teams, production pipelines, audit trails |

**Preliminary assessment:** Metabase Transforms is appropriate for this project's scale. The tradeoff is losing Git-based SQL versioning and `dbt test`-style assertions in exchange for a simpler, integrated workflow. This tradeoff is acceptable for a portfolio project and small analytics teams.

---

## 6. What Will NOT Be Tested

The following are explicitly out of scope for this experiment:

- Replacing Python-based validation (`src/validation.py`) with Metabase data alerts
- Replacing the executive summary generator (`src/report_generator.py`) with Metabase text cards
- Migrating the SQLite database to PostgreSQL (separate Phase 4 concern)
- Building a full dbt project as an alternative (documented in backlog as a separate option)
- Production scheduling or CI/CD integration

---

## 7. Success Criteria

The experiment is considered successful if:

1. Both SQL models (`03_financial_kpis.sql` and `05_mart_company_financial_performance.sql`) are reproduced inside Metabase Transforms without modifying the underlying source tables.
2. The Metabase mart produces identical row counts and column values as the current Python-exported CSV (`data/final/mart_company_financial_performance.csv`).
3. At least one dashboard question (e.g., Revenue by Company and Period) can be built directly on top of the Metabase Transform model.
4. The experiment can be documented in under one day of setup time.

---

## 8. Risks and Limitations

| Risk | Severity | Mitigation |
|---|---|---|
| Metabase Transforms may not support SQLite as a data source | High | Migrate to PostgreSQL before running experiment |
| LAG() window function support in Metabase Transforms is not guaranteed | Medium | Test with a simplified revenue growth model first |
| SQL models maintained inside Metabase UI are not version-controlled | Medium | Export and commit SQL as reference files after authoring |
| Metabase license cost may not be justified for a portfolio project | Low | Use Metabase Open Source (self-hosted, free) |
| If the experiment fails, the existing Python + raw SQL approach is already working | — | No risk to the current pipeline — this is additive |

---

## 9. Future Implementation Steps

When ready to run this experiment:

1. **Prerequisite:** Migrate SQLite database to PostgreSQL (Metabase Transforms requires a supported database; SQLite support is limited).
2. **Install Metabase** (Open Source, self-hosted via Docker or `.jar`).
3. **Connect Metabase** to the PostgreSQL database containing `dim_company`, `dim_period`, `dim_metric`, `fact_financial_metric`.
4. **Create Transform 1:** `metric_pivot` — replicate the pivot CTE.
5. **Create Transform 2:** `kpi_base` — join and calculate margin KPIs.
6. **Create Transform 3:** `mart_company_financial_performance` — add revenue growth via window function.
7. **Validate:** Compare Metabase mart output against `mart_company_financial_performance.csv` row by row.
8. **Build one dashboard question** to confirm the mart is dashboard-accessible.
9. **Document results** in a follow-up decision log entry (`docs/19_DECISION_LOG.md`).

---

## References

- [Metabase Transforms documentation](https://www.metabase.com/docs/latest/data-modeling/transforms)
- Current SQL layer: `sql/03_financial_kpis.sql`, `sql/05_mart_company_financial_performance.sql`
- Architecture overview: `docs/03_ARCHITECTURE.md`
- Decision log: `docs/19_DECISION_LOG.md`
- Backlog: `docs/18_BACKLOG.md`
