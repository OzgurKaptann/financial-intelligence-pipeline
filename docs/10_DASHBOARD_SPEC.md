# 10 - Dashboard Specification

## Dashboard Name

Financial Intelligence Dashboard

## Dashboard Purpose

The dashboard translates structured financial metrics into executive-level business insight. It should not be a random collection of charts. Every visual must answer a business question.

## Target Users

- CFO
- Finance manager
- Investment analyst
- Data analyst
- Hiring manager reviewing portfolio

## Data Source

Primary source:

```text
mart_company_financial_performance
```

Optional source:

```text
risk_keyword_summary
```

## Dashboard Grain

The primary analysis grain is:

```text
company + reporting period
```

## Page 1: Executive Overview

### Business Questions

- Which company is strongest overall?
- Which company is growing fastest?
- Which company has the biggest debt risk?
- Is profitability improving or weakening?

### KPI Cards

- Total Revenue
- Average Revenue Growth %
- Average Net Margin %
- Total Debt
- Total Cash
- Highest Risk Company

### Visuals

1. Revenue by Company
2. Revenue Growth % by Company
3. Net Margin % by Company
4. Debt / Assets % by Company
5. Cash / Debt % by Company

### Filters

- Period
- Company
- Sector if available
- Currency if multiple currencies are added later

## Page 2: Profitability Analysis

### Business Questions

- Which company converts revenue into profit best?
- Are margins consistent across companies?
- Is growth coming with margin pressure?

### Visuals

1. Revenue vs Net Income by Company
2. Gross Margin % by Company
3. Operating Margin % by Company
4. Net Margin % by Company
5. Margin trend by period

### Suggested Insight Text

The page should include a short note explaining that revenue growth alone is not enough. Profitability metrics show whether growth is efficient.

## Page 3: Balance Sheet Risk

### Business Questions

- Which company carries more debt relative to assets?
- Which company has stronger cash coverage?
- Is debt increasing faster than cash?

### Visuals

1. Debt / Assets % by Company
2. Cash / Debt % by Company
3. Total Debt by Period
4. Cash by Period
5. Debt vs Cash scatter plot

### Risk Signal Logic

A company should be highlighted if:

- debt_to_assets_pct is high
- cash_to_debt_pct is low
- net income is weak
- operating cash flow is negative

## Page 4: Risk and Management Commentary

### Business Questions

- Which companies mention more risk-related terms?
- Are risk mentions increasing?
- Which risk categories dominate?

### Visuals

1. Risk Keyword Count by Company
2. Risk Keyword Count by Period
3. Top Risk Categories
4. Keyword table with company and period

### Risk Keywords

Examples:

- inflation
- interest rate
- liquidity
- debt
- currency
- supply chain
- demand slowdown
- regulation

## Dashboard Design Rules

- Use clear titles.
- Avoid decorative visuals that do not answer a question.
- Use consistent number formats.
- Show percentages as percentages.
- Show financial values in the same unit.
- Add tooltips with metric definitions.
- Keep one main message per page.

## Suggested Color Logic

Use neutral and professional colors.

Possible semantic color usage:

- Positive growth: green tone
- Risk/debt: red or amber tone
- Neutral financial values: blue or gray tone
- Background: light neutral

Do not overuse colors. The dashboard should look like a finance/BI product, not a social media infographic.

## Required Dashboard Output Screenshots

For GitHub README:

- Executive Overview screenshot
- Profitability Analysis screenshot
- Balance Sheet Risk screenshot
- Risk Commentary screenshot

## Dashboard Acceptance Criteria

Dashboard is acceptable when:

- It uses the final mart table.
- It does not require manual reshaping inside the BI tool.
- Every KPI has a definition.
- Every visual answers a business question.
- A reviewer can understand the story without asking for explanation.

## Portfolio Story

When presenting this dashboard, say:

> The dashboard is not the starting point of the project. It is the final consumption layer of a pipeline that starts from messy financial inputs, standardizes metrics, validates data quality, and models KPIs in SQL.
