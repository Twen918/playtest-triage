# playtest-triage

Turn a pile of raw playtest notes into an organized QA report, using the Claude API.

## Why this exists

After my team shipped [Desperation](https://chieftain22.itch.io/desperation), a first-person
survival horror game built in Unreal Engine 5, we had pages of raw playtester feedback -
"too dark", "the monster feels unfair", "the sound loops in the packaged build" - all mixed
together. Sorting it by hand into bugs, balance problems, and UX issues took longer than
fixing some of the bugs. This tool does that first triage pass automatically.

## What it does

Given a text file with one feedback note per line, it:

1. Sends the notes to the Claude API in batches and asks for structured JSON:
   a **category** (`bug`, `balance`, `ux`, `performance`, `praise`, `other`),
   a **severity** (`critical` / `high` / `medium` / `low`), and a one-line
   actionable **summary** of each note.
2. Parses the response defensively - malformed output never crashes a run,
   items just fall back to safe defaults.
3. Renders a markdown report grouped by category and sorted by severity,
   plus optional raw JSON for further processing.

See [`sample_output.md`](sample_output.md) for a report generated from the real
feedback themes our Desperation playtests produced.

## Quickstart

```bash
git clone https://github.com/Twen918/playtest-triage.git
cd playtest-triage
pip install -e .

# Try it immediately - no API key needed (offline keyword mode):
playtest-triage sample_data/desperation_feedback.txt --mock

# Real classification with the Claude API:
export ANTHROPIC_API_KEY=sk-ant-...
playtest-triage sample_data/desperation_feedback.txt -o report.md --json-out results.json
```

Output:

```
Triaged 18 items -> report.md
  balance     4
  ux          4
  praise      4
  bug         4
  performance 1
  other       1
```

## How it works

- **Prompt-constrained structured output.** The prompt numbers each feedback item and
  asks for a JSON array of `{id, category, severity, summary}` objects, with the
  allowed values spelled out. Using ids (instead of echoing text back) keeps responses
  small and makes re-joining results reliable.
- **Defensive parsing** (`analyzer.parse_model_response`). Code fences are stripped,
  invalid categories/severities fall back to safe defaults, out-of-range ids are
  ignored, and every input item is guaranteed to produce a result.
- **Batching.** Items are classified in batches (default 25 per API call) so large
  feedback files don't hit token limits.
- **Mock mode** (`--mock`) is a deliberately simple keyword classifier so anyone can
  run the tool and tests offline. The live mode is the real classifier.

## Project structure

```
playtest_triage/
  analyzer.py   # API call, response parsing, mock classifier
  report.py     # grouping + markdown rendering
  cli.py        # argparse entry point
tests/          # pytest unit tests for parsing and reporting (no network needed)
sample_data/    # anonymized feedback from Desperation playtest sessions
```

Run the tests:

```bash
pip install -e ".[dev]"
python -m pytest
```

## Roadmap

- Deduplicate near-identical feedback before classification
- Track categories across multiple playtest sessions to show trends
- Export directly to a bug tracker (JIRA / GitHub Issues)

## Notes

Built with AI-assisted development tools as part of my workflow; all code is
reviewed, tested, and maintained by hand. MIT licensed.
