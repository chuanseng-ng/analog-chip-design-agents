"""Real open-source tool smoke test (ngspice via the infrastructure wrapper).

Exercises the actual EDA-tool path — ``plugins/infrastructure/tools/wrap-ngspice.sh``
running a tiny, PDK-independent deck — rather than only detecting the tool. The
ngspice-dependent test is skipped where the binary is unavailable (e.g. most CI
runners), so it never makes CI flaky; an always-on guard still verifies the worked
example and wrapper are present and wired.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
WRAP = REPO / "plugins" / "infrastructure" / "tools" / "wrap-ngspice.sh"
DECK = REPO / "examples" / "designs" / "ldo_pm" / "smoke" / "divider.sp"


def test_smoke_example_and_wrapper_present():
    # Always runs — keeps the worked example and wrapper from silently disappearing.
    assert DECK.is_file(), f"missing smoke deck: {DECK}"
    assert WRAP.is_file(), f"missing wrapper: {WRAP}"
    assert os.access(WRAP, os.X_OK), f"wrapper not executable: {WRAP}"


@pytest.mark.skipif(shutil.which("ngspice") is None, reason="ngspice not installed")
def test_ngspice_wrapper_runs_divider():
    res = subprocess.run(
        ["bash", str(WRAP), "-b", str(DECK)],
        capture_output=True, text=True, timeout=60,
    )
    assert res.returncode == 0, f"wrapper failed:\n{res.stdout}\n{res.stderr}"

    payload = json.loads(res.stdout)
    assert payload["tool"] == "ngspice"
    assert payload["status"] == "PASS", payload
    assert payload["summary"]["convergence"] is True

    vmid = payload["summary"]["measures"].get("vmid")
    assert vmid is not None, f"no 'vmid' measure captured: {payload}"
    assert abs(vmid - 0.5) < 1e-3, f"expected vmid ~ 0.5 V, got {vmid}"


@pytest.mark.skipif(shutil.which("ngspice") is not None,
                    reason="ngspice present — detect-only fallback not exercised")
def test_wrapper_reports_missing_tool_cleanly():
    # Where ngspice is absent, the wrapper must still emit valid JSON and exit 1.
    res = subprocess.run(
        ["bash", str(WRAP), "-b", str(DECK)],
        capture_output=True, text=True, timeout=60,
    )
    assert res.returncode == 1
    payload = json.loads(res.stdout)
    assert payload["status"] == "FAIL"
    assert any("not found" in e for e in payload["errors"])
