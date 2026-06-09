# 18 - Project Backlog

## Purpose

This backlog turns the project into actionable work items.

## Epic 1: Repository Foundation

### Task 1.1: Create folder structure

**Priority:** P0

**Description:** Create standard project folders.

**Acceptance Criteria:**

- `data/`, `src/`, `sql/`, `notebooks/`, `dashboard/`, `reports/`, `tests/`, and `docs/` exist.

### Task 1.2: Create README

**Priority:** P0

**Acceptance Criteria:**

- README explains project overview, problem, architecture, metrics, and run instructions.

### Task 1.3: Create CLAUDE.md

**Priority:** P0

**Acceptance Criteria:**

- Claude behavior and project standards are documented.

## Epic 2: Synthetic Data Layer

### Task 2.1: Generate synthetic company data

**Priority:** P0

**Acceptance Criteria:**

- 3 companies
- 2 periods
- 8 metrics per company-period
- synthetic flag or clear source field

### Task 2.2: Validate synthetic data consistency

**Priority:** P0

**Acceptance Criteria:**

- gross_profit <= revenue warning rule satisfied or documented
- cash <= total_assets rule satisfied or documented
- all company-period combinations complete

## Epic 3: Database Layer

### Task 3.1: Create SQLite schema

**Priority:** P0

**Acceptance Criteria:**

- Dimension and fact tables exist.
- Foreign keys are defined.
- Duplicate prevention exists.

### Task 3.2: Build database loader

**Priority:** P0

**Acceptance Criteria:**

- Loader reads synthetic CSV.
- Loader populates dimensions and facts.
- Loader prints row counts.

## Epic 4: SQL Modeling

### Task 4.1: Create financial metric pivot

**Priority:** P0

**Acceptance Criteria:**

- One row per company-period.
- All 8 metrics are columns.

### Task 4.2: Calculate KPIs

**Priority:** P0

**Acceptance Criteria:**

- Growth and margin calculations work.
- Safe division is used.
- SQL comments explain formulas.

### Task 4.3: Create dashboard mart

**Priority:** P0

**Acceptance Criteria:**

- `mart_company_financial_performance` exists.
- It is dashboard-ready.

## Epic 5: Validation

### Task 5.1: Build validation script

**Priority:** P1

**Acceptance Criteria:**

- Missing values checked.
- Duplicates checked.
- Completeness checked.
- Business rules checked.

### Task 5.2: Generate validation report

**Priority:** P1

**Acceptance Criteria:**

- Markdown report created.
- Errors and warnings separated.

## Epic 6: Executive Reporting

### Task 6.1: Build report generator

**Priority:** P1

**Acceptance Criteria:**

- Reads final mart.
- Produces `reports/executive_summary.md`.
- Includes grounded insights and limitations.

## Epic 7: Dashboard

### Task 7.1: Build dashboard pages

**Priority:** P1

**Acceptance Criteria:**

- Executive overview page
- Profitability page
- Balance sheet risk page
- Risk commentary page

### Task 7.2: Add dashboard screenshots to README

**Priority:** P1

**Acceptance Criteria:**

- Screenshots added.
- README explains each page.

## Epic 8: Real Document Processing

### Task 8.1: Add document conversion module

**Priority:** P2

**Acceptance Criteria:**

- Converts raw documents to Markdown/text.
- Saves processing log.

### Task 8.2: Add metric extraction prototype

**Priority:** P2

**Acceptance Criteria:**

- Extracts at least 8 metrics from one real document or manually reviewed source.
- Includes confidence and source traceability.

## Epic 9: Portfolio Polish

### Task 9.1: Review project as hiring manager

**Priority:** P1

**Acceptance Criteria:**

- Weak points identified.
- README improved.
- Unnecessary complexity removed.

### Task 9.2: Create LinkedIn launch post

**Priority:** P2

**Acceptance Criteria:**

- Post explains business problem, stack, and project value.

## Priority Legend

| Priority | Meaning |
|---|---|
| P0 | Must have for MVP |
| P1 | Strongly improves portfolio value |
| P2 | Future enhancement |
| P3 | Optional polish |
