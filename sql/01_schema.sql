-- =============================================================================
-- 01_schema.sql
-- Financial Intelligence Pipeline — SQLite Database Schema
--
-- Creates all dimension tables, fact tables, indexes, and seeds dim_metric.
-- Run this file to create or reset the database structure.
--
-- Execution order matters: fact tables are dropped before dimension tables
-- to avoid foreign key violations. Tables are created in the reverse order.
--
-- This script is idempotent. Running it twice produces the same result.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- =============================================================================
-- DROP — reverse dependency order
-- (facts first, then dimensions)
-- =============================================================================

DROP TABLE IF EXISTS fact_risk_keyword;
DROP TABLE IF EXISTS fact_financial_metric;
DROP TABLE IF EXISTS fact_document_source;
DROP TABLE IF EXISTS dim_metric;
DROP TABLE IF EXISTS dim_period;
DROP TABLE IF EXISTS dim_company;

-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- dim_company
-- Grain: one row per company being analysed.
-- company_id is assigned by the Python loader from config.py (not auto-assigned)
-- so that IDs stay stable across database rebuilds.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_company (
    company_id   INTEGER PRIMARY KEY,
    company_name TEXT    NOT NULL,
    sector       TEXT    NOT NULL,
    country      TEXT    NOT NULL,

    CONSTRAINT uq_company_name UNIQUE (company_name)
);

-- -----------------------------------------------------------------------------
-- dim_period
-- Grain: one row per reporting period (e.g. FY2024, FY2025).
-- period_id is assigned by the Python loader from config.py.
-- Dates are stored as ISO-8601 text (YYYY-MM-DD) because SQLite has no
-- native DATE type; this allows lexicographic sorting to work correctly.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_period (
    period_id    INTEGER PRIMARY KEY,
    period_label TEXT    NOT NULL,
    start_date   TEXT    NOT NULL,
    end_date     TEXT    NOT NULL,

    CONSTRAINT uq_period_label UNIQUE (period_label),
    CONSTRAINT chk_period_dates CHECK (end_date > start_date)
);

-- -----------------------------------------------------------------------------
-- dim_metric
-- Grain: one row per standardised financial metric definition.
-- Seeded at schema creation time — the metric catalogue is fixed for the MVP.
-- metric_id uses AUTOINCREMENT because rows are inserted once by this script
-- and never referenced by a manually assigned ID.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_metric (
    metric_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name        TEXT    NOT NULL,
    metric_category    TEXT    NOT NULL,
    metric_description TEXT    NOT NULL,
    unit               TEXT    NOT NULL,

    CONSTRAINT uq_metric_name     UNIQUE (metric_name),
    CONSTRAINT chk_metric_category CHECK (
        metric_category IN ('income_statement', 'balance_sheet', 'cash_flow', 'risk')
    )
);

-- =============================================================================
-- FACT TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- fact_document_source
-- Grain: one row per source document (or synthetic source) per company-period.
-- Tracks where each set of financial metrics came from.
-- In the synthetic MVP, one row is created per company-period with
-- document_type = 'synthetic'.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_document_source (
    document_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    source_document   TEXT    NOT NULL,
    company_id        INTEGER NOT NULL,
    period_id         INTEGER NOT NULL,
    document_type     TEXT    NOT NULL,
    is_synthetic      INTEGER NOT NULL DEFAULT 1,
    extraction_method TEXT    NOT NULL,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),

    CONSTRAINT uq_source_per_company_period UNIQUE (source_document, company_id, period_id),
    CONSTRAINT chk_is_synthetic_doc CHECK (is_synthetic IN (0, 1)),

    CONSTRAINT fk_doc_company FOREIGN KEY (company_id)
        REFERENCES dim_company (company_id),
    CONSTRAINT fk_doc_period  FOREIGN KEY (period_id)
        REFERENCES dim_period (period_id)
);

-- -----------------------------------------------------------------------------
-- fact_financial_metric
-- Grain: one row per company + period + metric.
-- This is the central fact table. KPI SQL models read from this table.
--
-- Note on metric_value sign: several metrics (operating_profit, net_income,
-- operating_cash_flow) can be negative for distressed companies. A hard
-- CHECK (metric_value >= 0) would block valid real data, so sign validation
-- is handled by the Python validation layer instead of the schema.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_financial_metric (
    financial_metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id          INTEGER NOT NULL,
    period_id           INTEGER NOT NULL,
    metric_id           INTEGER NOT NULL,
    document_id         INTEGER NOT NULL,
    metric_value        REAL    NOT NULL,
    currency            TEXT    NOT NULL,
    confidence_score    REAL    NOT NULL,
    is_synthetic        INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),

    -- Prevent duplicate metrics for the same company-period combination.
    -- A company can have only one accepted value per metric per period.
    CONSTRAINT uq_metric_per_company_period UNIQUE (company_id, period_id, metric_id),

    CONSTRAINT chk_confidence_score CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    CONSTRAINT chk_is_synthetic_metric CHECK (is_synthetic IN (0, 1)),

    CONSTRAINT fk_metric_company  FOREIGN KEY (company_id)
        REFERENCES dim_company (company_id),
    CONSTRAINT fk_metric_period   FOREIGN KEY (period_id)
        REFERENCES dim_period (period_id),
    CONSTRAINT fk_metric_def      FOREIGN KEY (metric_id)
        REFERENCES dim_metric (metric_id),
    CONSTRAINT fk_metric_document FOREIGN KEY (document_id)
        REFERENCES fact_document_source (document_id)
);

-- -----------------------------------------------------------------------------
-- fact_risk_keyword
-- Grain: one row per company + period + keyword + source document.
-- Empty in the synthetic MVP. Populated when real management commentary
-- or annual report text is processed in Phase 8+.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_risk_keyword (
    risk_keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id      INTEGER NOT NULL,
    period_id       INTEGER NOT NULL,
    document_id     INTEGER,           -- nullable: keyword may be inferred without a document
    keyword         TEXT    NOT NULL,
    risk_category   TEXT    NOT NULL,
    mention_count   INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),

    CONSTRAINT chk_mention_count  CHECK (mention_count >= 0),
    CONSTRAINT chk_risk_category  CHECK (
        risk_category IN ('macro', 'liquidity', 'operational', 'regulatory', 'other')
    ),

    CONSTRAINT fk_risk_company  FOREIGN KEY (company_id)
        REFERENCES dim_company (company_id),
    CONSTRAINT fk_risk_period   FOREIGN KEY (period_id)
        REFERENCES dim_period (period_id),
    CONSTRAINT fk_risk_document FOREIGN KEY (document_id)
        REFERENCES fact_document_source (document_id)
);

-- =============================================================================
-- INDEXES
-- Optimise the most common join and filter patterns used by KPI queries.
-- =============================================================================

-- fact_financial_metric — single-column lookups
CREATE INDEX IF NOT EXISTS idx_ffm_company_id
    ON fact_financial_metric (company_id);

CREATE INDEX IF NOT EXISTS idx_ffm_period_id
    ON fact_financial_metric (period_id);

CREATE INDEX IF NOT EXISTS idx_ffm_metric_id
    ON fact_financial_metric (metric_id);

-- fact_financial_metric — composite used by all KPI pivot queries
CREATE INDEX IF NOT EXISTS idx_ffm_company_period
    ON fact_financial_metric (company_id, period_id);

-- fact_document_source — used by joins from fact_financial_metric
CREATE INDEX IF NOT EXISTS idx_fds_company_period
    ON fact_document_source (company_id, period_id);

-- fact_risk_keyword — used when aggregating risk counts per company-period
CREATE INDEX IF NOT EXISTS idx_frk_company_period
    ON fact_risk_keyword (company_id, period_id);

-- =============================================================================
-- SEED DATA — dim_metric
--
-- The 8 core financial metrics are fixed for the MVP.
-- Descriptions are sourced from docs/06_METRICS_DICTIONARY.md.
-- unit = 'actual' means values are stored in the reported currency unit
-- (TRY, no thousands or millions scaling).
-- =============================================================================

INSERT INTO dim_metric (metric_name, metric_category, metric_description, unit) VALUES
    (
        'revenue',
        'income_statement',
        'Total income generated from primary business activities during the reporting period. Also known as Net Sales or Total Revenue.',
        'actual'
    ),
    (
        'gross_profit',
        'income_statement',
        'Revenue minus cost of goods sold. Measures profitability after direct production or procurement costs.',
        'actual'
    ),
    (
        'operating_profit',
        'income_statement',
        'Profit from operations before interest and tax. Also known as EBIT or Profit from Operations.',
        'actual'
    ),
    (
        'net_income',
        'income_statement',
        'Profit after all expenses, interest, tax, and other items. Also known as Net Profit or Profit for the Period.',
        'actual'
    ),
    (
        'total_assets',
        'balance_sheet',
        'Total resources controlled by the company as reported on the balance sheet. Equals current assets plus non-current assets.',
        'actual'
    ),
    (
        'total_debt',
        'balance_sheet',
        'Total financial debt obligations including short-term and long-term borrowings. Excludes trade payables and other non-financial liabilities.',
        'actual'
    ),
    (
        'cash',
        'balance_sheet',
        'Cash and cash equivalents available to the company. Includes bank balances and highly liquid short-term instruments.',
        'actual'
    ),
    (
        'operating_cash_flow',
        'cash_flow',
        'Net cash generated or used by core business operations during the reporting period. Distinct from free cash flow and investing activities.',
        'actual'
    );
