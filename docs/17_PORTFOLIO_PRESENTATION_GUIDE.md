# 17 - Portfolio Presentation Guide

## Purpose

This document explains how to present the project on GitHub, LinkedIn, and job interviews.

## GitHub Positioning

Use this headline:

> AI-Assisted Financial Intelligence Pipeline: From Messy Financial Documents to Executive Analytics

## Short Description

```text
An end-to-end analytics engineering project that converts messy financial inputs into structured financial metrics, SQL KPI models, dashboard-ready tables, validation reports, and executive summaries.
```

## What Makes This Project Strong

This project is stronger than a basic dashboard because it includes:

- messy input problem
- data modeling
- SQL metric logic
- validation plan
- dashboard-ready mart table
- executive storytelling
- AI-assisted document processing concept

## What Not to Say

Do not say:

```text
I built an AI that analyzes companies automatically.
```

That sounds exaggerated.

Say:

```text
I built an analytics pipeline enhanced with AI-assisted document processing. The core value is standardized financial metrics, SQL modeling, validation, and executive reporting.
```

## Interview Explanation: 60 Seconds

```text
This project solves a realistic finance analytics problem: financial data often comes from messy documents, not clean CSVs.

I designed a pipeline that first standardizes financial metrics, loads them into a SQLite analytical model, calculates KPIs with SQL, creates a dashboard-ready mart table, validates the data, and generates an executive summary.

The MVP uses synthetic data to prove the pipeline, and the architecture is designed to later support real PDF, Excel, and investor presentation parsing.

My focus was not only visualization. I wanted to show the full path from raw source to business decision.
```

## Interview Explanation: Technical Deep Dive

Mention these points:

1. I defined a clear metric dictionary.
2. I modeled data with dimensions and fact tables.
3. I used SQL to calculate growth, margins, debt ratios, and peer rankings.
4. I created a mart table with one row per company-period.
5. I added validation checks for missing metrics, duplicates, numeric issues, and business rules.
6. I separated raw, processed, extracted, and final data zones.
7. I documented limitations and future improvements.

## LinkedIn Post Draft

```text
Most analytics projects start with a clean CSV.

But in real business life, especially in finance, the data often lives inside PDFs, Excel files, annual reports, investor presentations, and management commentary.

I started building an AI-assisted financial intelligence pipeline that focuses on the full analytics path:

messy financial source → standardized metrics → SQL model → dashboard-ready table → validation report → executive summary

The goal is not just to create a dashboard.
The goal is to show how financial information becomes decision-ready analytics.

Stack:
Python, SQL, SQLite, pandas, dashboard-ready data modeling, Markdown reporting, AI-assisted document processing.

MVP scope:
3 companies, 2 periods, 8 financial metrics, KPI modeling, validation, and executive reporting.
```

## GitHub README Preview Sections

The README should include:

- Project overview
- Business problem
- Architecture diagram
- Data model
- Metrics dictionary
- SQL logic
- Validation process
- Dashboard screenshots
- Executive summary sample
- Limitations
- Future work

## Portfolio Screenshots to Add

1. Project folder structure
2. Data model diagram
3. SQL KPI query screenshot
4. Validation report screenshot
5. Dashboard overview screenshot
6. Executive summary screenshot

## Common Interview Questions

### Q1: Why did you start with synthetic data?

Answer:

```text
Because I wanted to prove the analytical model, SQL logic, validation rules, and dashboard structure before dealing with unpredictable PDF extraction. This is a controlled MVP strategy.
```

### Q2: How do you calculate revenue growth?

Answer:

```text
I calculate it as current period revenue minus previous period revenue divided by previous period revenue. In SQL, I use a window function with lag() partitioned by company and ordered by period_sort_order.
```

### Q3: How do you prevent wrong extracted values from reaching the dashboard?

Answer:

```text
Each metric includes extraction method, confidence score, source document, and validation status. The validation layer checks completeness, duplicates, numeric quality, and business logic before data is used in final mart tables.
```

### Q4: What would you improve next?

Answer:

```text
I would add real annual report ingestion, document conversion, table extraction, manual review workflow, and later migrate the model to PostgreSQL or dbt if the transformation layer grows.
```

## Final Positioning

This project should make you look like someone who understands not only dashboards, but also data quality, metric modeling, business context, and analytical storytelling.
