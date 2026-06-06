"""Unit tests for tools/export_ides.py."""

from __future__ import annotations

import os


def test_extract_stage_sequence(export_ides):
    text = "## Stage Sequence\n\n`a -> b -> c`\n\n## Next\n"
    assert export_ides.extract_stage_sequence(text) == "a -> b -> c"
    assert export_ides.extract_stage_sequence("no header here") == ""


def test_parse_skill_folded_description_and_stages(export_ides, fixtures_dir):
    s = export_ides.parse_skill(str(fixtures_dir / "sample_SKILL.md"))
    assert s["name"] == "sample-domain"
    # folded (>) block is joined into a single line
    assert "sample analog domain SKILL" in s["description"]
    assert "\n" not in s["description"]
    assert s["stage_sequence"] == "stage_a → stage_b → stage_c"
    assert s["purpose"].startswith("Demonstrate the SKILL shape")
    assert s["rel"].endswith("sample_SKILL.md")


def test_parse_skill_stage_sequence_falls_back_to_agent(export_ides, tmp_path):
    # A SKILL with no '## Stage Sequence' should fall back to the sibling agent's.
    plugin = tmp_path / "plugins" / "demo"
    skill_dir = plugin / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo\ndescription: d\n---\n\n## Purpose\n\nP\n")
    agents = plugin / "agents"
    agents.mkdir()
    (agents / "demo-orchestrator.md").write_text(
        "---\nname: demo-orchestrator\n---\n\n## Stage Sequence\n\n`x -> y`\n")
    s = export_ides.parse_skill(str(skill_dir / "SKILL.md"))
    assert s["stage_sequence"] == "x -> y"


def _make_tmp_repo(tmp_path):
    plugin = tmp_path / "plugins" / "demo" / "skills" / "demo"
    plugin.mkdir(parents=True)
    (plugin / "SKILL.md").write_text(
        "---\nname: demo\ndescription: demo skill\n---\n\n"
        "## Purpose\n\nP\n\n## Stage Sequence\n\n`a -> b`\n")
    return tmp_path


def test_check_mode_reports_stale_then_fresh(export_ides, tmp_path, monkeypatch):
    repo = _make_tmp_repo(tmp_path)
    monkeypatch.setattr(export_ides, "REPO_ROOT", str(repo))

    # ides/ does not exist yet -> stale -> exit 1
    assert export_ides.main(["--check"]) == 1

    # generate, then it should be up to date -> exit 0
    assert export_ides.main([]) == 0
    assert export_ides.main(["--check"]) == 0

    # every configured target file was written
    for key, (relpath, _display) in export_ides.TARGETS.items():
        assert os.path.isfile(os.path.join(repo, "ides", key, relpath))


def test_check_mode_detects_drift_after_skill_edit(export_ides, tmp_path, monkeypatch):
    repo = _make_tmp_repo(tmp_path)
    monkeypatch.setattr(export_ides, "REPO_ROOT", str(repo))
    assert export_ides.main([]) == 0
    assert export_ides.main(["--check"]) == 0

    # Change a rendered field (description) -> exports go stale.
    skill = repo / "plugins" / "demo" / "skills" / "demo" / "SKILL.md"
    skill.write_text(skill.read_text().replace("demo skill", "demo skill EDITED"))
    assert export_ides.main(["--check"]) == 1
