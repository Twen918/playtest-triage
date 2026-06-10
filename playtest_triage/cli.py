"""Command-line interface for playtest-triage."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

from .analyzer import DEFAULT_MODEL, analyze, analyze_mock, load_items, to_dicts
from .report import build_report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="playtest-triage",
        description="Triage raw playtest feedback into a structured QA report.",
    )
    parser.add_argument("input", help="text file with one feedback item per line")
    parser.add_argument(
        "-o", "--output", default="triage_report.md", help="markdown report path"
    )
    parser.add_argument("--json-out", help="optional path for raw JSON results")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Claude model to use")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument(
        "--mock",
        action="store_true",
        help="offline keyword mode (no API key needed)",
    )
    args = parser.parse_args(argv)

    items = load_items(args.input)
    if not items:
        sys.exit(f"No feedback items found in {args.input}")

    if args.mock:
        findings = analyze_mock(items)
        mode = "mock"
    else:
        findings = analyze(items, model=args.model, batch_size=args.batch_size)
        mode = f"live ({args.model})"

    report = build_report(findings, source=args.input, mode=mode)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(report)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(to_dicts(findings), fh, indent=2, ensure_ascii=False)

    counts = Counter(finding.category for finding in findings)
    print(f"Triaged {len(findings)} items -> {args.output}")
    for category, count in counts.most_common():
        print(f"  {category:<12}{count}")


if __name__ == "__main__":
    main()
