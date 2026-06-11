# LinkedIn and Metabase Outreach Notes

## Project Positioning

I built an open-source financial intelligence pipeline to evaluate how PostgreSQL-first transform marts can map to native Metabase query-based Transforms for small analytics teams.

The project converts raw financial documents into structured PostgreSQL KPI marts, validates the outputs, reconciles document-derived records against synthetic benchmarks, and connects the results to Metabase for dashboarding — with a dedicated evaluation of where native Metabase Transforms fit into that workflow.

---

## LinkedIn Post Draft

---

I spent the last few months building a financial intelligence pipeline from scratch to sharpen my analytics engineering skills and honestly evaluate how Metabase fits into a lightweight data stack.

Here is what the project does:

**Document ingestion** — Raw financial documents (.pdf, .docx, .xlsx) are converted to Markdown using Microsoft MarkItDown, then parsed into structured financial metrics using deterministic regex extraction. No LLM, no external API.

**PostgreSQL warehouse** — Extracted metrics load into a layered schema: `raw` → `analytics` → `transforms`. KPI marts (gross margin, operating margin, debt/assets, cash/debt, financial health flag) are materialized by version-controlled SQL scripts and Python runners.

**Reconciliation layer** — Document-derived KPI records are reconciled against a synthetic benchmark mart using a LEFT JOIN on company and period. Match status, KPI differences, and match rate are all reported cleanly.

**Metabase** — Connects to the PostgreSQL analytics database. The `transforms` schema is the primary dashboard source. I also wrote a separate evaluation of where native Metabase query-based Transforms can complement or replace the SQL-runner approach for analyst-owned marts.

**Validation** — 16 automated checks on the SQLite MVP mart. 14 SQL-based PASS/FAIL checks on the PostgreSQL KPI mart. Reconciliation results are transparent: unmatched records show exactly why they did not match, not just NULL.

The goal was not to build the most sophisticated system. The goal was to build something traceable, reproducible, and honest — where every KPI can be explained from source document to dashboard card.

If you work in analytics engineering, BI, or financial data — I'd be happy to hear how you approach the transform layer in your stack.

GitHub: [link to repo]

#AnalyticsEngineering #PostgreSQL #Metabase #DataEngineering #BusinessIntelligence #Python #SQL #OpenSource

---

## Short Message to Metabase Team

---

Hi [name],

I recently published an open-source project that builds a layered PostgreSQL analytics pipeline — document ingestion → metric extraction → KPI marts — and connects it to Metabase for dashboarding.

One part of the project is a dedicated evaluation of where native Metabase query-based Transforms can complement or replace a SQL-runner-based transform workflow for small analytics teams.

I thought it might be useful to the Metabase community as an honest case study of how the tool fits into a lightweight analytics stack. Happy to share the repository if it is relevant to work you are doing.

---

## GitHub Repo Description

End-to-end financial intelligence pipeline: document ingestion → PostgreSQL KPI marts → reconciliation → Metabase dashboards. Built for analytics engineering portfolio.

*(158 characters)*

---

## Suggested Hashtags

```
#AnalyticsEngineering
#PostgreSQL
#Metabase
#DataEngineering
#BusinessIntelligence
#Python
#SQL
#OpenSource
#FinancialData
#DataPipeline
#KPI
#MarkItDown
#DocumentIngestion
#DataValidation
```
