"""
document_converter.py

Phase 3 — MarkItDown document ingestion layer.

Converts raw financial documents from data/raw_documents/ into Markdown files
under data/processed_markdown/ using the Microsoft MarkItDown library.

This module does NOT extract financial metrics. It only converts source documents
to clean Markdown text so that a future extraction phase can parse them.

Supported formats: .pdf .docx .pptx .xlsx .xls .csv .html .txt .md
"""

import csv
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from markitdown import MarkItDown

# ---------------------------------------------------------------------------
# Paths — all resolved relative to this file so the script is location-independent
# ---------------------------------------------------------------------------
_SRC_DIR = Path(__file__).parent
_PROJECT_ROOT = _SRC_DIR.parent
RAW_DOCUMENTS_DIR = _PROJECT_ROOT / "data" / "raw_documents"
PROCESSED_MARKDOWN_DIR = _PROJECT_ROOT / "data" / "processed_markdown"
MANIFEST_PATH = PROCESSED_MARKDOWN_DIR / "conversion_manifest.csv"

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv", ".html", ".txt", ".md"}

MANIFEST_FIELDNAMES = [
    "source_file",
    "source_path",
    "output_file",
    "output_path",
    "file_extension",
    "conversion_status",
    "error_message",
    "converted_at",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _output_path(source_path: Path) -> Path:
    """Return the Markdown output path for a given source file."""
    return PROCESSED_MARKDOWN_DIR / (source_path.stem + ".md")


def _convert_file(converter: MarkItDown, source_path: Path) -> dict:
    """
    Convert a single file to Markdown.

    Returns a manifest row dict with conversion_status = 'success' or 'error'.
    """
    output_path = _output_path(source_path)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    row: dict = {
        "source_file": source_path.name,
        "source_path": str(source_path),
        "output_file": output_path.name,
        "output_path": str(output_path),
        "file_extension": source_path.suffix.lower(),
        "conversion_status": "",
        "error_message": "",
        "converted_at": timestamp,
    }

    try:
        result = converter.convert(str(source_path))
        markdown_text = result.text_content or ""
        output_path.write_text(markdown_text, encoding="utf-8")
        row["conversion_status"] = "success"
        logger.info("  converted  %s  →  %s  (%d chars)", source_path.name, output_path.name, len(markdown_text))
    except Exception as exc:  # noqa: BLE001
        row["conversion_status"] = "error"
        row["error_message"] = str(exc)
        logger.error("  FAILED     %s  —  %s", source_path.name, exc)

    return row


def _collect_source_files(directory: Path) -> list[Path]:
    """Return supported files from directory, sorted alphabetically."""
    files = []
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.name != ".gitkeep":
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(path)
            else:
                logger.warning("  skipped    %s  (unsupported extension: %s)", path.name, path.suffix)
    return files


def _write_manifest(rows: list[dict]) -> None:
    """Write or overwrite the conversion manifest CSV."""
    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Manifest written → %s  (%d rows)", MANIFEST_PATH, len(rows))


def run_conversion() -> list[dict]:
    """
    Main entry point.

    Scans data/raw_documents/, converts each supported file to Markdown,
    writes outputs to data/processed_markdown/, and produces a manifest CSV.

    Idempotent — re-running overwrites previous outputs safely.
    """
    PROCESSED_MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Phase 3 — MarkItDown Document Converter")
    logger.info("=" * 60)
    logger.info("Input  dir : %s", RAW_DOCUMENTS_DIR)
    logger.info("Output dir : %s", PROCESSED_MARKDOWN_DIR)

    if not RAW_DOCUMENTS_DIR.exists():
        logger.error("Input directory not found: %s", RAW_DOCUMENTS_DIR)
        sys.exit(1)

    source_files = _collect_source_files(RAW_DOCUMENTS_DIR)

    if not source_files:
        logger.info("No supported documents found in %s", RAW_DOCUMENTS_DIR)
        logger.info("Place .pdf / .docx / .xlsx / .pptx / .csv / .html / .txt files there and re-run.")
        _write_manifest([])
        return []

    logger.info("Found %d document(s) to convert", len(source_files))
    logger.info("-" * 60)

    converter = MarkItDown()
    manifest_rows: list[dict] = []

    for source_path in source_files:
        row = _convert_file(converter, source_path)
        manifest_rows.append(row)

    logger.info("-" * 60)
    success_count = sum(1 for r in manifest_rows if r["conversion_status"] == "success")
    error_count = len(manifest_rows) - success_count
    logger.info("Done: %d succeeded, %d failed", success_count, error_count)

    _write_manifest(manifest_rows)
    logger.info("=" * 60)

    return manifest_rows


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_conversion()
