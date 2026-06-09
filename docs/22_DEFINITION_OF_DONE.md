# 22 - Definition of Done

## Purpose

This document defines what “done” means. Without this, the project can grow forever without becoming portfolio-ready.

## MVP Done Criteria

The MVP is done when all items below are complete.

## 1. Repository Structure

- [ ] Folder structure is clean.
- [ ] README exists.
- [ ] CLAUDE.md exists.
- [ ] Docs folder exists.
- [ ] SQL folder exists.
- [ ] Src folder exists.
- [ ] Reports folder exists.
- [ ] Dashboard folder exists.

## 2. Synthetic Data

- [ ] Synthetic financial metrics CSV exists.
- [ ] Data includes 3 companies.
- [ ] Data includes 2 periods.
- [ ] Data includes 8 required metrics.
- [ ] Data is clearly labeled as synthetic.

## 3. Database

- [ ] SQLite schema exists.
- [ ] Dimension tables exist.
- [ ] Fact tables exist.
- [ ] Data loader works.
- [ ] Duplicate prevention exists.

## 4. SQL Modeling

- [ ] Financial metrics are pivoted correctly.
- [ ] Revenue growth is calculated.
- [ ] Gross margin is calculated.
- [ ] Operating margin is calculated.
- [ ] Net margin is calculated.
- [ ] Debt / assets is calculated.
- [ ] Cash / debt is calculated.
- [ ] Safe division is used.

## 5. Dashboard Mart

- [ ] `mart_company_financial_performance` exists.
- [ ] Grain is one row per company-period.
- [ ] Final CSV export exists.
- [ ] BI tool can read the file.

## 6. Validation

- [ ] Validation script exists.
- [ ] Validation report exists.
- [ ] Missing values checked.
- [ ] Duplicates checked.
- [ ] Completeness checked.
- [ ] Business rules checked.

## 7. Executive Summary

- [ ] Summary generator exists.
- [ ] Markdown summary exists.
- [ ] Claims are grounded in final mart data.
- [ ] Limitations are included.

## 8. Dashboard

- [ ] Executive Overview page exists.
- [ ] Profitability Analysis page exists.
- [ ] Balance Sheet Risk page exists.
- [ ] Risk Commentary page exists or planned.
- [ ] Screenshots are added to README.

## 9. Portfolio Polish

- [ ] README has clear project explanation.
- [ ] Architecture is documented.
- [ ] Metrics dictionary is documented.
- [ ] Limitations are documented.
- [ ] Future improvements are documented.
- [ ] Repo can be understood in 2 minutes.

## Not Done If

The project is not done if:

- It only contains notebooks.
- It has no validation report.
- KPI logic is hidden only inside a BI tool.
- Synthetic data is presented as real.
- README does not explain the business problem.
- Dashboard does not answer clear questions.
- SQL logic cannot be explained in an interview.

## Final Quality Bar

The project is ready to publish when you can answer these questions without looking at the code:

1. What business problem does this solve?
2. What is the grain of the fact table?
3. What is the grain of the mart table?
4. How is revenue growth calculated?
5. How are margins calculated?
6. What validation checks exist?
7. What are the limitations?
8. What would you improve next?
