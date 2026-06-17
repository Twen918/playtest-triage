import json

from playtest_triage.analyzer import analyze_mock, parse_model_response

BATCH = ["Game crashes in the freezer room", "I love the sliding"]


def test_parse_valid_json():
    reply = json.dumps(
        [
            {"id": 1, "category": "bug", "severity": "critical", "summary": "Crash in freezer room"},
            {"id": 2, "category": "praise", "severity": "low", "summary": "Sliding praised"},
        ]
    )
    findings = parse_model_response(reply, BATCH)
    assert findings[0].category == "bug"
    assert findings[0].severity == "critical"
    assert findings[1].category == "praise"


def test_parse_strips_code_fences():
    reply = '```json\n[{"id": 1, "category": "bug", "severity": "high", "summary": "x"}]\n```'
    findings = parse_model_response(reply, BATCH)
    assert findings[0].category == "bug"


def test_parse_invalid_values_fall_back_to_defaults():
    reply = json.dumps([{"id": 1, "category": "nonsense", "severity": "weird", "summary": ""}])
    findings = parse_model_response(reply, BATCH)
    assert findings[0].category == "other"
    assert findings[0].severity == "low"


def test_parse_garbage_reply_keeps_every_item():
    findings = parse_model_response("not json at all", BATCH)
    assert [f.text for f in findings] == BATCH
    assert all(f.category == "other" for f in findings)


def test_parse_out_of_range_id_is_ignored():
    reply = json.dumps([{"id": 99, "category": "bug", "severity": "high", "summary": "x"}])
    findings = parse_model_response(reply, BATCH)
    assert all(f.category == "other" for f in findings)


def test_mock_classifier_keywords():
    findings = analyze_mock(["The sound kept looping forever", "This is amazing"])
    assert findings[0].category == "bug"
    assert findings[1].category == "praise"
