# 08 - Document Ingestion and Extraction Strategy

## Purpose

This document explains how the project should eventually handle real financial documents. The MVP should not start here. Real document extraction should be added after the synthetic pipeline works.

## Supported Document Types

Future versions can support:

- PDF annual reports
- Excel financial statements
- PowerPoint investor presentations
- Word documents
- HTML reports
- Markdown/text files

## Ingestion Phases

## Phase 1: Synthetic Input

Use structured synthetic CSV data.

Purpose:

- prove database model
- prove SQL logic
- prove validation logic
- prove reporting outputs

## Phase 2: Document Conversion

Convert documents into Markdown/text.

Expected output:

```text
data/processed_markdown/company_period_document.md
```

This phase does not extract financial metrics yet. It only converts documents into an easier-to-process format.

## Phase 3: Candidate Extraction

Extract candidate metrics from converted text or tables.

Possible extraction methods:

- manual extraction
- regex pattern matching
- table parsing
- LLM-assisted extraction
- hybrid approach

## Phase 4: Standardization

Map raw metric labels to standard metric names.

Example:

| Raw Label | Standard Metric |
|---|---|
| Net Sales | revenue |
| Sales Revenue | revenue |
| Profit for the Period | net_income |
| Cash and Cash Equivalents | cash |

## Phase 5: Validation

Validate extracted values before loading into final tables.

## Extraction Methods

### 1. Manual Extraction

Best for first real-document version.

Pros:

- high trust
- easy to explain
- good for small MVP

Cons:

- not scalable

Recommended use:

- first real report integration
- benchmark dataset creation

### 2. Regex Extraction

Useful for recurring text patterns.

Pros:

- transparent
- fast
- testable

Cons:

- brittle when document format changes

### 3. Table Parsing

Useful for financial statements in PDF/Excel.

Pros:

- closer to source tables
- structured output

Cons:

- PDF tables often break
- multi-line headers cause errors

### 4. LLM-Assisted Extraction

Useful for management commentary or ambiguous labels.

Pros:

- flexible
- handles language variation
- useful for summaries

Cons:

- must be validated
- can hallucinate
- must include source traceability

## Recommended Strategy

Do not rely on one extraction method.

Use this hierarchy:

1. Excel table values if available
2. PDF table parsing
3. Regex on converted Markdown
4. LLM-assisted extraction
5. Manual review for low-confidence values

## Confidence Score Design

Suggested scale:

| Score | Meaning |
|---:|---|
| 1.00 | Synthetic or manually verified |
| 0.90 - 0.99 | Extracted from clean structured table |
| 0.75 - 0.89 | Extracted from text with strong pattern match |
| 0.50 - 0.74 | LLM-assisted or ambiguous extraction |
| < 0.50 | Should not be used without review |

## Source Traceability

Every extracted metric must include:

- source document
- page number or section if available
- raw label
- raw value
- standardized metric name
- extraction method
- confidence score

## Common Real-World Issues

### 1. Different Units

One report may say:

```text
Amounts are expressed in thousands of TRY.
```

Another may say:

```text
TRY million
```

The pipeline must store the unit and normalize values carefully.

### 2. Different Currency

Never compare values across different currencies unless an FX conversion layer is explicitly added.

### 3. Restated Financials

A company may restate prior period numbers. The source document and version must be kept.

### 4. Consolidated vs Standalone Statements

Consolidated and standalone reports are not the same. The source type must be documented.

### 5. OCR Errors

Scanned PDFs may produce incorrect numbers. OCR should not be trusted without validation.

### 6. Negative Cash Flow

Negative operating cash flow can be legitimate. Validation should not blindly reject negative values.

## Extraction Acceptance Criteria

A real extracted metric can be used in final analytics only when:

- metric name is standardized
- value is numeric
- currency is known
- unit is known
- source is documented
- confidence score is acceptable
- validation status is passed or reviewed

## MVP Warning

Do not build the extraction engine before the SQL and reporting workflow is complete. A broken extraction layer will distract from the main portfolio value.
