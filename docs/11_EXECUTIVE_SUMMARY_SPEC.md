# 11 - Executive Summary Specification

## Purpose

The executive summary turns the final analytics table into a concise business narrative. It should be short, factual, and tied directly to calculated metrics.

## Output File

```text
reports/executive_summary.md
```

## Data Source

The summary must use:

```text
mart_company_financial_performance
```

Optional supporting source:

```text
risk_keyword_summary
```

Do not generate summary claims from unvalidated raw extraction candidates.

## Summary Structure

The report should include:

1. Title
2. Reporting scope
3. Key highlights
4. Growth analysis
5. Profitability analysis
6. Balance sheet risk
7. Cash position
8. Risk commentary
9. Recommended follow-up questions
10. Limitations

## Example Structure

```md
# Executive Summary

## Scope

This summary covers 3 companies across 2 reporting periods using 8 standardized financial metrics.

## Key Highlights

- Company A recorded the strongest revenue growth.
- Company B delivered the highest net margin.
- Company C showed the highest debt-to-assets ratio.

## Growth Analysis

...

## Profitability Analysis

...

## Balance Sheet Risk

...

## Recommended Follow-Up Questions

1. Is revenue growth supported by operating cash flow?
2. Is debt increasing faster than assets?
3. Which cost categories are pressuring margins?
```

## Tone Guidelines

The tone should be:

- executive
- concise
- analytical
- cautious where data is limited
- clear about assumptions

Avoid:

- hype
- investment advice
- unsupported claims
- hallucinated causal explanations

## Claim Rules

Every claim must be grounded in a metric.

Allowed:

```text
Company A has the highest revenue growth at 18.4%.
```

Not allowed:

```text
Company A is clearly the best investment.
```

Allowed:

```text
Company C has a higher debt-to-assets ratio than peers, which may require closer review.
```

Not allowed:

```text
Company C is financially unstable.
```

## Recommended Automated Insights

The report generator can calculate:

- company with highest revenue growth
- company with lowest revenue growth
- company with highest net margin
- company with lowest net margin
- company with highest debt_to_assets_pct
- company with lowest cash_to_debt_pct
- company with highest risk_keyword_count

## Limitations Section

The summary must include limitations such as:

- MVP uses synthetic sample data unless real documents are added.
- Only 3 companies and 2 periods are analyzed.
- No FX conversion is performed unless implemented.
- Risk keyword count is a signal, not a full risk model.
- Financial statement definitions may vary across companies.

## Acceptance Criteria

The executive summary is acceptable when:

- It is generated from final mart data.
- It contains no unsupported claims.
- It identifies top growth, profitability, debt, and cash signals.
- It includes limitations.
- It is readable by a finance or business stakeholder.
