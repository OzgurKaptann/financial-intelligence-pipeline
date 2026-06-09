"""
report_generator.py

Reads the dashboard mart CSV, derives key analytical findings, and writes
a business-readable executive summary in Markdown.

IMPORTANT: All findings in this report are based on SYNTHETIC SAMPLE DATA.
They do not represent real company performance, real financial results, or
real investment signals. This report demonstrates the pipeline's output
format and analytical logic only.

Output: reports/executive_summary.md
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import MART_CSV, PROJECT_ROOT, REPORTS_DIR

EXECUTIVE_SUMMARY_PATH = REPORTS_DIR / "executive_summary.md"


# =============================================================================
# Step 1 — Load
# =============================================================================

def load_mart_csv() -> pd.DataFrame:
    """Load the mart CSV. Raises FileNotFoundError if it does not exist."""
    if not MART_CSV.exists():
        raise FileNotFoundError(
            f"Mart CSV not found: {MART_CSV}\n"
            "Run src/export_mart.py first."
        )
    return pd.read_csv(MART_CSV)


# =============================================================================
# Step 2 — Helpers
# =============================================================================

def get_latest_period_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return only rows from the most recent period.
    Uses the highest period_id as the definition of 'latest'.
    """
    latest_id = df["period_id"].max()
    return df[df["period_id"] == latest_id].copy()


def format_money(value: float) -> str:
    """
    Format a TRY value into a human-readable string.
    Values >= 1B shown as 'X.XX B TRY'. Values >= 1M shown as 'X,XXX M TRY'.
    """
    if pd.isna(value):
        return "N/A"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} B TRY"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.0f} M TRY"
    return f"{value:,.0f} TRY"


def format_percent(value: float) -> str:
    """Format a percentage value. Returns '—' for NaN (first-period growth)."""
    if pd.isna(value):
        return "—"
    return f"{value:.2f}%"


# =============================================================================
# Step 3 — Identify findings
# =============================================================================

def identify_key_findings(df: pd.DataFrame) -> dict:
    """
    Derive all named analytical findings from the mart DataFrame.

    Each finding is a dict with the company name, metric value, and period.
    All findings are sourced directly from the CSV — no values are inferred
    or fabricated.
    """
    latest = get_latest_period_df(df)
    latest_label = latest["period_label"].iloc[0]

    def best_row(df_subset: pd.DataFrame, col: str, ascending: bool = False) -> pd.Series:
        return df_subset.sort_values(col, ascending=ascending).iloc[0]

    def worst_row(df_subset: pd.DataFrame, col: str) -> pd.Series:
        return best_row(df_subset, col, ascending=True)

    # Revenue growth: only FY2025 rows have a value (FY2024 is NULL)
    growth_rows = df[df["revenue_growth_pct"].notna()]

    findings: dict = {
        # Growth
        "fastest_growth": {
            "company":   best_row(growth_rows, "revenue_growth_pct")["company_name"],
            "value":     best_row(growth_rows, "revenue_growth_pct")["revenue_growth_pct"],
            "period":    best_row(growth_rows, "revenue_growth_pct")["period_label"],
        },
        "slowest_growth": {
            "company":   worst_row(growth_rows, "revenue_growth_pct")["company_name"],
            "value":     worst_row(growth_rows, "revenue_growth_pct")["revenue_growth_pct"],
            "period":    worst_row(growth_rows, "revenue_growth_pct")["period_label"],
        },

        # Profitability (latest period)
        "highest_gross_margin": {
            "company":   best_row(latest, "gross_margin_pct")["company_name"],
            "value":     best_row(latest, "gross_margin_pct")["gross_margin_pct"],
            "period":    latest_label,
        },
        "lowest_gross_margin": {
            "company":   worst_row(latest, "gross_margin_pct")["company_name"],
            "value":     worst_row(latest, "gross_margin_pct")["gross_margin_pct"],
            "period":    latest_label,
        },
        "highest_net_margin": {
            "company":   best_row(latest, "net_margin_pct")["company_name"],
            "value":     best_row(latest, "net_margin_pct")["net_margin_pct"],
            "period":    latest_label,
        },
        "lowest_net_margin": {
            "company":   worst_row(latest, "net_margin_pct")["company_name"],
            "value":     worst_row(latest, "net_margin_pct")["net_margin_pct"],
            "period":    latest_label,
        },

        # Revenue scale
        "highest_revenue": {
            "company":   best_row(latest, "revenue")["company_name"],
            "value":     best_row(latest, "revenue")["revenue"],
            "period":    latest_label,
        },

        # Balance sheet
        "lowest_leverage": {
            "company":   worst_row(latest, "debt_to_assets_pct")["company_name"],
            "value":     worst_row(latest, "debt_to_assets_pct")["debt_to_assets_pct"],
            "period":    latest_label,
        },
        "highest_leverage": {
            "company":   best_row(latest, "debt_to_assets_pct")["company_name"],
            "value":     best_row(latest, "debt_to_assets_pct")["debt_to_assets_pct"],
            "period":    latest_label,
        },

        # Cash coverage
        "best_cash_coverage": {
            "company":   best_row(latest, "cash_to_debt_pct")["company_name"],
            "value":     best_row(latest, "cash_to_debt_pct")["cash_to_debt_pct"],
            "period":    latest_label,
        },
        "weakest_cash_coverage": {
            "company":   worst_row(latest, "cash_to_debt_pct")["company_name"],
            "value":     worst_row(latest, "cash_to_debt_pct")["cash_to_debt_pct"],
            "period":    latest_label,
        },

        # Metadata
        "companies":    sorted(df["company_name"].unique().tolist()),
        "periods":      sorted(df["period_label"].unique().tolist()),
        "latest_period": latest_label,
    }

    return findings


# =============================================================================
# Step 4 — Write executive summary
# =============================================================================

def write_executive_summary(findings: dict, df: pd.DataFrame) -> None:
    """Write the executive summary Markdown file to REPORTS_DIR."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    latest = get_latest_period_df(df)
    latest_label = findings["latest_period"]
    periods = findings["periods"]
    companies = findings["companies"]

    # Build the per-company latest-period comparison table
    table_rows = latest.sort_values("company_name")[
        ["company_name", "sector", "revenue", "revenue_growth_pct",
         "gross_margin_pct", "operating_margin_pct", "net_margin_pct",
         "debt_to_assets_pct", "cash_to_debt_pct"]
    ].copy()

    def tbl_line(row: pd.Series) -> str:
        return (
            f"| {row['company_name']} | {row['sector']} "
            f"| {format_money(row['revenue'])} "
            f"| {format_percent(row['revenue_growth_pct'])} "
            f"| {format_percent(row['gross_margin_pct'])} "
            f"| {format_percent(row['net_margin_pct'])} "
            f"| {format_percent(row['debt_to_assets_pct'])} "
            f"| {format_percent(row['cash_to_debt_pct'])} |"
        )

    lines: list[str] = []

    # ── Header ────────────────────────────────────────────────────────────────
    lines += [
        "# Executive Summary — Financial Intelligence Pipeline",
        "",
        f"**Generated:** {ts}  ",
        f"**Data source:** `{MART_CSV.relative_to(PROJECT_ROOT).as_posix()}`  ",
        f"**Companies analysed:** {len(companies)} ({', '.join(companies)})  ",
        f"**Reporting periods:** {len(periods)} ({', '.join(periods)})  ",
        "",
        "> ⚠️ **SYNTHETIC DATA DISCLAIMER**  ",
        "> All data in this report is **synthetic sample data** generated for pipeline",
        "> demonstration purposes. The companies, financial values, and metrics are",
        "> entirely fictional. This report does not represent real company performance,",
        "> real financial results, or investment advice of any kind.",
        "",
        "---",
        "",
    ]

    # ── Executive Overview ────────────────────────────────────────────────────
    f = findings
    lines += [
        "## Executive Overview",
        "",
        f"This report summarises the financial performance of {len(companies)} fictional",
        f"companies across {len(periods)} reporting periods ({' and '.join(periods)}) based",
        f"on synthetic financial metrics generated for pipeline testing.",
        "",
        f"In {latest_label}:",
        "",
        f"- **Fastest-growing company:** {f['fastest_growth']['company']} "
        f"({format_percent(f['fastest_growth']['value'])} revenue growth)",
        f"- **Most profitable company:** {f['highest_net_margin']['company']} "
        f"(net margin {format_percent(f['highest_net_margin']['value'])})",
        f"- **Largest by revenue:** {f['highest_revenue']['company']} "
        f"({format_money(f['highest_revenue']['value'])})",
        f"- **Most conservatively leveraged:** {f['lowest_leverage']['company']} "
        f"(debt/assets {format_percent(f['lowest_leverage']['value'])})",
        "",
        "---",
        "",
    ]

    # ── Company Performance Highlights ───────────────────────────────────────
    lines += [
        "## Company Performance Highlights",
        "",
        f"Period: **{latest_label}** (YoY growth vs FY2024)",
        "",
        "| Company | Sector | Revenue | Growth | Gross Margin | Net Margin | Debt/Assets | Cash/Debt |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in table_rows.iterrows():
        lines.append(tbl_line(row))

    lines += ["", "---", ""]

    # ── Growth Analysis ───────────────────────────────────────────────────────
    lines += [
        "## Growth Analysis",
        "",
        f"Revenue growth is calculated as the percentage change in revenue from FY2024 to {latest_label}.",
        "",
    ]
    growth_rows = df[df["revenue_growth_pct"].notna()].sort_values(
        "revenue_growth_pct", ascending=False
    )
    for _, row in growth_rows.iterrows():
        prev = df[(df["company_name"] == row["company_name"]) &
                  (df["period_label"] == "FY2024")]["revenue"].iloc[0]
        lines.append(
            f"- **{row['company_name']}**: revenue grew from {format_money(prev)} (FY2024) "
            f"to {format_money(row['revenue'])} ({latest_label}), "
            f"a growth rate of **{format_percent(row['revenue_growth_pct'])}**."
        )

    lines += [
        "",
        f"**{f['fastest_growth']['company']}** recorded the highest growth rate "
        f"in the dataset at **{format_percent(f['fastest_growth']['value'])}**.",
        f"**{f['slowest_growth']['company']}** recorded the lowest growth rate at "
        f"**{format_percent(f['slowest_growth']['value'])}**.",
        "",
        "---",
        "",
    ]

    # ── Profitability Analysis ────────────────────────────────────────────────
    lines += [
        "## Profitability Analysis",
        "",
        f"Profitability is measured across three margin metrics in {latest_label}.",
        "",
        "| Company | Gross Margin | Operating Margin | Net Margin |",
        "|---|---:|---:|---:|",
    ]
    for _, row in latest.sort_values("net_margin_pct", ascending=False).iterrows():
        lines.append(
            f"| {row['company_name']} "
            f"| {format_percent(row['gross_margin_pct'])} "
            f"| {format_percent(row['operating_margin_pct'])} "
            f"| {format_percent(row['net_margin_pct'])} |"
        )

    lines += [
        "",
        f"**{f['highest_gross_margin']['company']}** leads on gross margin at "
        f"**{format_percent(f['highest_gross_margin']['value'])}**, indicating "
        f"strong pricing power or lower direct costs relative to revenue.",
        "",
        f"**{f['highest_net_margin']['company']}** leads on net margin at "
        f"**{format_percent(f['highest_net_margin']['value'])}**, meaning it retains "
        f"the highest proportion of revenue as final profit after all expenses.",
        "",
        f"**{f['lowest_net_margin']['company']}** has the thinnest net margin at "
        f"**{format_percent(f['lowest_net_margin']['value'])}**, consistent with the "
        f"characteristically narrow margins of its sector "
        f"({latest[latest['company_name'] == f['lowest_net_margin']['company']]['sector'].iloc[0]}).",
        "",
        "---",
        "",
    ]

    # ── Balance Sheet / Leverage Analysis ────────────────────────────────────
    lines += [
        "## Balance Sheet and Leverage",
        "",
        f"Leverage is measured as total debt as a percentage of total assets in {latest_label}.",
        "",
        "| Company | Total Assets | Total Debt | Debt / Assets |",
        "|---|---:|---:|---:|",
    ]
    for _, row in latest.sort_values("debt_to_assets_pct").iterrows():
        lines.append(
            f"| {row['company_name']} "
            f"| {format_money(row['total_assets'])} "
            f"| {format_money(row['total_debt'])} "
            f"| {format_percent(row['debt_to_assets_pct'])} |"
        )

    lines += [
        "",
        f"**{f['lowest_leverage']['company']}** carries the lightest debt burden at "
        f"**{format_percent(f['lowest_leverage']['value'])}** debt-to-assets, "
        f"giving it the most balance sheet flexibility.",
        "",
        f"**{f['highest_leverage']['company']}** and other companies in capital-intensive "
        f"sectors carry higher leverage ratios, which is typical for their industry profile.",
        "",
        "---",
        "",
    ]

    # ── Cash Coverage Analysis ────────────────────────────────────────────────
    lines += [
        "## Cash Coverage",
        "",
        f"Cash coverage (cash / total debt × 100) measures liquidity relative to "
        f"financial obligations in {latest_label}.",
        "",
        "| Company | Cash | Total Debt | Cash / Debt |",
        "|---|---:|---:|---:|",
    ]
    for _, row in latest.sort_values("cash_to_debt_pct", ascending=False).iterrows():
        lines.append(
            f"| {row['company_name']} "
            f"| {format_money(row['cash'])} "
            f"| {format_money(row['total_debt'])} "
            f"| {format_percent(row['cash_to_debt_pct'])} |"
        )

    lines += [
        "",
        f"**{f['best_cash_coverage']['company']}** has the strongest cash coverage at "
        f"**{format_percent(f['best_cash_coverage']['value'])}** — meaning it holds "
        f"{f['best_cash_coverage']['value']:.1f} TRY in cash for every 100 TRY of debt.",
        "",
        f"**{f['weakest_cash_coverage']['company']}** has the weakest cash coverage at "
        f"**{format_percent(f['weakest_cash_coverage']['value'])}** and may have "
        f"less flexibility to absorb short-term liquidity shocks.",
        "",
        "---",
        "",
    ]

    # ── Risk Keywords ─────────────────────────────────────────────────────────
    lines += [
        "## Risk Keyword Analysis",
        "",
        "Risk keyword counts measure the frequency of disclosed risk terms in management",
        "commentary and annual report text.",
        "",
        "**Current status:** Risk keyword count is **0 for all companies and periods** in",
        "this synthetic MVP. The `fact_risk_keyword` table exists in the database schema",
        "but is not yet populated because no real documents have been processed.",
        "",
        "When Phase 8+ document processing is activated, this section will automatically",
        "populate with counts of keywords such as: *inflation, currency risk, liquidity,",
        "interest rate, supply chain, demand slowdown, regulation*.",
        "",
        "---",
        "",
    ]

    # ── Limitations ───────────────────────────────────────────────────────────
    lines += [
        "## Limitations",
        "",
        "The following limitations apply to all findings in this report:",
        "",
        "1. **Synthetic data only.** All financial values are generated programmatically.",
        "   No real company financials, annual reports, or external sources were used.",
        "",
        "2. **Small dataset.** Only 3 companies and 2 reporting periods are included in",
        "   the MVP. Real analysis requires a broader peer set and more periods.",
        "",
        "3. **No real document extraction.** The pipeline currently loads synthetic CSV",
        "   data directly. PDF, Excel, and PPTX document parsing is planned for Phase 8.",
        "",
        "4. **Risk keyword table is empty.** The `fact_risk_keyword` table exists but",
        "   contains no data. Risk analysis requires real management commentary.",
        "",
        "5. **Currency consistency.** All values are in TRY (Turkish Lira). No FX",
        "   conversion or multi-currency handling is implemented in the MVP.",
        "",
        "6. **No audit trail.** Extracted values have confidence_score = 1.00 because",
        "   they are synthetic. Real document extraction will produce variable confidence",
        "   scores that must be reviewed before being included in reporting.",
        "",
        "7. **These are pipeline demonstration outputs, not investment advice.**",
        "",
        "---",
        "",
    ]

    # ── Next Questions ────────────────────────────────────────────────────────
    lines += [
        "## Recommended Next Analytical Questions",
        "",
        "Once real financial data is loaded, this pipeline can answer:",
        "",
        "- Which company's revenue growth is sustainable based on operating cash flow trends?",
        "- Is the highest-leverage company's debt increasing faster than its revenue?",
        "- Which company mentions the most risk keywords in its management commentary?",
        "- Has any company's net margin deteriorated significantly period over period?",
        "- Which company has the strongest cash conversion quality (operating CF / net income)?",
        "",
        "---",
        "",
        "> *Generated by the AI-Assisted Financial Intelligence Pipeline.*  ",
        "> *All data is synthetic. No real financial results are presented or implied.*",
        "",
    ]

    EXECUTIVE_SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    print("=" * 60)
    print("Executive Summary Generator")
    print("=" * 60)
    print(f"Reading : {MART_CSV}")
    print(f"Writing : {EXECUTIVE_SUMMARY_PATH}")
    print()

    df = load_mart_csv()
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns.")

    findings = identify_key_findings(df)

    print()
    print("--- Key findings ---")
    print(f"  Fastest growth   : {findings['fastest_growth']['company']} "
          f"({format_percent(findings['fastest_growth']['value'])})")
    print(f"  Highest net margin: {findings['highest_net_margin']['company']} "
          f"({format_percent(findings['highest_net_margin']['value'])})")
    print(f"  Highest revenue  : {findings['highest_revenue']['company']} "
          f"({format_money(findings['highest_revenue']['value'])})")
    print(f"  Lowest leverage  : {findings['lowest_leverage']['company']} "
          f"({format_percent(findings['lowest_leverage']['value'])} debt/assets)")
    print(f"  Best cash cover  : {findings['best_cash_coverage']['company']} "
          f"({format_percent(findings['best_cash_coverage']['value'])} cash/debt)")

    write_executive_summary(findings, df)

    print()
    print(f"Executive summary written: {EXECUTIVE_SUMMARY_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
