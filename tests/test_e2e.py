"""End-to-end tests: drive the cross-domain fix_request loop to a terminal state.

Exercises the meta dispatch wiring (servicer/revalidator routing, the iteration cap,
the checkpoint gate, and sign-off) via the dependency-free replica in
tests/e2e/run_pipeline.py against the committed example designs and a few synthetic
variants.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

DESIGNS = Path(__file__).resolve().parents[1] / "examples" / "designs"


@pytest.mark.parametrize("design", ["ldo_pm", "lna_nf"])
def test_example_design_reaches_signoff(run_pipeline, design):
    state, scenario = run_pipeline.load_design(DESIGNS / design)
    result = run_pipeline.run(state, scenario, validate=True)

    assert result["outcome"] == "signoff"
    expect = scenario["expect"]
    assert result["cross_domain_iterations"] == expect["cross_domain_iterations"]

    final = result["state"]
    # No open/claimed work left; the resolved entry is archived.
    assert all(f["status"] not in ("open", "claimed") for f in final.get("fix_requests", []))
    assert len(final.get("archive_fix_requests", [])) == 1
    assert final["archive_fix_requests"][0]["status"] == "fixed"
    assert final["pending_approval"] is None
    assert final["pipeline_session_id"] is None


def test_routing_matches_scenario_expectation(run_pipeline):
    # lna_nf must route to em-modeling (Phase 7) and re-validate via rf-design.
    state, scenario = run_pipeline.load_design(DESIGNS / "lna_nf")
    fr = state["fix_requests"][0]
    assert run_pipeline.servicer_for(fr) == scenario["expect"]["servicer"]
    assert run_pipeline.revalidator_for(fr) == scenario["expect"]["revalidator"]

    # ldo_pm has no route_to -> default circuit-design servicer.
    state2, scenario2 = run_pipeline.load_design(DESIGNS / "ldo_pm")
    fr2 = state2["fix_requests"][0]
    assert "route_to" not in fr2
    assert run_pipeline.servicer_for(fr2) == "circuit-design-orchestrator"


def test_iteration_cap_escalates_non_converging(run_pipeline):
    state, scenario = run_pipeline.load_design(DESIGNS / "ldo_pm")
    # Servicer never fixes the spec -> loop must hit the cap and escalate.
    scenario = copy.deepcopy(scenario)
    scenario["servicer_responses"]["fr_ldo_pm_001"]["fixed_on_iteration"] = None
    result = run_pipeline.run(state, scenario, validate=True)

    assert result["outcome"] == "escalate_cap"
    cap = state["pipeline_config"]["max_cross_domain_iterations"]
    assert result["cross_domain_iterations"] == cap
    pa = result["state"]["pending_approval"]
    assert pa["type"] == "escalation"
    assert "resource_limit" in pa["reason"]


def test_checkpoint_gate_blocks_until_approved(run_pipeline):
    state, scenario = run_pipeline.load_design(DESIGNS / "ldo_pm")
    # Fix succeeds, but the tapeout_signoff checkpoint is NOT approved.
    scenario = copy.deepcopy(scenario)
    scenario["checkpoint_approvals"] = []
    result = run_pipeline.run(state, scenario, validate=True)

    assert result["outcome"] == "await_checkpoint"
    pa = result["state"]["pending_approval"]
    assert pa["type"] == "checkpoint"
    assert pa["stage"] == "tapeout_signoff"
    # The fix itself succeeded before the gate halted sign-off.
    assert result["state"]["fix_requests"][0]["status"] == "fixed"


def test_intake_halts_on_preexisting_pending_approval(run_pipeline):
    state, scenario = run_pipeline.load_design(DESIGNS / "ldo_pm")
    state = copy.deepcopy(state)
    state["pending_approval"] = {"type": "constraint_gap", "agent": "circuit-design-orchestrator",
                                 "reason": "missing supply.vdd_v"}
    result = run_pipeline.run(state, scenario, validate=True)
    assert result["outcome"] == "halt_constraint_gap"
    # Nothing was dispatched.
    assert result["cross_domain_iterations"] == 0


def test_emitted_history_entries_are_schema_valid(run_pipeline):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((Path(__file__).resolve().parents[1]
                         / "docs" / "design_state.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(schema)

    state, scenario = run_pipeline.load_design(DESIGNS / "ldo_pm")
    result = run_pipeline.run(state, scenario, validate=True)
    # Final state (with all appended history entries) validates clean.
    assert not list(validator.iter_errors(result["state"]))
