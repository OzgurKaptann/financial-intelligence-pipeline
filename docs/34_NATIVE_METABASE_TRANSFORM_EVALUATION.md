# Native Metabase Transform Evaluation

## Purpose

This document evaluates whether a small analytics team can build an analytics engineering
workflow using PostgreSQL, Metabase, and Metabase-style transforms without immediately
adopting dbt.

The goal is to position the project clearly for the Metabase community: explaining what
has been implemented in this repository, how the existing transform logic maps conceptually
to native Metabase Transforms, and what should remain outside Metabase for engineering
correctness and reproducibility.

---

## Current Implementation

The following components are already implemented and version-controlled in this repository:

| Component | Description |
|-----------|-------------|
| PostgreSQL-first transform layer | All mart logic is defined as SQL scripts under `metabase/postgres/sql/` and executed via Python runners |
| Version-controlled SQL transform scripts | `04_create_transform_mart.sql`, `08_create_document_kpi_mart.sql`, `10_create_document_reconciliation.sql` |
| Python runners for materialization and validation | `src/materialize_postgres_mart.py`, `src/materialize_document_kpi_mart.py`, `src/materialize_document_reconciliation.py` |
| `transforms.mart_company_financial_performance` | Synthetic KPI mart — 6 rows (3 companies × 2 periods) |
| `transforms.mart_document_company_financial_performance` | Document-derived KPI mart with 7 financial ratios and health flag |
| `transforms.document_metric_reconciliation` | Reconciliation of document-derived metrics against synthetic benchmark |
| Metabase dashboard connected to PostgreSQL transform marts | Financial Intelligence Dashboard built on top of the transform layer |

**Important clarity:** The project has implemented all transform logic outside Metabase first,
using PostgreSQL SQL scripts and Python runners. This approach ensures the pipeline is
reproducible, version-controlled, and easy to validate in CI or a local environment —
independent of a running Metabase instance.

---

## How This Maps to Native Metabase Transforms

Native Metabase Transforms allow analysts to write query results back into a database as
persistent tables. Transforms can be tagged, grouped into jobs, and scheduled for periodic
execution — making them a lightweight alternative to dbt for analyst-owned marts.

The following current project assets are direct candidates for native Metabase query-based
Transforms:

| Current SQL Script | Metabase Transform Candidate | Output Table |
|--------------------|------------------------------|--------------|
| [`metabase/postgres/sql/04_create_transform_mart.sql`](../metabase/postgres/sql/04_create_transform_mart.sql) | Query-based transform for synthetic KPI mart | `transforms.mart_company_financial_performance` |
| [`metabase/postgres/sql/08_create_document_kpi_mart.sql`](../metabase/postgres/sql/08_create_document_kpi_mart.sql) | Query-based transform for document-derived KPI mart | `transforms.mart_document_company_financial_performance` |
| [`metabase/postgres/sql/10_create_document_reconciliation.sql`](../metabase/postgres/sql/10_create_document_reconciliation.sql) | Query-based transform for reconciliation mart | `transforms.document_metric_reconciliation` |

The key mapping principle: wherever this project runs a Python script to execute a SQL
file and materialize a table, a native Metabase Transform can replace the materialization
step — provided the source tables already exist in the connected database.

---

## What Metabase Is Strong At

For a project at this scale and audience, Metabase provides genuine strengths:

- **Fast dashboarding** — SQL questions and visual questions connect directly to the
  transform mart tables without an additional BI layer
- **SQL question and model workflow** — analysts can write and save parameterized SQL
  questions, building a semantic layer on top of PostgreSQL without dbt
- **BI-friendly semantic layer** — field aliases, default display types, and metric
  definitions can be applied in the Metabase data model editor, reducing dashboard setup time
- **Persistent transform tables for small teams** — native Transforms write query results
  back to the database, making marts available to any connected tool (not just Metabase)
- **Scheduled transform jobs** — Transforms can be scheduled to refresh on a cron-like
  interval without external orchestration
- **Analyst-owned marts and lightweight analytics engineering** — a single analyst or
  small team can own the full chain from source tables to dashboard without standing up
  Airflow, dbt Cloud, or a separate orchestration service

---

## What Should Stay Outside Metabase

The following pipeline components are not candidates for implementation inside Metabase,
and should remain in the version-controlled Python and SQL layer:

| Component | Reason to Keep Outside Metabase |
|-----------|--------------------------------|
| Raw document conversion with Microsoft MarkItDown | Requires a local Python runtime, file I/O, and library dependencies — cannot run inside a BI tool |
| Regex/rule-based financial metric extraction | Deterministic Python logic with multi-alias matching, confidence scoring, and manifest output — belongs in `src/` |
| Data quality tests that should run in CI | PASS/FAIL validation checks against mart tables should be part of a reproducible test suite, not a dashboard |
| Git-versioned SQL development | SQL scripts under `metabase/postgres/sql/` are committed to version control — Metabase UI edits are not version-controlled by default |
| Environment setup and Docker orchestration | `docker-compose.yml`, `.env`, and init scripts are infrastructure — they belong outside any application layer |
| Future dbt/Airflow/Prefect production orchestration | If workload grows beyond analyst-owned marts, a proper orchestration framework should be adopted |

---

## Evaluation Summary

| Area | PostgreSQL-first implementation | Native Metabase Transform fit | Recommendation |
|------|---------------------------------|-------------------------------|----------------|
| Synthetic KPI mart | `04_create_transform_mart.sql` + Python runner | Strong candidate — simple pivot + KPI calculation | Could move to Metabase Transform; keep SQL in version control as source of truth |
| Document-derived KPI mart | `08_create_document_kpi_mart.sql` + Python runner | Strong candidate — same pattern as synthetic mart | Could move to Metabase Transform after source tables are stable |
| Reconciliation mart | `10_create_document_reconciliation.sql` + Python runner | Moderate candidate — depends on both upstream marts being fresh | Consider scheduling after upstream Transforms complete |
| Document conversion | `src/document_converter.py` (MarkItDown) | Not applicable | Must stay in Python — file I/O and local runtime required |
| Metric extraction | `src/extract_financial_metrics.py` (regex) | Not applicable | Must stay in Python — rule-based extraction logic is not SQL-expressible |
| Validation | `metabase/postgres/sql/09_*`, `11_*` + Python runners | Partial — SQL checks could run as Metabase questions | Keep PASS/FAIL logic in Python runners for CI integration; use Metabase for monitoring views |
| Scheduling | Python runner + manual execution | Strong fit — Metabase Transform jobs support cron scheduling | Metabase scheduling is a viable replacement for the Python runner cron for mart refreshes |
| Dashboarding | Metabase dashboard on `transforms.*` marts | Native strength | Metabase is already the dashboard layer; no change needed |

---

## Recommended Positioning

The following statement is suitable for use in the README, a LinkedIn post, or a portfolio description:

> "This project implements a PostgreSQL-first, version-controlled transform pipeline and
> evaluates how the same mart logic could map to native Metabase query-based Transforms.
> Metabase is used as the BI and dashboard layer, while document ingestion, extraction,
> and validation remain outside Metabase for reproducibility and engineering control."

---

## Honest Scope Statement

This repository does not claim that all transforms were created inside the Metabase UI.
Instead, it implements transform logic in PostgreSQL first and documents which parts are
candidates for native Metabase Transforms.

The SQL scripts, Python runners, and validation checks in this repository are the
authoritative implementation. Metabase is the consumption and dashboarding layer.

---

## Next Step

To complete a practical evaluation of native Metabase Transforms beyond this documentation:

1. Manually recreate one mart as a native Metabase query-based Transform — the synthetic
   KPI mart (`transforms.mart_company_financial_performance`) is the recommended starting
   point, as its SQL is simple and already version-controlled.

2. Save screenshot evidence under `metabase/screenshots/` — at minimum: the Transform
   editor, the scheduled job configuration, and the resulting table row count in Metabase.

3. Compare the native Transform experience against the current PostgreSQL-first approach
   across these dimensions:

   | Dimension | PostgreSQL-first (current) | Native Metabase Transform |
   |-----------|---------------------------|--------------------------|
   | Development experience | SQL editor + git commit | Metabase UI editor, no git by default |
   | Validation visibility | PASS/FAIL terminal output + Python assertions | SQL question in Metabase; no assertion framework |
   | Scheduling | Manual Python runner or external cron | Built-in Metabase job scheduler |
   | Version control | Full git history for SQL and runner scripts | Metabase internal versioning only |
   | Dashboard integration | Direct — dashboard reads from `transforms.*` tables | Direct — same tables, same connection |

This comparison will produce a concrete data point for teams deciding between PostgreSQL-first
analytics engineering and Metabase-native transform workflows at small scale.
