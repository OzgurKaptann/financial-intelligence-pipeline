-- =============================================================================
-- 10_create_document_reconciliation.sql
-- Phase 4 — Document-Derived Metrics Reconciliation Layer
--
-- PURPOSE:
--   Compare document-derived KPI mart records against the synthetic benchmark
--   mart to identify matched vs. unmatched companies/periods and quantify
--   differences where comparison is possible.
--
-- TABLES CREATED:
--   transforms.document_metric_reconciliation
--     One row per document-derived company-period. Preserves lineage fields
--     (source_file, document_company_name, document_period_label) and adds
--     match_status, synthetic mart KPI values (when matched), and difference
--     fields.
--
--   transforms.document_kpi_reconciliation_summary
--     One-row aggregate summary: total records, match counts, match rate,
--     and average absolute differences for key KPIs.
--
-- SCHEMAS MODIFIED:
--   transforms — two new Phase 4 tables listed above
--
-- SCHEMAS NOT TOUCHED:
--   raw       — no changes
--   analytics — no changes
--   transforms.mart_company_financial_performance           — NOT modified (Phase 2.1)
--   transforms.document_financial_metric_pivot              — NOT modified (Phase 3.3)
--   transforms.mart_document_company_financial_performance  — NOT modified (Phase 3.3)
--
-- MATCHING STRATEGY:
--   LEFT JOIN from document mart to synthetic mart on:
--     LOWER(TRIM(doc.company_name)) = LOWER(TRIM(syn.company_name))
--     AND LOWER(TRIM(doc.period_label)) = LOWER(TRIM(syn.fiscal_period))
--   Normalise case and whitespace to make the join robust to minor formatting
--   differences. When no synthetic row matches, match_status is
--   'unmatched_company_or_period' and all synthetic/difference fields are NULL.
--
-- IDEMPOTENCY:
--   Only Phase 4 tables are dropped and recreated. All earlier tables are
--   untouched. Safe to rerun at any time.
--
-- DIVISION SAFETY:
--   All percentage-difference calculations use NULLIF(denominator, 0) so zero
--   denominators return NULL rather than causing a division-by-zero error.
-- =============================================================================


-- =============================================================================
-- Ensure the transforms schema exists
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS transforms;


-- =============================================================================
-- Drop Phase 4 tables only — in reverse dependency order.
-- Phase 2.1 and Phase 3.3 tables are NOT touched.
-- =============================================================================

DROP TABLE IF EXISTS transforms.document_kpi_reconciliation_summary CASCADE;
DROP TABLE IF EXISTS transforms.document_metric_reconciliation       CASCADE;


-- =============================================================================
-- transforms.document_metric_reconciliation
--
-- Joins the document-derived KPI mart (left) to the synthetic benchmark mart
-- (right) to produce one reconciliation row per document company-period.
--
-- Preserved lineage:
--   source_file              — originating Markdown file
--   document_company_name    — company name as it appears in the document
--   document_period_label    — period label as it appears in the document
--
-- Match status:
--   matched                       — synthetic row found for same company + period
--   unmatched_company_or_period   — no synthetic row found; expected for documents
--                                   whose company names are not in the synthetic set
--
-- Difference fields (doc value − synthetic value):
--   A positive value means the document figure is higher than synthetic.
--   All difference fields are NULL when match_status = 'unmatched_company_or_period'.
-- =============================================================================

CREATE TABLE transforms.document_metric_reconciliation AS
SELECT

    -- ── Lineage ───────────────────────────────────────────────────────────────
    doc.source_file,
    doc.company_name                            AS document_company_name,
    doc.period_label                            AS document_period_label,

    -- ── Match status ──────────────────────────────────────────────────────────
    CASE
        WHEN syn.company_name IS NOT NULL THEN 'matched'
        ELSE                                   'unmatched_company_or_period'
    END                                         AS match_status,

    -- ── Document KPI values ───────────────────────────────────────────────────
    doc.revenue                                 AS doc_revenue,
    doc.gross_margin_pct                        AS doc_gross_margin_pct,
    doc.operating_margin_pct                    AS doc_operating_margin_pct,
    doc.net_margin_pct                          AS doc_net_margin_pct,
    doc.debt_to_assets_pct                      AS doc_debt_to_assets_pct,
    doc.cash_to_debt_pct                        AS doc_cash_to_debt_pct,

    -- ── Synthetic benchmark KPI values (NULL when unmatched) ──────────────────
    syn.revenue                                 AS syn_revenue,
    syn.gross_margin_pct                        AS syn_gross_margin_pct,
    syn.operating_margin_pct                    AS syn_operating_margin_pct,
    syn.net_margin_pct                          AS syn_net_margin_pct,
    syn.debt_to_assets_pct                      AS syn_debt_to_assets_pct,
    syn.cash_to_debt_pct                        AS syn_cash_to_debt_pct,

    -- ── Absolute differences (doc − synthetic; NULL when unmatched) ──────────
    ROUND(doc.revenue - syn.revenue, 2)         AS revenue_difference,

    ROUND(
        doc.gross_margin_pct
        - syn.gross_margin_pct, 2)              AS gross_margin_difference,

    ROUND(
        doc.operating_margin_pct
        - syn.operating_margin_pct, 2)          AS operating_margin_difference,

    ROUND(
        doc.net_margin_pct
        - syn.net_margin_pct, 2)                AS net_margin_difference,

    ROUND(
        doc.debt_to_assets_pct
        - syn.debt_to_assets_pct, 2)            AS debt_to_assets_difference,

    ROUND(
        doc.cash_to_debt_pct
        - syn.cash_to_debt_pct, 2)              AS cash_to_debt_difference,

    -- ── Percentage difference on revenue (safe division) ─────────────────────
    -- Formula: (doc_revenue − syn_revenue) / syn_revenue × 100
    -- NULL when unmatched or when syn_revenue = 0.
    ROUND(
        (doc.revenue - syn.revenue)
        / NULLIF(syn.revenue, 0)
        * 100,
        2
    )                                           AS revenue_pct_difference,

    -- ── Metadata ──────────────────────────────────────────────────────────────
    NOW()                                       AS reconciliation_created_at

FROM transforms.mart_document_company_financial_performance  doc

LEFT JOIN transforms.mart_company_financial_performance      syn
    ON  LOWER(TRIM(doc.company_name))  = LOWER(TRIM(syn.company_name))
    AND LOWER(TRIM(doc.period_label))  = LOWER(TRIM(syn.fiscal_period))

ORDER BY doc.company_name, doc.period_label;

COMMENT ON TABLE transforms.document_metric_reconciliation IS
    'Phase 4 reconciliation of document-derived KPIs against the synthetic '
    'benchmark mart. Grain: one row per source_file + document company-period. '
    'match_status = matched | unmatched_company_or_period.';

COMMENT ON COLUMN transforms.document_metric_reconciliation.match_status IS
    'matched: a synthetic row was found for the same company + period. '
    'unmatched_company_or_period: no synthetic row matched — expected for '
    'documents whose company names are not in the synthetic benchmark set.';

COMMENT ON COLUMN transforms.document_metric_reconciliation.revenue_pct_difference IS
    '(doc_revenue - syn_revenue) / syn_revenue * 100. '
    'NULL when unmatched or when syn_revenue = 0 (NULLIF protection).';


-- =============================================================================
-- transforms.document_kpi_reconciliation_summary
--
-- Single-row aggregate summary of the reconciliation result.
--
-- Columns:
--   total_document_records          — total rows in document_metric_reconciliation
--   matched_records                 — rows where match_status = 'matched'
--   unmatched_records               — rows where match_status = 'unmatched_company_or_period'
--   match_rate_pct                  — matched / total × 100; 0.00 when total = 0
--   avg_abs_revenue_difference      — AVG(ABS(revenue_difference)) for matched rows only
--   avg_abs_net_margin_difference   — AVG(ABS(net_margin_difference)) for matched rows only
--   summary_created_at              — materialization timestamp
--
-- NOTE: avg_abs_* fields are NULL (not 0) when there are no matched rows.
-- NULL accurately reflects that no comparison was possible.
-- =============================================================================

CREATE TABLE transforms.document_kpi_reconciliation_summary AS
SELECT

    COUNT(*)                                                        AS total_document_records,

    COUNT(*) FILTER (WHERE match_status = 'matched')               AS matched_records,

    COUNT(*) FILTER (
        WHERE match_status = 'unmatched_company_or_period'
    )                                                               AS unmatched_records,

    -- COALESCE converts NULL (no rows) to 0.00 for a clean display value.
    COALESCE(
        ROUND(
            COUNT(*) FILTER (WHERE match_status = 'matched')::NUMERIC
            / NULLIF(COUNT(*), 0)
            * 100,
            2
        ),
        0.00
    )                                                               AS match_rate_pct,

    -- NULL when no matched rows — no comparison was possible.
    ROUND(
        AVG(ABS(revenue_difference))
            FILTER (WHERE match_status = 'matched'),
        2
    )                                                               AS avg_abs_revenue_difference,

    ROUND(
        AVG(ABS(net_margin_difference))
            FILTER (WHERE match_status = 'matched'),
        2
    )                                                               AS avg_abs_net_margin_difference,

    NOW()                                                           AS summary_created_at

FROM transforms.document_metric_reconciliation;

COMMENT ON TABLE transforms.document_kpi_reconciliation_summary IS
    'Phase 4 one-row aggregate summary of the document reconciliation result. '
    'match_rate_pct = 0.00 when no document companies match the synthetic set — '
    'this is expected and correct for the current sample dataset.';
