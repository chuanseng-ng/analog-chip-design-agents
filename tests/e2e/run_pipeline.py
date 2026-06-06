#!/usr/bin/env python3
"""run_pipeline.py — end-to-end driver for the cross-domain fix_request loop.

A lightweight, dependency-free replica of the meta pipeline-orchestrator's dispatch
rules (see plugins/meta/agents/pipeline-orchestrator.md and
plugins/meta/skills/pipeline-orchestration/SKILL.md). It drives a design_state.json
through the open -> claimed -> fixed lifecycle so the closed-loop wiring can be
regression-tested without invoking live LLM orchestrators or EDA tools.

What it faithfully models:
  * servicer selection by each fix_request's ``route_to`` hint (default circuit-design,
    else behavioral-modeling / custom-layout / em-modeling);
  * re-validation routing back to the producer by ``created_by``;
  * the cross-domain iteration cap (``>=`` against
    ``pipeline_config.max_cross_domain_iterations``, default 3) -> escalation;
  * the checkpoint gate (``pipeline_config.checkpoints`` vs ``approved_checkpoints``);
  * the sign-off criteria (no open/claimed fix_requests, all checkpoints approved,
    ``pending_approval == null``), archiving resolved entries.

A ``scenario.json`` beside each design's ``design_state.json`` says how each servicer
responds (which cycle, if any, the re-validation passes) and which checkpoints the
user approves. Usage:

    python3 tests/e2e/run_pipeline.py examples/designs/lna_nf
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "docs" / "design_state.schema.json"

# failure_class -> retry_strategy (authoritative map, mirrors the SKILL + schema).
RETRY_MAP = {
    "none": "none", "functional": "refine", "spec_violation": "refine",
    "matching": "refine", "yield": "refine", "convergence": "regenerate",
    "drc_lvs": "regenerate", "connectivity": "refine", "reliability": "refine",
    "tool_error": "regenerate", "spec_gap": "escalate", "resource_limit": "escalate",
}

# route_to hint -> servicer orchestrator (default circuit-design when absent).
SERVICER_BY_ROUTE = {
    "circuit-design": "circuit-design-orchestrator",
    "behavioral-modeling": "behavioral-modeling-orchestrator",
    "custom-layout": "custom-layout-orchestrator",
    "em-modeling": "em-modeling-orchestrator",
}

# created_by producer -> re-validation orchestrator.
REVALIDATOR_BY_CREATOR = {
    "circuit-simulation-orchestrator": "circuit-simulation-orchestrator",
    "post-layout-signoff-orchestrator": "post-layout-signoff-orchestrator",
    "parasitic-extraction-orchestrator": "post-layout-signoff-orchestrator",
    "ams-verification-orchestrator": "ams-verification-orchestrator",
    "physical-verification-orchestrator": "physical-verification-orchestrator",
    "ams-integration-orchestrator": "ams-integration-orchestrator",
    "rf-design-orchestrator": "rf-design-orchestrator",
}


class PipelineError(Exception):
    pass


def servicer_for(fr: dict) -> str:
    route = fr.get("route_to") or "circuit-design"
    if route not in SERVICER_BY_ROUTE:
        raise PipelineError(f"fix_request {fr['id']}: unknown route_to {route!r}")
    return SERVICER_BY_ROUTE[route]


def revalidator_for(fr: dict) -> str:
    creator = fr.get("created_by")
    if creator not in REVALIDATOR_BY_CREATOR:
        raise PipelineError(f"fix_request {fr['id']}: unknown created_by {creator!r}")
    return REVALIDATOR_BY_CREATOR[creator]


class Clock:
    """Monotonic synthetic ISO-8601 timestamps for reproducible traces."""

    def __init__(self) -> None:
        self._n = 0

    def now(self) -> str:
        self._n += 1
        return f"2026-03-10T12:{self._n // 60:02d}:{self._n % 60:02d}Z"


def _append_history(state: dict, clock: Clock, stage: str, decision: str,
                    failure_class: str, next_step: str, reason: str,
                    constraint_ref=None) -> None:
    state.setdefault("history", []).append({
        "timestamp": clock.now(),
        "agent": "pipeline-orchestrator",
        "stage": stage,
        "decision": decision,
        "confidence": "high",
        "failure_class": failure_class,
        "retry_strategy": RETRY_MAP[failure_class],
        "suggested_next_step": next_step,
        "reason": reason,
        "constraint_ref": constraint_ref,
    })


def run(state: dict, scenario: dict, validate: bool = True) -> dict:
    """Drive the cross-domain loop. Returns {outcome, state, trace, cross_domain_iterations}."""
    state = copy.deepcopy(state)
    state.setdefault("format_version", "1.0")
    clock = Clock()
    trace: list[str] = []

    validator = _make_validator() if validate else None

    def checkpoint(label: str) -> None:
        if validator is not None:
            errs = sorted(validator.iter_errors(state), key=lambda e: list(e.path))
            if errs:
                msgs = "; ".join(f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}"
                                 for e in errs[:5])
                raise PipelineError(f"schema violation after {label}: {msgs}")

    # --- intake: halt on any pre-existing pending_approval -------------------
    if state.get("pending_approval"):
        pa_type = state["pending_approval"].get("type", "escalation")
        trace.append(f"intake: halt on pending_approval ({pa_type})")
        return _result(f"halt_{pa_type}", state, trace)

    cap = (state.get("pipeline_config") or {}).get("max_cross_domain_iterations", 3)
    state["pipeline_session_id"] = state.get("pipeline_session_id") or "ps_e2e"
    responses = scenario.get("servicer_responses", {})

    # --- detect + service each open fix_request ------------------------------
    for fr in state.get("fix_requests", []):
        if fr.get("status") not in ("open", "claimed"):
            continue
        servicer = servicer_for(fr)
        revalidator = revalidator_for(fr)
        resp = responses.get(fr["id"], {})
        fixed_on = resp.get("fixed_on_iteration")  # int (1-based cycle) or None
        trace.append(f"detect: {fr['id']} -> servicer={servicer}, revalidator={revalidator}")

        while fr["status"] in ("open", "claimed"):
            if state["cross_domain_iteration_count"] >= cap:
                state["pending_approval"] = {
                    "type": "escalation",
                    "agent": "pipeline-orchestrator",
                    "reason": (f"resource_limit: fix_request loop reached {cap} cross-domain "
                               f"iterations on {fr['id']} — relax the spec, raise the cap, "
                               f"or accept current QoR"),
                    "fix_request_id": fr["id"],
                }
                _append_history(state, clock, "dispatch_revalidation", "escalate",
                                "resource_limit", "escalate",
                                f"cap {cap} reached for {fr['id']}", fr["id"])
                trace.append(f"escalate: cap {cap} reached on {fr['id']}")
                checkpoint("cap escalation")
                return _result("escalate_cap", state, trace)

            # dispatch servicer: open -> claimed
            if fr["status"] == "open":
                fr["status"] = "claimed"
                fr.setdefault("history", []).append({
                    "timestamp": clock.now(), "agent": servicer,
                    "from_status": "open", "to_status": "claimed",
                    "note": f"Claimed by pipeline-orchestrator dispatch -> {servicer}",
                })
                _append_history(state, clock, "dispatch_circuit_design", "proceed",
                                "none", "proceed", f"dispatched {servicer} for {fr['id']}",
                                fr["id"])

            cycle = state["cross_domain_iteration_count"] + 1
            state["cross_domain_iteration_count"] = cycle
            trace.append(f"cycle {cycle}: {servicer} acts, {revalidator} re-validates {fr['id']}")

            spec_met = fixed_on is not None and cycle >= fixed_on
            if spec_met:
                fr["status"] = "fixed"
                fr["circuit_response"] = {
                    "fixed_at": clock.now(),
                    "diff_summary": resp.get("diff_summary", ""),
                    "files_changed": resp.get("files_changed", []),
                    "commit_ref": None,
                }
                fr.setdefault("history", []).append({
                    "timestamp": clock.now(), "agent": servicer,
                    "from_status": "claimed", "to_status": "fixed",
                    "note": f"Re-validated by {revalidator}; spec met",
                })
                _append_history(state, clock, "dispatch_revalidation", "proceed",
                                "none", "proceed",
                                f"{fr['id']} re-validated by {revalidator}", fr["id"])
                trace.append(f"cycle {cycle}: {fr['id']} fixed")
            else:
                fr["status"] = "open"  # re-validation failed; loop again
                _append_history(state, clock, "dispatch_revalidation", "proceed",
                                fr.get("failure_class", "spec_violation"),
                                "loop_back_to:dispatch_circuit_design",
                                f"{fr['id']} still failing after cycle {cycle}", fr["id"])
            checkpoint(f"cycle {cycle}")

    # --- checkpoint gate -----------------------------------------------------
    approved = {e["stage"] for e in state.get("approved_checkpoints", [])}
    granted = set(scenario.get("checkpoint_approvals", []))
    for cp in (state.get("pipeline_config") or {}).get("checkpoints", []):
        if cp in approved:
            continue
        if cp in granted:
            state.setdefault("approved_checkpoints", []).append({
                "stage": cp, "approved_at": clock.now(), "approved_by": "user",
            })
            approved.add(cp)
            trace.append(f"checkpoint: {cp} approved")
        else:
            state["pending_approval"] = {
                "type": "checkpoint",
                "agent": "pipeline-orchestrator",
                "reason": f"checkpoint gate: {cp} requires human approval before sign-off",
                "stage": cp,
            }
            _append_history(state, clock, "checkpoint_gate", "await_approval",
                            "none", "escalate", f"awaiting approval for {cp}", cp)
            trace.append(f"checkpoint: awaiting approval for {cp}")
            checkpoint("checkpoint gate")
            return _result("await_checkpoint", state, trace)

    # --- sign-off ------------------------------------------------------------
    still_open = [f for f in state.get("fix_requests", [])
                  if f.get("status") in ("open", "claimed")]
    if still_open:
        raise PipelineError(f"sign-off reached with open fix_requests: {still_open}")

    resolved = [f for f in state.get("fix_requests", []) if f.get("status") == "fixed"]
    state.setdefault("archive_fix_requests", []).extend(resolved)
    state["fix_requests"] = [f for f in state.get("fix_requests", [])
                             if f.get("status") not in ("fixed",)]
    state["pipeline_session_id"] = None
    _append_history(state, clock, "pipeline_signoff", "proceed", "none", "proceed",
                    "all fix_requests resolved and checkpoints approved", None)
    trace.append("signoff: pipeline complete")
    checkpoint("signoff")
    return _result("signoff", state, trace)


def _result(outcome: str, state: dict, trace: list) -> dict:
    return {
        "outcome": outcome,
        "state": state,
        "trace": trace,
        "cross_domain_iterations": state.get("cross_domain_iteration_count", 0),
    }


def _make_validator():
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return None
    if not SCHEMA_PATH.is_file():
        return None
    return Draft202012Validator(json.loads(SCHEMA_PATH.read_text()))


def load_design(design_dir) -> tuple[dict, dict]:
    d = Path(design_dir)
    state = json.loads((d / "design_state.json").read_text())
    scenario_path = d / "scenario.json"
    scenario = json.loads(scenario_path.read_text()) if scenario_path.is_file() else {}
    return state, scenario


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("design_dir", help="Directory holding design_state.json + scenario.json")
    parser.add_argument("--no-validate", action="store_true",
                        help="Skip JSON-schema validation of intermediate states")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.design_dir):
        print(f"ERROR: not a directory: {args.design_dir}", file=sys.stderr)
        return 2

    state, scenario = load_design(args.design_dir)
    try:
        result = run(state, scenario, validate=not args.no_validate)
    except PipelineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"design: {state.get('design_name')}  outcome: {result['outcome']}  "
          f"iterations: {result['cross_domain_iterations']}\n")
    for line in result["trace"]:
        print(f"  {line}")

    expect = scenario.get("expect", {})
    exp_outcome = expect.get("outcome")
    if exp_outcome and exp_outcome != result["outcome"]:
        print(f"\nMISMATCH: expected outcome {exp_outcome!r}, got {result['outcome']!r}",
              file=sys.stderr)
        return 1
    print(f"\nOK: outcome {result['outcome']!r}")
    return 0 if result["outcome"] == "signoff" else 1


if __name__ == "__main__":
    sys.exit(main())
