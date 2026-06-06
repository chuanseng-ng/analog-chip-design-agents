"""Unit tests for the memory-keeper distill.py helper."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DISTILL = Path(__file__).resolve().parents[1] / \
    "plugins/infrastructure/skills/memory-keeper/distill.py"


def test_every_valid_domain_has_metric_fields(distill):
    # The 14 design domains + infrastructure + meta must each be registered.
    assert len(distill.VALID_DOMAINS) == 16
    for dom in distill.VALID_DOMAINS:
        assert dom in distill.METRIC_FIELDS, f"{dom} missing from METRIC_FIELDS"
    assert "infrastructure" in distill.VALID_DOMAINS
    assert "meta" in distill.VALID_DOMAINS


def test_load_records_skips_malformed_and_non_objects(distill, tmp_path):
    p = tmp_path / "experiences.jsonl"
    p.write_text(
        '{"a": 1}\n'
        "\n"                       # blank line ignored
        "not json\n"               # malformed -> skipped
        "[1, 2, 3]\n"              # valid JSON but not an object -> skipped
        '{"b": 2}\n')
    records = distill.load_records(p)
    assert records == [{"a": 1}, {"b": 2}]


def test_load_records_missing_file_returns_empty(distill, tmp_path):
    assert distill.load_records(tmp_path / "nope.jsonl") == []


def test_compute_metric_ranges(distill):
    records = [
        {"key_metrics": {"dc_gain_db": 60.0, "phase_margin_deg": 65}},
        {"key_metrics": {"dc_gain_db": 62.0, "phase_margin_deg": 55}},
        {"key_metrics": {"dc_gain_db": 64.0}},
    ]
    ranges = distill.compute_metric_ranges(records, "circuit")
    assert ranges["dc_gain_db"]["min"] == 60.0
    assert ranges["dc_gain_db"]["max"] == 64.0
    assert ranges["dc_gain_db"]["latest"] == 64.0
    assert ranges["dc_gain_db"]["count"] == 3
    assert ranges["phase_margin_deg"]["count"] == 2


def test_extract_issue_fix_pairs(distill):
    records = [
        {"issues_encountered": ["low PM"], "fixes_applied": ["bigger Cc"]},
        {"issues_encountered": ["low PM"], "fixes_applied": ["bigger Cc"]},
        {"issues_encountered": ["dc offset"], "fixes_applied": ["trim"]},
    ]
    pairs = distill.extract_issue_fix_pairs(records)
    top = pairs[0]
    assert top["issue"] == "low PM" and top["fix"] == "bigger Cc"
    assert top["count"] == 2


def _run(domain, memory_root, min_records=5):
    return subprocess.run(
        [sys.executable, str(DISTILL), domain,
         "--memory-root", str(memory_root), "--min-records", str(min_records)],
        capture_output=True, text=True)


def test_main_skips_below_threshold(tmp_path):
    mem = tmp_path / "memory" / "circuit"
    mem.mkdir(parents=True)
    (mem / "experiences.jsonl").write_text('{"timestamp": "t", "key_metrics": {}}\n')
    res = _run("circuit", tmp_path / "memory", min_records=5)
    assert res.returncode == 2
    payload = json.loads(res.stdout)
    assert payload["skipped"] is True
    assert payload["record_count"] == 1


def test_main_emits_summary_when_enough_records(tmp_path):
    mem = tmp_path / "memory" / "circuit"
    mem.mkdir(parents=True)
    lines = []
    for i in range(5):
        lines.append(json.dumps({
            "timestamp": f"2026-03-0{i+1}T00:00:00Z",
            "key_metrics": {"dc_gain_db": 60 + i},
            "issues_encountered": ["x"], "fixes_applied": ["y"],
            "notes": f"run {i}", "signoff_achieved": i % 2 == 0,
        }))
    (mem / "experiences.jsonl").write_text("\n".join(lines) + "\n")
    res = _run("circuit", tmp_path / "memory", min_records=5)
    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    assert payload["skipped"] is False
    assert payload["record_count"] == 5
    assert "dc_gain_db" in payload["metric_ranges"]
    assert payload["signoff_rate"] == round(3 / 5, 3)


def test_main_rejects_unknown_domain(tmp_path):
    res = _run("not-a-domain", tmp_path / "memory")
    assert res.returncode == 2          # argparse choices error
    assert "invalid choice" in res.stderr
