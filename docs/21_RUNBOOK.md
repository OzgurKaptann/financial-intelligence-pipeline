# 21 - Runbook

## Purpose

This runbook explains the expected way to run the project once implementation begins.

## Initial Setup

```bash
git clone <repo-url>
cd financial-intelligence-pipeline
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Expected MVP Run Order

## Step 1: Generate Synthetic Data

```bash
python src/synthetic_data_generator.py
```

Expected output:

```text
data/synthetic/synthetic_financial_metrics.csv
```

## Step 2: Create Database and Load Data

```bash
python src/database_loader.py
```

Expected output:

```text
data/final/financial_intelligence.sqlite
```

## Step 3: Run KPI SQL

Depending on implementation, either:

```bash
python src/financial_metrics.py
```

or run SQL files directly against SQLite.

Expected output:

```text
mart_company_financial_performance
```

## Step 4: Export Dashboard Mart

```bash
python src/financial_metrics.py --export
```

Expected output:

```text
data/final/mart_company_financial_performance.csv
```

## Step 5: Run Validation

```bash
python src/validation.py
```

Expected output:

```text
reports/validation_report.md
```

## Step 6: Generate Executive Summary

```bash
python src/report_generator.py
```

Expected output:

```text
reports/executive_summary.md
```

## Step 7: Build Dashboard

Load this file into Power BI, Tableau, or Metabase:

```text
data/final/mart_company_financial_performance.csv
```

## Troubleshooting

### Problem: Missing synthetic CSV

Run:

```bash
python src/synthetic_data_generator.py
```

### Problem: Database not found

Run:

```bash
python src/database_loader.py
```

### Problem: KPI query fails

Check:

- schema exists
- fact table has data
- metric names match dictionary
- SQL file path is correct

### Problem: Dashboard columns missing

Check:

- mart table SQL ran successfully
- final CSV was exported after KPI model creation

### Problem: Validation report shows missing metrics

Check whether every company-period has all 8 required metrics.

## Clean Rebuild

To rebuild from scratch:

```bash
rm data/final/financial_intelligence.sqlite
rm data/final/mart_company_financial_performance.csv
python src/synthetic_data_generator.py
python src/database_loader.py
python src/financial_metrics.py --export
python src/validation.py
python src/report_generator.py
```

## Runbook Principle

A portfolio reviewer should be able to reproduce the MVP without asking the author for hidden setup steps.
