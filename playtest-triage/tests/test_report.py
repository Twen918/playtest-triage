from playtest_triage.analyzer import Finding
from playtest_triage.report import build_report, group_findings


def test_groups_sorted_by_severity():
    findings = [
        Finding(text="a", category="bug", severity="low"),
        Finding(text="b", category="bug", severity="critical"),
    ]
    groups = group_findings(findings)
    assert [f.severity for f in groups["bug"]] == ["critical", "low"]


def test_report_contains_sections_and_counts():
    findings = [
        Finding(text="crash", category="bug", severity="high", summary="Crash on load"),
        Finding(text="nice", category="praise", severity="low"),
    ]
    report = build_report(findings, source="notes.txt", mode="mock")
    assert "# Playtest Feedback Triage Report" in report
    assert "| Bugs | 1 |" in report
    assert "**[high]** Crash on load" in report
    assert 'raw: "crash"' in report


def test_empty_categories_are_omitted():
    findings = [Finding(text="crash", category="bug", severity="high")]
    report = build_report(findings)
    assert "Performance" not in report
    assert "What Players Loved" not in report
