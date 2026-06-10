# 28 — Docker + PostgreSQL + Metabase Setup Plan

**Phase:** 2  
**Branch:** phase-2-metabase-transforms  
**Status:** Planning — Not Yet Implemented  
**Date:** 2026-06-10  

---

> **IMPORTANT: Do not attempt to create Metabase Transforms directly on SQLite.**
> Metabase can browse and query SQLite as a data source via native queries,
> but the Transforms feature only works against supported database backends.
> PostgreSQL is used for this experiment. SQLite remains the MVP database.

---

## 1. Overview

This document describes the Docker environment required to run the Phase 2
Metabase Transforms experiment. Docker is already installed on the development
machine.

The environment consists of two services:

| Service | Image | Purpose |
|---|---|---|
| `postgres_analytics` | `postgres:15` | Holds the financial intelligence tables for the Transforms experiment |
| `metabase` | `metabase/metabase:latest` (OSS) | Metabase OSS — BI tool with Transforms support |

An optional third service can be added:

| Service | Image | Purpose |
|---|---|---|
| `postgres_metabase_app` | `postgres:15` | Dedicated PostgreSQL for Metabase's own metadata (replaces H2 embedded DB) |

For the initial experiment, Metabase's built-in H2 database is acceptable
for storing metadata (questions, dashboards). The dedicated app database
becomes important if Metabase state needs to persist across container restarts.

---

## 2. Database Role Separation

```
SQLite  (data/financial_intelligence.db)
  ├── MVP source of truth
  ├── Used by src/ Python pipeline scripts
  ├── Can be browsed in Metabase (read-only)
  └── NOT used for Transforms — NOT modified in Phase 2

PostgreSQL (Docker: postgres_analytics)
  ├── Copy of synthetic financial data loaded from existing CSV exports
  ├── Target for all three Metabase Transforms
  ├── NOT the MVP source of truth
  └── Ephemeral for experiment; can be reset without affecting MVP

Metabase OSS (Docker: metabase)
  ├── Connected to postgres_analytics for Transforms
  ├── Can also browse SQLite via a separate data source (optional)
  └── UI state (questions, dashboards) stored in H2 or postgres_metabase_app
```

---

## 3. Proposed Docker Compose Configuration

The Docker Compose file will be located at `metabase/docker-compose.yml`.

**It is not created yet.** This document describes what it should contain
when the implementation phase begins.

### Services

**postgres_analytics**
- Image: `postgres:15`
- Container name: `financial_analytics_db`
- Database name: `financial_analytics`
- Port: `5433:5432` (5433 on host to avoid conflicts with any existing PostgreSQL)
- Volume: named volume `pg_analytics_data` for persistence
- Environment: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`

**metabase**
- Image: `metabase/metabase:latest`
- Container name: `financial_metabase`
- Port: `3000:3000`
- Depends on: `postgres_analytics`
- Environment: database connection for Metabase app DB (if using dedicated PG)

### Docker Compose structure (not yet created)

```yaml
# metabase/docker-compose.yml  ← FILE DOES NOT EXIST YET
# This is the planned structure, not a runnable file.

version: "3.9"
services:

  postgres_analytics:
    image: postgres:15
    container_name: financial_analytics_db
    environment:
      POSTGRES_USER: fin_user
      POSTGRES_PASSWORD: <set in .env, not hardcoded>
      POSTGRES_DB: financial_analytics
    ports:
      - "5433:5432"
    volumes:
      - pg_analytics_data:/var/lib/postgresql/data
    networks:
      - metabase_net

  metabase:
    image: metabase/metabase:latest
    container_name: financial_metabase
    ports:
      - "3000:3000"
    depends_on:
      - postgres_analytics
    networks:
      - metabase_net

volumes:
  pg_analytics_data:

networks:
  metabase_net:
```

**Credentials** will be stored in `metabase/.env` (not committed to git).
`metabase/.env` must be added to `.gitignore`.

---

## 4. What Must Be Added to .gitignore

Before any Docker files are created, add these entries to the project `.gitignore`:

```
# Metabase experiment — do not commit
metabase/.env
metabase/docker-compose.yml
metabase_db/
metabase/metabase.db
```

The Docker Compose file itself may be committed once credentials are confirmed
to use environment variable references only (no hardcoded passwords).
The `.env` file must never be committed.

---

## 5. PostgreSQL Schema Plan

The PostgreSQL analytics database needs the same five tables that the
SQLite MVP database contains. The schema mirrors `sql/01_schema.sql`
with PostgreSQL-compatible types.

**Key type differences from SQLite:**

| SQLite type | PostgreSQL equivalent | Notes |
|---|---|---|
| `INTEGER` | `INTEGER` | Same |
| `REAL` | `NUMERIC(20, 4)` | Use NUMERIC to avoid integer division in KPI calculations |
| `TEXT` | `TEXT` | Same |
| `UNIQUE(...)` constraint | `UNIQUE(...)` constraint | Same |

The `metric_value` column in `fact_financial_metric` must be `NUMERIC`, not
`INTEGER`, to ensure KPI division produces decimal results without explicit casting.

### Tables required (same grain as SQLite MVP)

| Table | Rows | Source for loading |
|---|---|---|
| `dim_company` | 3 | `data/processed/` or direct from MVP DB |
| `dim_period` | 2 | `data/processed/` or direct from MVP DB |
| `dim_metric` | 8 | `data/processed/` or direct from MVP DB |
| `fact_financial_metric` | 48 | `data/processed/` or direct from MVP DB |
| `fact_risk_keyword` | 0 | Empty in synthetic MVP |

---

## 6. Data Loading Plan

Data is loaded from existing CSV exports that the MVP pipeline already
produces. No MVP scripts are modified.

### Loading method options

**Option A — Python loader script (recommended)**
Write a new Phase 2 script (e.g., `src/phase2_load_postgres.py`) that:
1. Reads the existing processed CSV files from `data/processed/`.
2. Connects to PostgreSQL via `psycopg2` or `SQLAlchemy`.
3. Creates tables and inserts rows.

This script is a Phase 2 addition and does not affect the MVP pipeline.

**Option B — PostgreSQL COPY from CSV**
If the CSV files are accessible from inside the Docker container, use
`\COPY` via `psql` to load data directly. Simpler but requires
the container to have file access.

**Option C — SQLite to PostgreSQL migration script**
Write a one-time script that reads from `data/financial_intelligence.db`
(SQLite) and writes to PostgreSQL. Straightforward with pandas:
`df.to_sql(table_name, pg_engine)`.

The recommended approach is **Option A or C**, both of which are new Phase 2
scripts that do not touch any existing `src/` files.

---

## 7. SQL Dialect Adjustments for PostgreSQL

The transform SQL files in `metabase/transforms/` were authored to be
PostgreSQL-compatible, but the following adjustments must be verified
before execution:

### 7.1 Integer division — critical

In PostgreSQL, `INTEGER / INTEGER = INTEGER` (truncated, not decimal).
All KPI percentage calculations must use `NUMERIC` casts:

```sql
-- SQLite (MVP) — works because SQLite promotes to REAL
ROUND(gross_profit / NULLIF(revenue, 0) * 100, 2)

-- PostgreSQL — requires explicit cast if columns are INTEGER
ROUND(gross_profit::NUMERIC / NULLIF(revenue::NUMERIC, 0) * 100, 2)
```

If `metric_value` is stored as `NUMERIC` in PostgreSQL (recommended), the
cast is not strictly required but should still be added for clarity.

### 7.2 LAG() window function

PostgreSQL fully supports `LAG()`. No adjustments needed. The syntax is
identical to the SQLite version.

### 7.3 NULLIF, COALESCE, ROUND

All three functions have identical syntax in SQLite and PostgreSQL.
No adjustments needed.

### 7.4 Conditional aggregation (MAX CASE WHEN)

Identical syntax in both databases. No adjustments needed.

---

## 8. Metabase Setup Steps (planned, not yet executed)

### Step 1: Prepare .gitignore
Add `metabase/.env` and related entries before creating any Docker files.

### Step 2: Create Docker Compose file
Create `metabase/docker-compose.yml` with the structure described in section 3.
Create `metabase/.env` with credentials (never commit this file).

### Step 3: Start Docker services
```bash
cd metabase
docker compose up -d
```
Verify containers are running:
```bash
docker ps
```

### Step 4: Verify PostgreSQL is accessible
```bash
docker exec -it financial_analytics_db psql -U fin_user -d financial_analytics
```
Run `\dt` to confirm the connection works. Tables will not exist yet.

### Step 5: Create PostgreSQL schema and load data
Run the Phase 2 data loader script (to be written):
```bash
python src/phase2_load_postgres.py
```
Verify table row counts match the MVP:
```sql
SELECT 'dim_company' AS t, COUNT(*) FROM dim_company
UNION ALL SELECT 'dim_period', COUNT(*) FROM dim_period
UNION ALL SELECT 'dim_metric', COUNT(*) FROM dim_metric
UNION ALL SELECT 'fact_financial_metric', COUNT(*) FROM fact_financial_metric
UNION ALL SELECT 'fact_risk_keyword', COUNT(*) FROM fact_risk_keyword;
-- Expected: 3, 2, 8, 48, 0
```

### Step 6: Open Metabase and connect to PostgreSQL
- Navigate to `http://localhost:3000`.
- Complete the initial Metabase setup wizard.
- Add a new database connection:
  - Type: PostgreSQL
  - Host: `postgres_analytics` (Docker internal service name)
  - Port: `5432` (internal Docker port, not 5433)
  - Database: `financial_analytics`
  - Username/Password: from `.env`

### Step 7: Create Transform 01
- Metabase → New → Model
- Select database: `financial_analytics`
- Paste SQL from `metabase/transforms/01_financial_metric_pivot.sql`
- Run query — verify 6 rows, 10 columns
- Save as: `Financial Metric Pivot`

### Step 8: Create Transform 02
- Metabase → New → Model
- Select database: `financial_analytics`
- Paste SQL from `metabase/transforms/02_financial_kpi_model.sql`
- Run query — verify 6 rows, 22 columns
- Save as: `Financial KPI Model`

### Step 9: Create Transform 03
- Metabase → New → Model
- Select database: `financial_analytics`
- Paste SQL from `metabase/transforms/03_mart_company_financial_performance.sql`
- Run query — verify 6 rows, 22 columns
- Save as: `Mart — Company Financial Performance`

### Step 10: Validate output against MVP mart CSV
- Download Transform 03 result as CSV from Metabase.
- Compare against `dashboard/mart_company_financial_performance.csv`.
- All 6 rows, all 22 columns, all numeric values must match (within ROUND precision).
- Document any discrepancies.

### Step 11: Build dashboard
- Create Metabase questions from Transform 03.
- Build a dashboard with at minimum:
  - Revenue by company and period (bar chart)
  - Gross margin % comparison (bar chart)
  - Debt/assets % by company (bar chart)
- Save screenshots to `metabase/screenshots/`.

---

## 9. What Is NOT Done in This Phase

- No Docker files are created yet. This document describes what they will contain.
- No `docker-compose.yml` exists yet.
- No PostgreSQL schema or data loader script exists yet.
- No Metabase instance is running yet.
- The MVP pipeline (`src/`, `sql/`) is not modified.
- No cloud infrastructure is provisioned.

---

## 10. Risks and Windows-Specific Notes

| Risk | Notes |
|---|---|
| Docker Desktop must be running | Ensure Docker Desktop is started before running `docker compose up` |
| Port 3000 conflict | If another service uses port 3000, change Metabase to `"3001:3000"` |
| Port 5433 conflict | If another PostgreSQL is on 5432, 5433 is used as the host-side port |
| Windows file path in Docker volumes | Use named volumes (not bind mounts to Windows paths) to avoid permission issues |
| Metabase H2 database reset on container restart | Use `postgres_metabase_app` as the Metabase app DB for persistent state |
| `.env` file accidentally committed | Must be in `.gitignore` before creating the file |
| Metabase Transforms feature availability | Verify Transforms/Models are available in the OSS version before setup |

---

## 11. Files This Plan Will Produce (not created yet)

| File | Status |
|---|---|
| `metabase/docker-compose.yml` | Not created — planned |
| `metabase/.env` | Not created — planned (never commit) |
| `src/phase2_load_postgres.py` | Not created — planned Phase 2 script |
| `sql/phase2_postgres_schema.sql` | Not created — planned PostgreSQL DDL |
| `metabase/screenshots/*.png` | Not created — captured during experiment |

All existing MVP files remain unchanged.
