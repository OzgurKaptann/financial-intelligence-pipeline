# 23 - Non-Markdown Files to Create Later

## Purpose

The current package focuses on Markdown planning files. During implementation, the project should also include code, SQL, configuration, and data files.

## Root Files

```text
requirements.txt
.gitignore
```

## Python Files

```text
src/config.py
src/document_converter.py
src/synthetic_data_generator.py
src/metric_extractor.py
src/data_cleaner.py
src/database_loader.py
src/financial_metrics.py
src/validation.py
src/report_generator.py
```

## SQL Files

```text
sql/01_schema.sql
sql/02_insert_sample_data.sql
sql/03_financial_kpis.sql
sql/04_peer_comparison.sql
sql/05_mart_company_financial_performance.sql
```

## Notebook Files

```text
notebooks/01_document_conversion.ipynb
notebooks/02_metric_extraction.ipynb
notebooks/03_financial_analysis.ipynb
notebooks/04_dashboard_export.ipynb
```

## Data Files

```text
data/synthetic/synthetic_financial_metrics.csv
data/final/financial_intelligence.sqlite
data/final/mart_company_financial_performance.csv
```

## Report Files

```text
reports/executive_summary.md
reports/validation_report.md
reports/extraction_quality_report.md
```

## Test Files

```text
tests/test_metric_extractor.py
tests/test_financial_metrics.py
tests/test_validation.py
tests/test_database_loader.py
```

## Recommended requirements.txt

```text
pandas
numpy
pytest
jupyter
python-dotenv
```

Optional later:

```text
markitdown
openpyxl
pymupdf
```

## Recommended .gitignore

```text
.venv/
__pycache__/
*.pyc
.env
.ipynb_checkpoints/
data/raw_documents/*
data/final/*.sqlite
.DS_Store
```

Important: if public raw documents are used and legally shareable, this rule can be adjusted. For private documents, never commit them.
