# 15 - Risks, Assumptions, and Limitations

## Purpose

A professional project does not hide uncertainty. This document makes the project's assumptions and risks explicit.

## Core Assumptions

### Assumption 1: Synthetic Data First

The MVP starts with synthetic data to build and test the analytics workflow.

Why:

- faster development
- easier testing
- avoids early PDF extraction chaos
- lets SQL and dashboard logic mature first

### Assumption 2: One Currency in MVP

The MVP assumes one currency, such as TRY or USD.

Why:

- avoids FX conversion complexity
- keeps financial comparison clean

Future version can add currency conversion.

### Assumption 3: Annual Periods First

The MVP uses yearly reporting periods.

Why:

- simpler period-over-period comparison
- easier financial statement alignment

Future version can support quarters and months.

### Assumption 4: Same Metrics Across Companies

Each company has the same 8 core metrics.

Why:

- clean comparison
- reliable dashboard design

Real reports may require mapping and exceptions.

## Key Risks

## Risk 1: PDF Extraction Is Messy

PDF tables often break because of:

- merged cells
- multi-line headers
- scanned pages
- footnotes
- currency/unit notes
- table continuation across pages

Mitigation:

- do not start with PDF extraction
- add conversion logs
- keep confidence scores
- manually validate extracted values

## Risk 2: Metric Definitions Vary

Different companies may use different labels for similar metrics.

Example:

- sales
- net sales
- revenue
- operating revenue

Mitigation:

- maintain metric mapping dictionary
- keep raw labels
- document standardization rules

## Risk 3: Unit and Currency Confusion

Financial reports often use:

- actual values
- thousands
- millions
- local currency
- USD equivalents

Mitigation:

- store unit separately
- normalize values carefully
- avoid multi-currency comparison in MVP

## Risk 4: AI Hallucination

LLMs can produce plausible but incorrect extraction or summaries.

Mitigation:

- never use AI output without source fields
- validate extracted values
- include confidence scores
- restrict executive summary to final mart data

## Risk 5: Dashboard Misleads Without Context

A dashboard may show growth but hide cash flow weakness or debt pressure.

Mitigation:

- include profitability, debt, cash, and risk pages
- explain limitations
- add metric definitions

## Risk 6: Overengineering

The project can become too complex if too many tools are added early.

Examples of premature complexity:

- vector database
- agents
- cloud orchestration
- APIs
- web app
- advanced ML

Mitigation:

- complete MVP first
- add features only when they serve the business story

## Limitations of MVP

- Uses synthetic sample data unless real documents are added.
- Covers only 3 companies and 2 periods.
- Uses only 8 financial metrics.
- Does not perform FX conversion.
- Does not provide investment advice.
- Does not fully automate complex scanned PDF extraction.
- Risk keyword count is only a directional signal.

## Future Improvements

Possible future improvements:

- Real annual report ingestion
- Excel financial statement parsing
- PostgreSQL migration
- dbt transformation layer
- Power BI dashboard
- LLM-assisted extraction with human review
- Document-level source citations
- FX normalization
- Multi-period trend analysis
- Sector benchmarking
- GitHub Actions pipeline

## Professional Positioning

Limitations are not weakness. They show that the project owner understands the boundary between demo, MVP, and production system.
