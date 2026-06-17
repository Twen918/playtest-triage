"""Render triage findings as a markdown report."""

from __future__ import annotations

from collections import OrderedDict

from .analyzer import Finding

_CATEGORY_ORDER = ("bug", "performance", "balance", "ux", "praise", "other")
_CATEGORY_TITLES = {
    "bug": "Bugs",
    "performance": "Performance",
    "balance": "Balance",
    "ux": "UX & Clarity",
    "praise": "What Players Loved",
    "other": "Other",
}
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def group_findings(findings: list[Finding]) -> "OrderedDict[str, list[Finding]]":
    """Group findings by category (fixed order), severity-sorted within each."""
    groups: "OrderedDict[str, list[Finding]]" = OrderedDict(
        (category, []) for category in _CATEGORY_ORDER
    )
    for finding in findings:
        groups.setdefault(finding.category, []).append(finding)
    for items in groups.values():
        items.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 99))
    return groups


def build_report(findings: list[Finding], source: str = "", mode: str = "live") -> str:
    """Build the full markdown report."""
    groups = group_findings(findings)

    lines = ["# Playtest Feedback Triage Report", ""]
    total = sum(finding.count for finding in findings)
    meta = f"{len(findings)} items - mode: {mode}"
    if total != len(findings):
        meta = f"{len(findings)} unique items ({total} raw) - mode: {mode}"
    if source:
        meta = f"Source: `{source}` - " + meta
    lines += [meta, "", "## Summary", "", "| Category | Count |", "| --- | --- |"]
    for category, items in groups.items():
        if items:
            title = _CATEGORY_TITLES.get(category, category.title())
            lines.append(f"| {title} | {len(items)} |")
    lines.append("")

    for category, items in groups.items():
        if not items:
            continue
        title = _CATEGORY_TITLES.get(category, category.title())
        lines += [f"## {title} ({len(items)})", ""]
        for finding in items:
            headline = finding.summary or finding.text
            line = f"- **[{finding.severity}]** {headline}"
            if finding.count > 1:
                line += f" *(reported {finding.count}x)*"
            lines.append(line)
            if finding.summary and finding.summary != finding.text:
                lines.append(f'  - raw: "{finding.text}"')
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
