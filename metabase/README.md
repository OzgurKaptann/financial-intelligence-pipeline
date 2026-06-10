# Metabase Transforms — Phase 2 Experiment

> **WARNING: Do not attempt to create Metabase Transforms directly on SQLite.**
> Metabase can browse and query SQLite tables, but the Transforms feature
> requires a supported database backend. PostgreSQL is used for this experiment.
> See `docs/28_DOCKER_POSTGRES_METABASE_PLAN.md` for the Docker setup plan.

---

## Purpose

This directory contains the Phase 2 experiment for evaluating whether
**Metabase Transforms** can reproduce the SQL mart layer currently produced
by the MVP pipeline.

The MVP pipeline generates its mart layer by running SQL files against a local
SQLite database via Python scripts. The goal of this experiment is to determine
whether the same transformation logic can live inside Metabase — using
PostgreSQL as the transform-capable backend.

---

## Database Architecture for Phase 2

The MVP and the Metabase experiment use **separate databases**. The MVP SQLite
database is not replaced or modified.

| Database | Technology | Purpose |
|---|---|---|
| MVP database | SQLite (`data/financial_intelligence.db`) | Source of truth for the existing pipeline. Not touched. |
| Metabase analytics DB | PostgreSQL (Docker) | Target for Transforms experiment. Receives a copy of the synthetic data. |
| Metabase app DB | PostgreSQL (Docker, optional) | Stores Metabase's own metadata (questions, dashboards, users). |

Data flows from the existing synthetic CSV exports → PostgreSQL → Metabase Transforms.

---

## What is Metabase Transforms?

Metabase Transforms is a feature that lets you write SQL models directly inside
Metabase. Each model is a saved SQL query that can be referenced by other models
or questions, similar to dbt models or SQL views. Transforms allow you to build
a layered data model inside Metabase without a separate transformation tool.

**Transforms require a supported database.** SQLite is supported for browsing
and native queries, but not for the Transforms feature. PostgreSQL is the
recommended database for this experiment.

---

## Experiment Scope

This experiment evaluates whether the three-layer mart SQL in the MVP can be
reproduced in Metabase Transforms against a PostgreSQL database, and whether
the output matches the MVP mart CSV exactly.

| MVP SQL file | Database | Metabase Transform equivalent |
|---|---|---|
| `sql/03_financial_kpis.sql` (metric_pivot CTE) | SQLite | `transforms/01_financial_metric_pivot.sql` → PostgreSQL |
| `sql/03_financial_kpis.sql` (kpi_base + KPIs) | SQLite | `transforms/02_financial_kpi_model.sql` → PostgreSQL |
| `sql/05_mart_company_financial_performance.sql` | SQLite | `transforms/03_mart_company_financial_performance.sql` → PostgreSQL |

The SQL files in `transforms/` are PostgreSQL-compatible and Metabase-ready.
They are not executed yet — execution happens when the Docker environment
described in `docs/28_DOCKER_POSTGRES_METABASE_PLAN.md` is running.

---

## Directory Structure

```
metabase/
├── README.md                              ← this file
├── transforms/
│   ├── 01_financial_metric_pivot.sql      ← Transform 1: long → wide metric pivot
│   ├── 02_financial_kpi_model.sql         ← Transform 2: KPI calculations
│   └── 03_mart_company_financial_performance.sql  ← Transform 3: dashboard mart
└── screenshots/
    └── .gitkeep                           ← placeholder for Metabase UI screenshots
```

---

## Current Status

**Infrastructure**

- [ ] Docker Compose file created for Metabase + PostgreSQL
- [ ] PostgreSQL container running and accessible
- [ ] Metabase OSS container running and accessible at localhost:3000
- [ ] Metabase connected to PostgreSQL analytics database

**Data Loading**

- [ ] PostgreSQL schema created (tables: fact_financial_metric, dim_company, dim_period, dim_metric, fact_risk_keyword)
- [ ] Synthetic data loaded from existing CSV exports into PostgreSQL

**Transforms**

- [x] Transform SQL files authored from MVP source SQL (PostgreSQL-compatible)
- [ ] Transform 01 created and validated in Metabase UI (6 rows, 10 columns)
- [ ] Transform 02 created and validated in Metabase UI (6 rows, 22 columns)
- [ ] Transform 03 created and validated in Metabase UI (6 rows, 22 columns)

**Validation**

- [ ] Transform 03 output exported and compared row-by-row against MVP mart CSV
- [ ] Any SQL dialect differences documented

**Dashboard**

- [ ] Dashboard built on top of Transform 03
- [ ] Screenshots saved to `metabase/screenshots/`

---

## Important Notes

- The SQL in `transforms/` is **PostgreSQL-compatible and conceptually Metabase-ready**
  but has not been executed in a live Metabase instance yet.
- The existing MVP pipeline in `src/` and `sql/` is **not modified** by this experiment.
- SQLite (`data/financial_intelligence.db`) is the MVP source of truth and remains unchanged.
- The Metabase instance state (questions, dashboards, settings) is **not committed to git**.
  Only the SQL transform files and screenshots are version-controlled.
- See `docs/27_METABASE_IMPLEMENTATION_PLAN.md` for the full transform architecture plan.
- See `docs/28_DOCKER_POSTGRES_METABASE_PLAN.md` for the Docker and PostgreSQL setup plan.
