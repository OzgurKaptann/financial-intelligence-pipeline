# 13 - Testing Strategy

## Purpose

Testing proves that the project is not just a collection of scripts. It shows that important logic is protected from silent errors.

## Testing Scope for MVP

The MVP should include lightweight tests for:

- metric extraction helpers
- data cleaning functions
- KPI calculations
- validation logic
- database loading assumptions

## Test Folder

```text
tests/
├── test_metric_extractor.py
├── test_financial_metrics.py
├── test_validation.py
└── test_database_loader.py
```

## Recommended Test Tool

Use `pytest`.

## Unit Test Ideas

### 1. Metric Name Standardization

Input:

```text
Net Sales
```

Expected output:

```text
revenue
```

Input:

```text
Profit for the Period
```

Expected output:

```text
net_income
```

### 2. Numeric Value Cleaning

Input:

```text
"1,250.5"
```

Expected output:

```text
1250.5
```

Input:

```text
"TRY 1.2 million"
```

Expected output depends on unit logic.

### 3. Safe Division

Input:

```text
numerator = 100
denominator = 0
```

Expected output:

```text
None or null-safe value
```

### 4. Margin Calculation

Input:

```text
revenue = 1000
gross_profit = 400
```

Expected output:

```text
40.0
```

### 5. Revenue Growth

Input:

```text
current_revenue = 1200
previous_revenue = 1000
```

Expected output:

```text
20.0
```

### 6. Completeness Check

A company-period missing one of eight required metrics should fail completeness validation.

## SQL Testing Ideas

SQLite queries can be tested by:

- creating a temporary database
- loading a small fixture dataset
- running SQL files
- comparing outputs

## Data Quality Test Ideas

| Test | Expected Result |
|---|---|
| all companies have all 8 metrics | pass |
| confidence_score between 0 and 1 | pass |
| no duplicate company-period-metric-source rows | pass |
| revenue not null | pass |
| cash <= total_assets | pass or warning |

## Tests Not Needed in MVP

Do not overbuild tests for:

- UI dashboard behavior
- cloud orchestration
- advanced PDF parsing
- LLM response quality

Add those later if the project grows.

## Testing Acceptance Criteria

The MVP testing layer is acceptable when:

- `pytest` runs successfully.
- Core financial calculation helpers are tested.
- Validation logic is tested.
- Data cleaning assumptions are tested.
- The tests are readable by a reviewer.

## Portfolio Message

Testing is not about showing off. It proves that financial metrics are calculated consistently and that future changes will not silently break the pipeline.
