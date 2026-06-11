-- =============================================================================
-- 06_create_extracted_metrics_tables.sql
-- Phase 3.2 — Create PostgreSQL tables for document-derived extracted metrics
--
-- PURPOSE:
--   Create landing and analytics tables for metrics extracted from financial
--   documents via the Phase 3.1 Markdown extraction layer.
--   This connects document-derived data to the analytics warehouse path.
--
-- SCHEMAS MODIFIED:
--   raw        — raw.extracted_financial_metrics
--                raw.extraction_manifest
--   analytics  — analytics.document_extracted_financial_metric
--
-- SCHEMAS NOT TOUCHED:
--   transforms — transforms.mart_company_financial_performance is not modified
--   raw        — raw.synthetic_financial_metrics is not modified
--   analytics  — all Phase 2 analytics tables are not modified
--
-- IDEMPOTENCY:
--   Only the three Phase 3.2 tables listed above are dropped and recreated.
--   Safe to rerun at any time without affecting existing Phase 2 data.
--
-- GRAIN:
--   raw.extracted_financial_metrics              — one row per extracted metric value
--   raw.extraction_manifest                      — one row per source document processed
--   analytics.document_extracted_financial_metric — one row per loaded metric value
--
-- TYPES:
--   metric_value is NUMERIC to avoid integer division truncation in downstream
--   KPI calculations and to match the convention in Phase 2 tables.
-- =============================================================================


-- =============================================================================
-- Drop Phase 3.2 tables only — in dependency order
-- CASCADE removes any dependent objects on these tables only.
-- =============================================================================

DROP TABLE IF EXISTS analytics.document_extracted_financial_metric CASCADE;
DROP TABLE IF EXISTS raw.extraction_manifest                        CASCADE;
DROP TABLE IF EXISTS raw.extracted_financial_metrics               CASCADE;


-- =============================================================================
-- raw.extracted_financial_metrics
--
-- Landing table for data/extracted/extracted_financial_metrics.csv produced by
-- src/extract_financial_metrics.py (Phase 3.1).
--
-- One row per successfully extracted metric value.
-- Column names and types mirror the CSV structure as closely as possible.
-- No transformations are applied at this layer.
-- source_file preserves the document lineage so every value can be traced back
-- to the originating Markdown file.
-- =============================================================================

CREATE TABLE raw.extracted_financial_metrics (
    id                 SERIAL       PRIMARY KEY,
    source_file        TEXT         NOT NULL,
    company_name       TEXT         NOT NULL,
    period_label       TEXT         NOT NULL,
    metric_name        TEXT         NOT NULL,
    metric_value       NUMERIC,
    extraction_status  TEXT         NOT NULL,
    error_message      TEXT,
    extracted_at       TIMESTAMP,
    loaded_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE raw.extracted_financial_metrics IS
    'Raw landing table for extracted_financial_metrics.csv (Phase 3.1 output). '
    'One row per extracted metric value. 8 rows expected for the sample dataset.';

COMMENT ON COLUMN raw.extracted_financial_metrics.source_file IS
    'Markdown filename the metric was extracted from — primary lineage key.';
COMMENT ON COLUMN raw.extracted_financial_metrics.metric_value IS
    'Parsed numeric value. NULL when extraction_status is not success.';
COMMENT ON COLUMN raw.extracted_financial_metrics.loaded_at IS
    'Timestamp when this row was inserted into PostgreSQL by the loader.';


-- =============================================================================
-- raw.extraction_manifest
--
-- Landing table for data/extracted/extraction_manifest.csv produced by
-- src/extract_financial_metrics.py (Phase 3.1).
--
-- One row per source document processed by the extractor, recording summary
-- metadata: how many metrics were found, which were missing, and overall status.
-- Provides a document-level audit trail independent of the metric rows.
-- =============================================================================

CREATE TABLE raw.extraction_manifest (
    id                 SERIAL       PRIMARY KEY,
    source_file        TEXT         NOT NULL,
    company_name       TEXT,
    period_label       TEXT,
    metrics_extracted  INTEGER,
    missing_metrics    TEXT,
    extraction_status  TEXT         NOT NULL,
    error_message      TEXT,
    extracted_at       TIMESTAMP,
    loaded_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE raw.extraction_manifest IS
    'Document-level extraction audit trail (extraction_manifest.csv). '
    'One row per source document. Grain: one row per source_file.';

COMMENT ON COLUMN raw.extraction_manifest.metrics_extracted IS
    'Number of metric rows successfully written for this document.';
COMMENT ON COLUMN raw.extraction_manifest.missing_metrics IS
    'Pipe-separated list of canonical metric names not found in this document.';


-- =============================================================================
-- analytics.document_extracted_financial_metric
--
-- Analytics-layer view of document-derived metrics.
-- Populated from raw.extracted_financial_metrics by the loader script,
-- filtered to rows where extraction_status = 'success' and metric_value IS NOT NULL.
--
-- This table is the analytics warehouse entry point for document-derived data.
-- It can be joined with analytics.fact_financial_metric (synthetic data) for
-- side-by-side comparison once company and period keys are aligned.
--
-- loaded_at records when this row entered the analytics layer.
-- =============================================================================

CREATE TABLE analytics.document_extracted_financial_metric (
    id            SERIAL       PRIMARY KEY,
    source_file   TEXT         NOT NULL,
    company_name  TEXT         NOT NULL,
    period_label  TEXT         NOT NULL,
    metric_name   TEXT         NOT NULL,
    metric_value  NUMERIC      NOT NULL,
    loaded_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE analytics.document_extracted_financial_metric IS
    'Analytics-layer table for document-derived financial metrics (Phase 3.2). '
    'Grain: one row per source_file + company_name + period_label + metric_name. '
    '8 rows expected for the sample dataset.';

COMMENT ON COLUMN analytics.document_extracted_financial_metric.source_file IS
    'Originating Markdown filename — preserved for lineage traceability.';
COMMENT ON COLUMN analytics.document_extracted_financial_metric.loaded_at IS
    'Timestamp when this row was promoted from raw to analytics layer.';
