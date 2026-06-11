# 29 — MarkItDown Document Ingestion Plan

Phase 3 of the Financial Intelligence Pipeline.

---

## Why MarkItDown

Microsoft MarkItDown is an open-source Python library that converts common office
and document formats into clean Markdown text. It is chosen here because:

- **Single dependency, broad format support.** One `pip install markitdown[all]`
  covers PDF, DOCX, XLSX, PPTX, HTML, CSV, TXT, and more.
- **Plain text output.** Markdown is easy to inspect, diff, version, and feed into
  downstream parsing or LLM extraction steps.
- **No proprietary API required.** Conversion runs entirely locally — no data leaves
  the machine, which matters for potentially sensitive financial documents.
- **Simple Python API.** `MarkItDown().convert(path)` returns a result object with
  a `text_content` string. No configuration required for basic use.

---

## Where It Sits in the Pipeline

```
data/raw_documents/          ← raw financial PDFs, Excel reports, PPTX slides
        │
        ▼
src/document_converter.py    ← Phase 3: MarkItDown conversion (this phase)
        │
        ▼
data/processed_markdown/     ← one .md file per source document
        │
        ▼
[future] src/metric_extractor.py   ← Phase 4: parse Markdown → structured metrics
        │
        ▼
[existing] database_loader.py → SQLite / PostgreSQL → KPI models → dashboard
```

The converter is intentionally isolated. It does not touch the MVP SQLite pipeline,
the PostgreSQL loader, or Docker Compose.

---

## Supported File Formats

| Extension | Format | Notes |
|-----------|--------|-------|
| `.pdf` | PDF document | Requires `pdfminer.six` (included in `markitdown[all]`) |
| `.docx` | Word document | Requires `mammoth` |
| `.pptx` | PowerPoint presentation | Requires `python-pptx` |
| `.xlsx` | Excel workbook (modern) | Requires `openpyxl` |
| `.xls` | Excel workbook (legacy) | Requires `xlrd` |
| `.csv` | Comma-separated values | Built-in |
| `.html` | HTML page | Requires `beautifulsoup4` |
| `.txt` | Plain text | Built-in |
| `.md` | Markdown (pass-through) | Built-in |

Files with any other extension are skipped with a logged warning. No error is raised.

---

## Input / Output Folders

| Folder | Purpose | Committed to git |
|--------|---------|-----------------|
| `data/raw_documents/` | Place raw financial documents here before running the converter. Real documents must **not** be committed (see `.gitignore`). | `.gitkeep` only |
| `data/processed_markdown/` | Converted Markdown files land here, one per source document. Generated outputs are **not** committed. | `.gitkeep` only |

Both folders exist in the repository via `.gitkeep` files so the directory structure
is always present after a fresh clone, even before any documents are placed.

---

## How the Conversion Manifest Works

After each run, `src/document_converter.py` writes a summary CSV to:

```
data/processed_markdown/conversion_manifest.csv
```

Each row records one conversion attempt:

| Column | Description |
|--------|-------------|
| `source_file` | Filename of the original document |
| `source_path` | Full path to the source file |
| `output_file` | Filename of the generated Markdown file |
| `output_path` | Full path to the Markdown output |
| `file_extension` | Extension of the source file (lowercased) |
| `conversion_status` | `success` or `error` |
| `error_message` | Empty on success; exception message on error |
| `converted_at` | UTC timestamp of the conversion attempt |

The manifest is overwritten on every run (idempotent). It is excluded from git by
default. To share a sample manifest for demo purposes, `git add -f` it explicitly.

---

## Running the Converter

```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Place documents in data/raw_documents/ then run:
python src/document_converter.py
```

The script logs progress to stdout and writes the manifest CSV on completion.
Re-running is safe — output files are overwritten.

---

## Security and Privacy Note

Real financial documents (annual reports, earnings releases, internal spreadsheets)
often contain material non-public information. The following safeguards are in place:

- `data/raw_documents/*` is in `.gitignore`. Only `.gitkeep` is committed.
- `data/processed_markdown/*` is in `.gitignore`. Only `.gitkeep` is committed.
- `conversion_manifest.csv` is in `.gitignore` by default.
- **Never run `git add -A` or `git add .` without reviewing what is staged.**
- Conversion runs locally. No document content is sent to any external service.

---

## Current Limitation

**This phase only converts documents to Markdown text. It does not extract financial
metrics, company names, periods, or any structured data.**

The Markdown output is raw text. Tables from PDFs may not render as clean Markdown
tables — quality depends on the PDF's internal structure. Scanned/image-only PDFs
will produce minimal or empty output without an OCR step.

---

## Next Phase: Metric Extraction

Phase 4 will add `src/metric_extractor.py`, which will:

1. Read Markdown files from `data/processed_markdown/`.
2. Parse them for financial line items (revenue, net income, etc.).
3. Produce structured rows matching the data contract in `docs/05_DATA_CONTRACTS.md`.
4. Write results to `data/extracted/` for loading into the SQLite / PostgreSQL pipeline.

Extraction will initially use regex patterns and keyword matching. LLM-assisted
extraction (Claude API) is a later option once the regex baseline is established.
