# 19 - Decision Log

## Purpose

This document records important project decisions and why they were made.

## Decision 001: Start with Synthetic Data

**Status:** Accepted

**Decision:** The MVP starts with synthetic financial data instead of real PDFs.

**Reason:** Real document extraction is messy and can delay the core analytics workflow. Synthetic data allows the project to prove database modeling, SQL KPIs, validation, dashboard marts, and reporting first.

**Consequence:** The MVP must clearly label data as synthetic. Real document ingestion becomes a future enhancement.

## Decision 002: Use SQLite for MVP

**Status:** Accepted

**Decision:** Use SQLite as the first database.

**Reason:** SQLite is simple, local, reproducible, and sufficient for portfolio-scale data.

**Consequence:** PostgreSQL-specific features are avoided in MVP SQL. Migration can happen later.

## Decision 003: Keep 8 Core Financial Metrics

**Status:** Accepted

**Decision:** The MVP uses 8 metrics: revenue, gross profit, operating profit, net income, total assets, total debt, cash, operating cash flow.

**Reason:** These metrics support meaningful growth, profitability, debt, and cash analysis without making the project too complex.

**Consequence:** Advanced metrics such as EBITDA, free cash flow, ROE, ROA, current ratio, and working capital can be added later.

## Decision 004: Calculate KPIs in SQL

**Status:** Accepted

**Decision:** Core KPIs should be calculated in SQL, not only in the dashboard tool.

**Reason:** SQL makes business logic reviewable, testable, and reusable.

**Consequence:** Dashboard should consume final mart tables rather than contain hidden metric logic.

## Decision 005: Generate Markdown Reports

**Status:** Accepted

**Decision:** Executive summary and validation report are generated as Markdown.

**Reason:** Markdown is GitHub-friendly, easy to review, and portfolio-readable.

**Consequence:** Reports can later be converted to PDF or HTML if needed.

## Decision 006: No Full AI Agent in MVP

**Status:** Accepted

**Decision:** The MVP will not build a full autonomous AI agent.

**Reason:** The project should showcase analytics engineering first. A premature agent layer would add complexity without improving the core business story.

**Consequence:** AI assistance is positioned around document processing and summary generation, not autonomous decision-making.

## Decision 007: Validation Is a First-Class Feature

**Status:** Accepted

**Decision:** Validation is required, not optional.

**Reason:** Financial analytics requires trust. A pipeline without validation is not credible.

**Consequence:** The project includes a validation report and explicit data quality checks.

## Pending Decisions

| Decision | Options | When to Decide |
|---|---|---|
| BI tool | Power BI, Tableau, Metabase | After mart table is ready |
| Real company data | Public companies, synthetic only, manually extracted | After MVP works |
| Database migration | Stay SQLite, migrate PostgreSQL | After dashboard and reports are done |
| PDF parsing tool | MarkItDown, PyMuPDF, Tabula, Camelot, manual | After document conversion phase |
| Currency handling | Single currency, FX conversion | When real multi-currency docs are added |
