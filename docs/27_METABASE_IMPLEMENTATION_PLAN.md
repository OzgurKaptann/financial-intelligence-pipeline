# 27 — Metabase Transforms Implementation Plan

**Phase:** 2  
**Branch:** phase-2-metabase-transforms  
**Status:** Planning / Experiment Design — Updated  
**Date:** 2026-06-10  

---

> **IMPORTANT CORRECTION (updated from initial plan)**
>
> The original plan assumed Metabase Transforms could be run against SQLite.
> This is incorrect. Metabase can browse and query SQLite as a data source,
> but the **Transforms feature requires a supported database backend**.
> SQLite is not a supported Transforms target.
>
> **The Phase 2 Transforms experiment uses PostgreSQL, not SQLite.**
> SQLite remains the MVP database and is not modified.
> PostgreSQL is run via Docker alongside Metabase OSS.
> See `docs/28_DOCKER_POSTGRES_METABASE_PLAN.md` for the Docker setup plan.

> **WARNING: Do not attempt to create Metabase Transforms directly on SQLite.**

---

## 1. Why Metabase Transforms Is Relevant to This Project

The MVP pipeline currently runs SQL transformations as external files executed
by Python scripts against a local SQLite database. This works well for
reproducibility and version control, but it separates the transformation logic
from the business intelligence layer.

Metabase Transforms (also called Metabase Models) allow SQL transformation
logic to live inside Metabase itself. Each transform is a saved SQL model that
can be referenced by other models or by dashboard questions — similar to how dbt
models work, but inside the BI tool rather than a separate CLI pipeline.

For this project, Metabase Transforms are relevant because:

- The mart SQL layer is already dashboard-ready SQL with well-defined grain,
  column names, and KPI formulas.
- Moving the mart layer into Metabase would allow analysts to modify KPI
  definitions inside the BI tool without touching the Python pipeline.
- It is a common real-world pattern: dbt-like modelling inside a BI tool.
- Evaluating this pattern against PostgreSQL demonstrates understanding of
  production-grade analytics engineering, not just local SQLite scripting.

---

## 2. Which Part of the Existing Pipeline Could Move Into Metabase

The pipeline has three logical layers. The MVP SQLite pipeline is unchanged.

| Layer | Current location | Can move to Metabase? | Notes |
|---|---|---|---|
| Data generation | `src/01_generate_synthetic_data.py` | No | Python only |
| Schema setup | `sql/01_schema.sql` | No | DDL, not a transform |
| Data loading | `src/02_load_to_database.py` | No | Python only |
| KPI SQL model | `sql/03_financial_kpis.sql` | **Yes (PostgreSQL)** | Requires PG backend |
| Mart view | `sql/05_mart_company_financial_performance.sql` | **Yes (PostgreSQL)** | Requires PG backend |
| CSV export | `src/04_export_mart_csv.py` | Partially | Metabase can export CSV from a model |
| Validation report | `src/05_generate_validation_report.py` | No | Python report logic |
| Executive summary | `src/06_generate_executive_summary.py` | No | Python narrative logic |

The candidate portion for Metabase Transforms is the **mart SQL layer**:
the metric pivot, KPI calculations, and dashboard mart view.

The data ingestion, validation, and reporting layers remain Python-based.

---

## 3. Database Architecture for This Experiment

SQLite and PostgreSQL serve **separate, non-overlapping roles** in Phase 2.

```
SQLite (data/financial_intelligence.db)
  → MVP pipeline source of truth
  → Used by src/ Python scripts
  → Can be browsed in Metabase (read-only native queries)
  → NOT used for Metabase Transforms
  → NOT modified by Phase 2

PostgreSQL (Docker container: financial_analytics)
  → Receives a copy of the synthetic data loaded from existing CSV exports
  → Supports Metabase Transforms
  → Used for all three transform experiments
  → NOT the MVP source of truth
```

Data loaded into PostgreSQL comes from the existing synthetic CSV files that
the MVP pipeline already produces. No Python pipeline scripts are modified.

---

## 4. How the Current SQL Model Maps Into Metabase Transforms

The MVP mart SQL is structured as four CTEs plus a final SELECT:

```
metric_pivot        → pivot long metric rows to wide company-period rows
risk_counts         → aggregate risk keyword counts
kpi_base            → join dimensions and risk counts
with_prior_revenue  → add LAG() for revenue growth
final SELECT        → calculate all 8 KPIs
```

This maps into three Metabase Transforms running against PostgreSQL:

```
Transform 01: Financial Metric Pivot
  → Target database: PostgreSQL (financial_analytics)
  → Sources: fact_financial_metric, dim_metric (PostgreSQL tables)
  → Logic: metric_pivot CTE
  → Output: wide table, 6 rows, 10 columns

Transform 02: Financial KPI Model
  → Target database: PostgreSQL (financial_analytics)
  → Sources: Transform 01 + dim_company + dim_period + fact_risk_keyword
  → Logic: risk_counts + kpi_base + with_prior_revenue + KPI SELECT
  → Output: 6 rows, 22 columns with all raw metrics and KPIs

Transform 03: Mart — Company Financial Performance
  → Target database: PostgreSQL (financial_analytics)
  → Sources: Transform 02 (or self-contained for validation)
  → Logic: dashboard mart pass-through
  → Output: dashboard-ready mart, 6 rows, 22 columns
```

Transform 03 is the Metabase equivalent of the MVP's
`mart_company_financial_performance` view and CSV export.

---

## 5. Proposed Transform Flow

```
Existing synthetic CSV exports
  (data/ or dashboard/mart_company_financial_performance.csv)
        │
        ▼ (manual load or Python loader script — Phase 2 setup only)
PostgreSQL tables (Docker: financial_analytics database)
├── fact_financial_metric  (48 rows)
├── dim_metric             (8 rows)
├── dim_company            (3 rows)
├── dim_period             (2 rows)
└── fact_risk_keyword      (0 rows in MVP)
        │
        ▼
Metabase OSS (Docker: localhost:3000)
Connected to PostgreSQL financial_analytics
        │
        ▼
Transform 01: Financial Metric Pivot
  Long → Wide pivot via conditional aggregation (PostgreSQL-compatible SQL)
  Output: 6 rows × 10 columns
        │
        ▼
Transform 02: Financial KPI Model
  Join dimensions, aggregate risk counts, apply LAG(), calculate KPIs
  (PostgreSQL LAG() window function — fully supported)
  Output: 6 rows × 22 columns
        │
        ▼
Transform 03: Mart — Company Financial Performance
  Dashboard-ready mart (same grain, clean column names, full annotations)
  Output: 6 rows × 22 columns
        │
        ▼
Metabase Questions & Dashboards
  Revenue trends, margin comparisons, leverage analysis, period-over-period

        │ VALIDATION
        ▼
Compare Transform 03 output vs. dashboard/mart_company_financial_performance.csv
(Python + SQLite mart output vs. PostgreSQL + Metabase Transform output)
```

---

## 6. SQL Dialect: SQLite vs. PostgreSQL

The transform SQL files are written to be PostgreSQL-compatible. The key
differences from the MVP SQLite SQL are minor:

| Feature | SQLite (MVP) | PostgreSQL (Transforms) |
|---|---|---|
| `MAX(CASE WHEN ...)` conditional aggregation | Supported | Supported (identical syntax) |
| `LAG()` window function | Supported (>= 3.25.0) | Supported (fully) |
| `NULLIF()` | Supported | Supported (identical syntax) |
| `ROUND(x, 2)` | Supported | Supported (identical syntax) |
| `COALESCE()` | Supported | Supported (identical syntax) |
| `CREATE VIEW` | Supported | Supported |
| Integer division | Truncates to integer | Returns integer for integer inputs |

The main risk is **integer division**. In PostgreSQL, if `metric_value` is
stored as `INTEGER`, then `gross_profit / revenue` returns 0, not a decimal.
The fix is to cast: `gross_profit::NUMERIC / NULLIF(revenue::NUMERIC, 0)`.
The transform files should use explicit `::NUMERIC` casts on all KPI divisions.

---

## 7. What This Experiment Will Evaluate

- Whether Metabase Transforms can execute the metric pivot SQL against PostgreSQL.
- Whether LAG() window functions work correctly in Metabase SQL models on PostgreSQL.
- Whether Transform 03 output matches the MVP mart CSV row-by-row (exact numeric
  values, column names, row count) — this is the primary validation.
- Whether Metabase can reference one saved model from another (model chaining).
- Whether a Metabase dashboard built on Transform 03 shows the same KPI values
  as the MVP executive summary and validation report.
- How much effort the setup requires vs. the existing Python + SQLite pipeline.
- What SQL dialect adjustments (if any) are needed when moving from SQLite to PostgreSQL.

---

## 8. What This Experiment Will NOT Evaluate Yet

- **Real document extraction**: PDF/MarkItDown extraction is Phase 8+. This
  experiment uses the existing synthetic data only.
- **Metabase embedding or API**: No embedded analytics or API integration.
- **User permissions or row-level security**: Not in scope.
- **Automated refresh or scheduling**: Transform refresh cadence is out of scope.
- **dbt comparison**: A dbt vs. Metabase Transforms comparison is a possible
  Phase 3 topic.
- **Production PostgreSQL**: The Docker PostgreSQL instance is local and
  ephemeral. No cloud database is provisioned in this phase.
- **Migrating the MVP to PostgreSQL permanently**: SQLite remains the MVP
  database. PostgreSQL is used only for the Transforms experiment.

---

## 9. Success Criteria

The experiment is considered successful when ALL of the following are true:

1. Metabase OSS and PostgreSQL are running in Docker and accessible locally.
2. PostgreSQL contains all five source tables with correct row counts.
3. Metabase is connected to the PostgreSQL analytics database.
4. Transform 01 executes in Metabase and returns 6 rows with 10 columns.
5. Transform 02 executes in Metabase and returns 6 rows with 22 columns.
6. Transform 03 executes in Metabase and returns 6 rows with 22 columns.
7. Transform 03 output matches `dashboard/mart_company_financial_performance.csv`
   row-by-row (all numeric values identical after ROUND, column order not required).
8. A Metabase dashboard with at least 3 chart tiles is built on Transform 03.
9. Screenshots of working transforms and dashboard are saved to `metabase/screenshots/`.

---

## 10. Risks and Limitations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Integer division in PostgreSQL truncates KPI percentages to 0** | High | High | Cast all KPI division operands to `::NUMERIC` in transform SQL |
| Model chaining not available in Metabase free tier | Medium | Medium | Transforms 02 and 03 are self-contained as fallback |
| Output does not match MVP CSV due to floating-point rounding differences | Low | Low | Use `ROUND(..., 2)` in both; compare with tolerance |
| Docker volume/path issues on Windows for PostgreSQL data persistence | Medium | Low | Use named Docker volumes instead of bind mounts |
| Metabase setup state accidentally committed to git | Medium | Medium | Add `.metabase/` and `metabase_db/` to `.gitignore` |
| PostgreSQL container not reachable from Metabase container | Low | High | Use Docker Compose internal network; Metabase connects via service name |
| Metabase Transforms feature gated behind a paid plan version | Low | High | Verify feature availability in Metabase OSS before setup |

---

## 11. Future Implementation Steps

See `docs/28_DOCKER_POSTGRES_METABASE_PLAN.md` for the full step-by-step
Docker and PostgreSQL setup procedure.

### High-level sequence

1. Create Docker Compose file (`metabase/docker-compose.yml`) — see doc 28.
2. Start Docker services: PostgreSQL + Metabase OSS.
3. Create PostgreSQL schema and load synthetic data.
4. Connect Metabase to PostgreSQL analytics database.
5. Create Transform 01, validate 6 rows.
6. Create Transform 02, validate 6 rows × 22 columns.
7. Create Transform 03, validate against MVP mart CSV.
8. Build dashboard on Transform 03.
9. Capture screenshots to `metabase/screenshots/`.
10. Document findings and any SQL adjustments needed.

---

## Appendix: SQL File Mapping

| File | Target DB | Purpose | Status |
|---|---|---|---|
| `metabase/transforms/01_financial_metric_pivot.sql` | PostgreSQL | Transform 01 — metric pivot | Authored, PostgreSQL-compatible, not yet executed |
| `metabase/transforms/02_financial_kpi_model.sql` | PostgreSQL | Transform 02 — KPI calculations | Authored, PostgreSQL-compatible, not yet executed |
| `metabase/transforms/03_mart_company_financial_performance.sql` | PostgreSQL | Transform 03 — dashboard mart | Authored, PostgreSQL-compatible, not yet executed |
| `sql/03_financial_kpis.sql` | SQLite | MVP KPI model (source of truth) | In production, not modified |
| `sql/05_mart_company_financial_performance.sql` | SQLite | MVP mart view (source of truth) | In production, not modified |
