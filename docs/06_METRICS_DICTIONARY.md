# 06 - Metrics Dictionary

## Purpose

This document defines every metric used in the project. A metric without a definition is a risk.

## Core Financial Metrics

### 1. Revenue

**Standard name:** `revenue`

**Business meaning:** Total income generated from the company's primary business activities during the reporting period.

**Expected source labels:**

- Revenue
- Sales
- Net Sales
- Total Revenue
- Net Revenue

**Formula:**

```text
source reported value
```

**Validation notes:**

- Usually positive.
- Should be higher than gross profit.
- Must not be mixed across currencies.

---

### 2. Gross Profit

**Standard name:** `gross_profit`

**Business meaning:** Revenue minus cost of goods sold or cost of sales.

**Expected source labels:**

- Gross Profit
- Gross Income
- Revenue less Cost of Sales

**Formula:**

```text
revenue - cost_of_sales
```

or reported directly.

**Validation notes:**

- Usually less than revenue.
- Can be negative in distressed companies.

---

### 3. Operating Profit

**Standard name:** `operating_profit`

**Business meaning:** Profit generated from operations before interest and tax.

**Expected source labels:**

- Operating Profit
- Operating Income
- EBIT
- Profit from Operations

**Formula:**

```text
gross_profit - operating_expenses
```

or reported directly.

**Validation notes:**

- Can be negative.
- Should not be confused with EBITDA.

---

### 4. Net Income

**Standard name:** `net_income`

**Business meaning:** Profit after all expenses, interest, tax, and other items.

**Expected source labels:**

- Net Income
- Net Profit
- Profit for the Period
- Net Earnings

**Formula:**

```text
profit_after_tax
```

**Validation notes:**

- Can be negative.
- Should not be confused with operating profit.

---

### 5. Total Assets

**Standard name:** `total_assets`

**Business meaning:** Total resources controlled by the company.

**Expected source labels:**

- Total Assets
- Assets Total

**Formula:**

```text
current_assets + non_current_assets
```

or reported directly.

**Validation notes:**

- Usually positive.
- Should be greater than or equal to cash.

---

### 6. Total Debt

**Standard name:** `total_debt`

**Business meaning:** Total financial debt obligations.

**Expected source labels:**

- Total Debt
- Borrowings
- Financial Liabilities
- Short-term Debt + Long-term Debt

**Formula:**

```text
short_term_debt + long_term_debt
```

**Validation notes:**

- Definition must be documented.
- Do not mix all liabilities with financial debt unless explicitly intended.

---

### 7. Cash

**Standard name:** `cash`

**Business meaning:** Cash and cash equivalents available to the company.

**Expected source labels:**

- Cash
- Cash and Cash Equivalents
- Cash Position

**Formula:**

```text
source reported value
```

**Validation notes:**

- Should be non-negative in normal financial statements.
- Should be less than or equal to total assets.

---

### 8. Operating Cash Flow

**Standard name:** `operating_cash_flow`

**Business meaning:** Cash generated or used by core operations during the period.

**Expected source labels:**

- Operating Cash Flow
- Cash Flow from Operations
- Net Cash Provided by Operating Activities

**Formula:**

```text
source reported value
```

**Validation notes:**

- Can be negative.
- Should not be confused with free cash flow.

## Calculated KPIs

### Revenue Growth %

**Standard name:** `revenue_growth_pct`

**Formula:**

```text
(current_period_revenue - previous_period_revenue) / previous_period_revenue * 100
```

**Business meaning:** Measures top-line growth from one period to the next.

**Edge cases:**

- Previous period revenue is zero.
- Previous period is missing.

---

### Gross Margin %

**Standard name:** `gross_margin_pct`

**Formula:**

```text
gross_profit / revenue * 100
```

**Business meaning:** Measures profitability after direct costs.

---

### Operating Margin %

**Standard name:** `operating_margin_pct`

**Formula:**

```text
operating_profit / revenue * 100
```

**Business meaning:** Measures operating efficiency.

---

### Net Margin %

**Standard name:** `net_margin_pct`

**Formula:**

```text
net_income / revenue * 100
```

**Business meaning:** Measures final profitability after all expenses.

---

### Debt / Assets %

**Standard name:** `debt_to_assets_pct`

**Formula:**

```text
total_debt / total_assets * 100
```

**Business meaning:** Measures balance sheet leverage.

---

### Cash / Debt %

**Standard name:** `cash_to_debt_pct`

**Formula:**

```text
cash / total_debt * 100
```

**Business meaning:** Measures cash coverage relative to debt.

---

### Risk Keyword Count

**Standard name:** `risk_keyword_count`

**Formula:**

```text
count of predefined risk keywords detected in management commentary
```

**Risk keyword examples:**

- inflation
- currency
- interest rate
- liquidity
- debt
- regulation
- supply chain
- demand slowdown

## Metric Governance Rule

If a metric cannot be defined, sourced, validated, and explained, it should not be included in the dashboard.
