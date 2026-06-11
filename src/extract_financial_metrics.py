"""
extract_financial_metrics.py

Phase 3.1 — Markdown to structured financial metrics extraction.

Reads Markdown files from data/processed_markdown/, applies deterministic
regex-based rules to extract company name, reporting period, and the eight
core financial metrics, then writes results to data/extracted/.

No LLM, no external APIs. Fully deterministic and idempotent.

Outputs
-------
data/extracted/extracted_financial_metrics.csv  — one row per metric extracted
data/extracted/extraction_manifest.csv          — one row per source file processed
"""

import csv
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SRC_DIR = Path(__file__).parent
_PROJECT_ROOT = _SRC_DIR.parent
PROCESSED_MARKDOWN_DIR = _PROJECT_ROOT / "data" / "processed_markdown"
EXTRACTED_DIR = _PROJECT_ROOT / "data" / "extracted"
METRICS_CSV = EXTRACTED_DIR / "extracted_financial_metrics.csv"
MANIFEST_CSV = EXTRACTED_DIR / "extraction_manifest.csv"

# ---------------------------------------------------------------------------
# Metric definitions — canonical name → list of label aliases accepted in text
# ---------------------------------------------------------------------------
METRIC_ALIASES: dict[str, list[str]] = {
    "revenue": [
        "revenue",
        "total revenue",
        "net revenue",
        "net sales",
        "sales",
        "turnover",
        "total sales",
    ],
    "gross_profit": [
        "gross profit",
        "gross income",
        "gross margin value",
    ],
    "operating_profit": [
        "operating profit",
        "operating income",
        "ebit",
        "operating earnings",
        "income from operations",
        "profit from operations",
    ],
    "net_income": [
        "net income",
        "net profit",
        "net earnings",
        "profit after tax",
        "net profit after tax",
        "earnings after tax",
        "bottom line",
    ],
    "total_assets": [
        "total assets",
        "assets total",
        "total asset",
    ],
    "total_debt": [
        "total debt",
        "total borrowings",
        "total liabilities",
        "financial debt",
        "interest bearing debt",
        "net debt",
        "borrowings",
        "long-term debt",
        "total financial debt",
    ],
    "cash": [
        "cash",
        "cash and cash equivalents",
        "cash & cash equivalents",
        "cash equivalents",
        "cash and equivalents",
        "liquid assets",
    ],
    "operating_cash_flow": [
        "operating cash flow",
        "cash flow from operations",
        "cash flow from operating activities",
        "net cash from operations",
        "net cash from operating activities",
        "operating activities",
    ],
}

# Pre-compile one pattern per canonical metric.
# Pattern: label (any alias) followed by optional colon/equals and a numeric value.
# Numeric value may have:  currency symbols  ($£€₺),  commas,  dots,  spaces,
#                          trailing K / M / B suffixes,  optional parentheses for negatives.
_NUMBER_RE = r"""
    (?:[$£€₺])?          # optional leading currency symbol
    \s*
    \(?                  # optional opening parenthesis (negative convention)
    (
        [\d]{1,3}        # first digit group
        (?:[,\s]\d{3})*  # optional comma/space-separated thousands groups
        (?:[.,]\d+)?     # optional decimal part
        |
        \d+(?:[.,]\d+)?  # plain number with optional decimal
    )
    \)?                  # optional closing parenthesis
    \s*
    (?:[KkMmBb]b?)?      # optional K / M / B suffix (ignored in normalisation for now)
"""

_LABEL_PATTERNS: dict[str, re.Pattern] = {}
for _canonical, _aliases in METRIC_ALIASES.items():
    # Escape each alias and join with | — longest-first so greedier match wins
    _sorted_aliases = sorted(_aliases, key=len, reverse=True)
    _alias_group = "|".join(re.escape(a) for a in _sorted_aliases)
    _LABEL_PATTERNS[_canonical] = re.compile(
        rf"(?:^|[\n\r])[ \t]*(?:{_alias_group})[ \t]*[:=][ \t]*{_NUMBER_RE}",
        re.IGNORECASE | re.VERBOSE | re.MULTILINE,
    )

# Pattern for company name:  "Company: <name>" or "Company Name: <name>"
_COMPANY_RE = re.compile(
    r"(?:^|[\n\r])[ \t]*company(?:\s+name)?[ \t]*:[ \t]*(.+)",
    re.IGNORECASE | re.MULTILINE,
)

# Pattern for reporting period:  "Period: FY2025"  or  "Reporting Period: ..."
_PERIOD_RE = re.compile(
    r"(?:^|[\n\r])[ \t]*(?:reporting\s+)?period[ \t]*:[ \t]*(.+)",
    re.IGNORECASE | re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Output column definitions
# ---------------------------------------------------------------------------
METRICS_FIELDNAMES = [
    "source_file",
    "company_name",
    "period_label",
    "metric_name",
    "metric_value",
    "extraction_status",
    "error_message",
    "extracted_at",
]

MANIFEST_FIELDNAMES = [
    "source_file",
    "company_name",
    "period_label",
    "metrics_found",
    "metrics_missing",
    "total_rows_written",
    "extraction_status",
    "error_message",
    "extracted_at",
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
# Helpers
# ---------------------------------------------------------------------------

def _clean_number(raw: str) -> float:
    """
    Normalise a raw numeric string to a float.

    Handles:
    - Comma thousands separators:  1,000,000  →  1000000.0
    - Space thousands separators:  1 000 000  →  1000000.0
    - European decimals:           1.000,50   →  1000.5
    - Plain integers and decimals
    """
    s = raw.strip().replace(" ", "")
    # Detect European format: has dots for thousands and comma for decimal
    if re.search(r"\d\.\d{3},", s):
        s = s.replace(".", "").replace(",", ".")
    else:
        # Standard format — remove comma thousands separator
        s = s.replace(",", "")
    return float(s)


def _extract_text_field(pattern: re.Pattern, text: str) -> str | None:
    """Return the first capture group match, stripped, or None."""
    m = pattern.search(text)
    if m:
        return m.group(1).strip()
    return None


def _extract_metric(canonical: str, text: str) -> float | None:
    """Return the first numeric match for a metric alias, or None."""
    m = _LABEL_PATTERNS[canonical].search(text)
    if not m:
        return None
    try:
        return _clean_number(m.group(1))
    except (ValueError, AttributeError):
        return None


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Per-file extraction
# ---------------------------------------------------------------------------

def extract_from_markdown(md_path: Path) -> tuple[list[dict], dict]:
    """
    Extract structured metrics from one Markdown file.

    Returns
    -------
    rows     : list of metric row dicts (one per found metric)
    manifest : single manifest row dict describing the overall result
    """
    timestamp = _now_utc()
    source_file = md_path.name

    manifest: dict = {
        "source_file": source_file,
        "company_name": "",
        "period_label": "",
        "metrics_found": "",
        "metrics_missing": "",
        "total_rows_written": 0,
        "extraction_status": "",
        "error_message": "",
        "extracted_at": timestamp,
    }

    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        manifest["extraction_status"] = "error"
        manifest["error_message"] = f"Cannot read file: {exc}"
        logger.error("  FAILED  %s  —  %s", source_file, exc)
        return [], manifest

    company = _extract_text_field(_COMPANY_RE, text)
    period = _extract_text_field(_PERIOD_RE, text)

    manifest["company_name"] = company or ""
    manifest["period_label"] = period or ""

    if not company or not period:
        missing_fields = []
        if not company:
            missing_fields.append("company")
        if not period:
            missing_fields.append("period")
        manifest["extraction_status"] = "failed"
        manifest["error_message"] = f"Missing required fields: {', '.join(missing_fields)}"
        logger.warning(
            "  FAILED  %s  —  missing: %s", source_file, ", ".join(missing_fields)
        )
        return [], manifest

    rows: list[dict] = []
    found: list[str] = []
    missing: list[str] = []

    for canonical in METRIC_ALIASES:
        value = _extract_metric(canonical, text)
        if value is not None:
            rows.append({
                "source_file": source_file,
                "company_name": company,
                "period_label": period,
                "metric_name": canonical,
                "metric_value": value,
                "extraction_status": "success",
                "error_message": "",
                "extracted_at": timestamp,
            })
            found.append(canonical)
        else:
            missing.append(canonical)

    manifest["metrics_found"] = "|".join(found)
    manifest["metrics_missing"] = "|".join(missing)
    manifest["total_rows_written"] = len(rows)

    if not rows:
        manifest["extraction_status"] = "no_metrics"
        manifest["error_message"] = "Company and period found but no metric values matched"
        logger.warning("  NO METRICS  %s  (company=%s, period=%s)", source_file, company, period)
    else:
        manifest["extraction_status"] = "success"
        logger.info(
            "  extracted  %s  →  company=%s  period=%s  metrics=%d  missing=%d",
            source_file, company, period, len(found), len(missing),
        )
        if missing:
            logger.info("    missing metrics: %s", ", ".join(missing))

    return rows, manifest


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_extraction() -> None:
    """
    Entry point.

    Scans data/processed_markdown/ for .md files, extracts metrics from each,
    and writes extracted_financial_metrics.csv + extraction_manifest.csv.
    """
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Phase 3.1 — Markdown Metric Extractor")
    logger.info("=" * 60)
    logger.info("Input  dir : %s", PROCESSED_MARKDOWN_DIR)
    logger.info("Output dir : %s", EXTRACTED_DIR)

    if not PROCESSED_MARKDOWN_DIR.exists():
        logger.error("Processed Markdown directory not found: %s", PROCESSED_MARKDOWN_DIR)
        sys.exit(1)

    md_files = sorted(
        p for p in PROCESSED_MARKDOWN_DIR.iterdir()
        if p.is_file() and p.suffix == ".md" and p.name != ".gitkeep"
    )

    if not md_files:
        logger.info("No .md files found in %s", PROCESSED_MARKDOWN_DIR)
        logger.info("Run src/document_converter.py first to produce Markdown files.")
        _write_outputs([], [])
        return

    logger.info("Found %d Markdown file(s)", len(md_files))
    logger.info("-" * 60)

    all_rows: list[dict] = []
    all_manifest: list[dict] = []

    for md_path in md_files:
        rows, manifest = extract_from_markdown(md_path)
        all_rows.extend(rows)
        all_manifest.append(manifest)

    logger.info("-" * 60)
    success = sum(1 for m in all_manifest if m["extraction_status"] == "success")
    failed = len(all_manifest) - success
    logger.info(
        "Done: %d file(s) succeeded, %d failed, %d metric rows extracted",
        success, failed, len(all_rows),
    )

    _write_outputs(all_rows, all_manifest)
    logger.info("=" * 60)


def _write_outputs(rows: list[dict], manifest: list[dict]) -> None:
    with METRICS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=METRICS_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Metrics CSV  → %s  (%d rows)", METRICS_CSV, len(rows))

    with MANIFEST_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDNAMES)
        writer.writeheader()
        writer.writerows(manifest)
    logger.info("Manifest CSV → %s  (%d rows)", MANIFEST_CSV, len(manifest))


if __name__ == "__main__":
    run_extraction()
