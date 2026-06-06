"""Unit tests for tools/qor_trends.py."""

from __future__ import annotations

import json

from conftest import write_experiences


def test_as_number_coercions(qor_trends):
    assert qor_trends.as_number(True) == 1.0
    assert qor_trends.as_number(False) == 0.0
    assert qor_trends.as_number(3) == 3.0
    assert qor_trends.as_number(2.5) == 2.5
    assert qor_trends.as_number("4.2") == 4.2
    assert qor_trends.as_number("not-a-number") is None
    assert qor_trends.as_number(None) is None


def test_collect_points_filters_by_design_and_metric(qor_trends, tmp_path):
    mem = tmp_path / "memory"
    write_experiences(mem, "circuit", [
        {"timestamp": "2026-01-01T00:00:00Z", "domain": "circuit",
         "design_name": "a", "pdk": "sky130", "tool_used": "ngspice",
         "key_metrics": {"phase_margin_deg": 60, "nf_db": 2.0}},
        {"timestamp": "2026-01-02T00:00:00Z", "domain": "circuit",
         "design_name": "b", "pdk": "sky130", "tool_used": "ngspice",
         "key_metrics": {"phase_margin_deg": 55}},
    ])
    pts = qor_trends.collect_points(str(mem), "a", None, {"phase_margin_deg"})
    # Only design "a", only the requested metric.
    assert [p["value"] for p in pts] == [60.0]
    assert all(p["metric"] == "phase_margin_deg" for p in pts)


def test_summarize_flags_higher_is_better_regression(qor_trends, tmp_path):
    mem = tmp_path / "memory"
    write_experiences(mem, "circuit", [
        {"timestamp": "2026-01-01T00:00:00Z", "domain": "circuit",
         "design_name": "a", "key_metrics": {"phase_margin_deg": 65}},
        {"timestamp": "2026-01-02T00:00:00Z", "domain": "circuit",
         "design_name": "a", "key_metrics": {"phase_margin_deg": 50}},
    ])
    pts = qor_trends.collect_points(str(mem), "a", None, None)
    rows, alerts = qor_trends.summarize(pts, "none", 5.0)
    row = next(r for r in rows if r["metric"] == "phase_margin_deg")
    assert row["regressed"] is True          # higher-is-better metric fell
    assert any("phase_margin_deg" in a for a in alerts)


def test_summarize_flags_lower_is_better_regression(qor_trends, tmp_path):
    mem = tmp_path / "memory"
    write_experiences(mem, "rf", [
        {"timestamp": "2026-01-01T00:00:00Z", "domain": "rf",
         "design_name": "lna", "key_metrics": {"nf_db": 2.0}},
        {"timestamp": "2026-01-02T00:00:00Z", "domain": "rf",
         "design_name": "lna", "key_metrics": {"nf_db": 2.6}},
    ])
    pts = qor_trends.collect_points(str(mem), "lna", None, None)
    rows, alerts = qor_trends.summarize(pts, "none", 5.0)
    row = next(r for r in rows if r["metric"] == "nf_db")
    assert row["regressed"] is True          # lower-is-better metric rose
    assert any("nf_db" in a for a in alerts)


def test_summarize_threshold_gating(qor_trends, tmp_path):
    mem = tmp_path / "memory"
    write_experiences(mem, "circuit", [
        {"timestamp": "2026-01-01T00:00:00Z", "domain": "circuit",
         "design_name": "a", "key_metrics": {"phase_margin_deg": 60.0}},
        {"timestamp": "2026-01-02T00:00:00Z", "domain": "circuit",
         "design_name": "a", "key_metrics": {"phase_margin_deg": 59.0}},
    ])
    pts = qor_trends.collect_points(str(mem), "a", None, None)
    # ~1.7% drop is below a 5% threshold -> not a regression.
    rows, alerts = qor_trends.summarize(pts, "none", 5.0)
    assert next(r for r in rows if r["metric"] == "phase_margin_deg")["regressed"] is False
    assert not alerts
    # ...but above a 1% threshold it is.
    rows, alerts = qor_trends.summarize(pts, "none", 1.0)
    assert next(r for r in rows if r["metric"] == "phase_margin_deg")["regressed"] is True


def test_summarize_handles_zero_first_value(qor_trends, tmp_path):
    mem = tmp_path / "memory"
    write_experiences(mem, "physical-verification", [
        {"timestamp": "2026-01-01T00:00:00Z", "domain": "physical-verification",
         "design_name": "a", "key_metrics": {"drc_violations": 0}},
        {"timestamp": "2026-01-02T00:00:00Z", "domain": "physical-verification",
         "design_name": "a", "key_metrics": {"drc_violations": 3}},
    ])
    pts = qor_trends.collect_points(str(mem), "a", None, None)
    rows, _ = qor_trends.summarize(pts, "none", 5.0)
    row = next(r for r in rows if r["metric"] == "drc_violations")
    # first==0, delta!=0 -> pct is +inf (guarded division), still a regression.
    assert row["pct"] == float("inf")
    assert row["regressed"] is True


def test_main_returns_nonzero_on_regression(qor_trends, tmp_path, capsys):
    mem = tmp_path / "memory"
    write_experiences(mem, "circuit", [
        {"timestamp": "2026-01-01T00:00:00Z", "domain": "circuit",
         "design_name": "a", "key_metrics": {"phase_margin_deg": 65}},
        {"timestamp": "2026-01-02T00:00:00Z", "domain": "circuit",
         "design_name": "a", "key_metrics": {"phase_margin_deg": 40}},
    ])
    rc = qor_trends.main(["--design", "a", "--memory-dir", str(mem)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "regression alert" in out

    # CSV mode never gates (returns 0) even when a regression exists.
    rc_csv = qor_trends.main(["--design", "a", "--memory-dir", str(mem), "--format", "csv"])
    assert rc_csv == 0


def test_main_missing_memory_dir(qor_trends, tmp_path):
    assert qor_trends.main(["--memory-dir", str(tmp_path / "nope")]) == 2


def test_committed_fixture_parses(qor_trends, fixtures_dir, tmp_path):
    # The worked-example fixture loads and trends without error.
    mem = tmp_path / "memory"
    (mem / "circuit").mkdir(parents=True)
    (mem / "circuit" / "experiences.jsonl").write_text(
        (fixtures_dir / "sample_experiences.jsonl").read_text())
    pts = qor_trends.collect_points(str(mem), "demo_ota", None, {"phase_margin_deg"})
    assert len(pts) == 5
    rows, alerts = qor_trends.summarize(pts, "none", 5.0)
    # phase_margin_deg trends 65 -> 48 (higher-is-better): a regression.
    assert any(a for a in alerts if "phase_margin_deg" in a)
