# 09 - SQL Modeling Guide

## Purpose

This document defines how SQL should be used in the project. SQL is not only a technical layer; it is where business logic becomes explicit and reviewable.

## SQL Folder Structure

```text
sql/
├── 01_schema.sql
├── 02_insert_sample_data.sql
├── 03_financial_kpis.sql
├── 04_peer_comparison.sql
└── 05_mart_company_financial_performance.sql
```

## SQL Style Rules

- Use snake_case.
- Use descriptive CTE names.
- Add comments for business logic.
- Avoid unnecessary nested subqueries.
- Use `nullif()` or safe division logic when dividing.
- Keep one major purpose per SQL file.
- Define the grain of every output.

## Example KPI Logic

### Gross Margin %

```sql
-- Business meaning:
-- Gross margin measures how much revenue remains after direct costs.
-- Formula: gross_profit / revenue * 100

select
    company_name,
    period_label,
    round(gross_profit * 100.0 / nullif(revenue, 0), 2) as gross_margin_pct
from financial_metric_pivot;
```

### Revenue Growth %

```sql
-- Business meaning:
-- Revenue growth compares current period revenue against previous period revenue.

with revenue_by_period as (
    select
        company_name,
        period_label,
        period_sort_order,
        revenue,
        lag(revenue) over (
            partition by company_name
            order by period_sort_order
        ) as previous_revenue
    from financial_metric_pivot
)

select
    company_name,
    period_label,
    round(
        (revenue - previous_revenue) * 100.0 / nullif(previous_revenue, 0),
        2
    ) as revenue_growth_pct
from revenue_by_period;
```

## Required Model: financial_metric_pivot

Before KPI calculation, the long metric table should be pivoted to one row per company and period.

### Grain

```text
one row per company + period
```

### Output Columns

- company_name
- period_label
- period_sort_order
- revenue
- gross_profit
- operating_profit
- net_income
- total_assets
- total_debt
- cash
- operating_cash_flow

## Required Model: mart_company_financial_performance

This is the final dashboard-ready table.

### Grain

```text
one row per company + period
```

### Required KPIs

- revenue_growth_pct
- gross_margin_pct
- operating_margin_pct
- net_margin_pct
- debt_to_assets_pct
- cash_to_debt_pct
- risk_keyword_count

## Peer Comparison Queries

The project should include rankings such as:

- Top company by revenue growth
- Top company by net margin
- Highest debt to assets
- Highest cash to debt
- Highest risk keyword count

## SQL Testing Ideas

Basic sanity checks:

```sql
-- Count rows by company and period
select company_name, period_label, count(*)
from mart_company_financial_performance
group by company_name, period_label;
```

```sql
-- Check missing revenue values
select *
from mart_company_financial_performance
where revenue is null;
```

```sql
-- Check impossible cash/assets relationship
select *
from mart_company_financial_performance
where cash > total_assets;
```

## Common SQL Mistakes to Avoid

### Mistake 1: Dividing by zero

Always use `nullif(denominator, 0)`.

### Mistake 2: Calculating growth without period order

Do not order by string labels alone if labels can be inconsistent. Use `period_sort_order`.

### Mistake 3: Mixing metric grain

Do not join company-period metrics to document-level risk rows without aggregating risk first.

### Mistake 4: Hiding logic in BI tool

Do not calculate all important KPIs only in Power BI. Keep core KPI logic in SQL.

## Portfolio Review Standard

A reviewer should be able to open the SQL files and understand:

- what each query produces
- why each KPI matters
- how each KPI is calculated
- what the output grain is
