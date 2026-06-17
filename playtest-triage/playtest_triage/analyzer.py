"""Classify raw playtest feedback with the Claude API (or an offline mock)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

CATEGORIES = ("bug", "balance", "ux", "performance", "praise", "other")
SEVERITIES = ("critical", "high", "medium", "low")

DEFAULT_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "You are a QA analyst triaging playtest feedback for a video game team. "
    "For every feedback item you receive, classify it and respond with JSON only."
)

_PROMPT = """Classify each playtest feedback item below.

For every item, return an object with:
- "id": the item's number, unchanged
- "category": one of {categories}
- "severity": one of {severities} ("praise" items are always "low")
- "summary": a one-sentence neutral restatement a developer can act on

Respond with ONLY a JSON array of these objects - no prose, no code fences.

Feedback items:
{items}"""


@dataclass
class Finding:
    """One classified piece of playtest feedback."""

    text: str
    category: str = "other"
    severity: str = "low"
    summary: str = ""
    count: int = 1  # raw items merged into this one (see dedup.py)


def load_items(path: str) -> list[str]:
    """Read one feedback item per line, skipping blanks and # comments."""
    items = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                items.append(line)
    return items


def analyze(
    items: list[str],
    model: str = DEFAULT_MODEL,
    batch_size: int = 25,
) -> list[Finding]:
    """Classify feedback via the Claude API. Requires ANTHROPIC_API_KEY."""
    from anthropic import Anthropic

    client = Anthropic()
    findings: list[Finding] = []
    for start in range(0, len(items), batch_size):
        batch = items[start : start + batch_size]
        numbered = "\n".join(f"{i + 1}. {text}" for i, text in enumerate(batch))
        prompt = _PROMPT.format(
            categories=", ".join(CATEGORIES),
            severities=", ".join(SEVERITIES),
            items=numbered,
        )
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        reply = "".join(
            block.text for block in message.content if block.type == "text"
        )
        findings.extend(parse_model_response(reply, batch))
    return findings


def parse_model_response(reply: str, batch: list[str]) -> list[Finding]:
    """Turn the model's JSON reply into Findings, falling back safely.

    Every item in ``batch`` always produces a Finding. If the reply is
    malformed, items keep their defaults (category="other", severity="low")
    instead of crashing the run.
    """
    findings = [Finding(text=text) for text in batch]
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", reply.strip())
    try:
        rows = json.loads(cleaned)
    except json.JSONDecodeError:
        return findings
    if not isinstance(rows, list):
        return findings
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            idx = int(row.get("id", 0)) - 1
        except (TypeError, ValueError):
            continue
        if not 0 <= idx < len(findings):
            continue
        finding = findings[idx]
        category = str(row.get("category", "")).lower()
        severity = str(row.get("severity", "")).lower()
        finding.category = category if category in CATEGORIES else "other"
        finding.severity = severity if severity in SEVERITIES else "low"
        finding.summary = str(row.get("summary", "")).strip()
    return findings


# --- offline mock mode ----------------------------------------------------

_MOCK_RULES = (
    (
        ("loop", "stuck", "disappear", "didn't register", "crash", "glitch", "broken"),
        "bug",
        "high",
    ),
    (("frame", "fps", "lag", "stutter", "tank"), "performance", "high"),
    (
        ("unfair", "too fast", "too slow", "too hard", "too easy", "cheap", "too much"),
        "balance",
        "medium",
    ),
    (
        (
            "dark",
            "timer",
            "no idea",
            "couldn't find",
            "couldn't tell",
            "not obvious",
            "confusing",
            "wish",
        ),
        "ux",
        "medium",
    ),
    (
        ("love", "amazing", "great", "incredible", "scariest", "cool", "intense"),
        "praise",
        "low",
    ),
)


def analyze_mock(items: list[str]) -> list[Finding]:
    """Offline keyword classifier so the tool runs without an API key.

    Intentionally simple: first matching rule wins. Used for demos and tests;
    the live mode (``analyze``) is the real classifier.
    """
    findings = []
    for text in items:
        lowered = text.lower()
        finding = Finding(text=text)
        for keywords, category, severity in _MOCK_RULES:
            if any(keyword in lowered for keyword in keywords):
                finding.category, finding.severity = category, severity
                break
        findings.append(finding)
    return findings


def to_dicts(findings: list[Finding]) -> list[dict]:
    """Findings as plain dicts, for JSON export."""
    return [asdict(f) for f in findings]
