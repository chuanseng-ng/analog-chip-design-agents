---
name: ams-verification
description: >
  Build mixed-signal testbenches, define connect rules, run analog-digital co-simulation and
  real-number-model regressions, and close functional coverage. Use when verifying an
  analog/mixed-signal block against its digital control across corners, or re-validating
  after a model/circuit fix. Opens fix_requests routed to behavioral-modeling or circuit-design.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: AMS Verification

## Invocation

- **If invoked by a user** presenting a mixed-signal verification task: immediately spawn the
  `analog-chip-design-agents:ams-verification-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `ams-verification-orchestrator` mid-flow** (including re-validation):
  do not spawn a new agent. Treat this file as read-only — return the requested stage rules,
  sign-off criteria, or loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation
and must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/ams-verification/knowledge.md` — known co-sim sync pitfalls, connect-rule recipes,
   RNM-vs-SPICE divergence patterns, coverage-closure tactics. Incorporate its guidance.
2. `memory/ams-verification/run_state.md` — current run identity for resume-after-interruption.

## Purpose

Verify an analog/mixed-signal block against its digital control: build mixed-signal
testbenches, define connect rules, run analog-digital co-simulation and real-number-model
regressions, and close functional coverage. Six stages with explicit QoR gates. On a
mismatch the testbench cannot resolve, this domain opens a `fix_request` routed by the
pipeline-orchestrator to behavioral-modeling (model fault) or circuit-design (circuit fault).

---

## Supported EDA Tools

### Open-Source
- **cocotb** (`python -m cocotb`) + **ngspice** / **Xyce** — analog-digital co-simulation harness
- **Verilator** (`verilator`) / **Icarus** (`iverilog`) — digital + RNM regression
- **Xyce** (`Xyce`) — mixed-signal SPICE for the analog side

### Proprietary (detect-only — never installed)
- **Cadence Xcelium AMS / AMS Designer** (`xrun`) — AMS co-sim + coverage
- **Spectre AMS** (`spectre`) — analog engine for AMS
- **Synopsys VCS-AMS / CustomSim** (`vcs`) — AMS co-sim
- **Siemens Symphony + QuestaSim** — AMS + digital co-sim
- **AFS-driven co-sim** (`afs`) — fast-SPICE analog engine

---

## Stage: ams_testbench

### Domain Rules
1. Build the mixed-signal testbench around the DUT: instantiate the analog block (SPICE netlist from `design_state.circuit.netlist` or the behavioral model from `design_state.modeling`), the digital control, and the cocotb driver/monitor harness over ngspice/Xyce co-sim.
2. Define the functional intent as checkable assertions/scoreboards (cocotb coroutines) — every spec the AMS sim verifies must map to a pass/fail check, never a waveform eyeball.
3. Parameterise stimulus for corner/supply sweeps; seed randomisation deterministically for reproducible regressions.

### QoR Metrics to Evaluate
- Every verified spec maps to a pass/fail assertion or scoreboard
- DUT (netlist or model) instantiates cleanly in the co-sim harness
- Stimulus seeds are deterministic/reproducible

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Spec checked by eye | Add a cocotb assertion/scoreboard for it |
| Non-reproducible regression | Fix the RNG seed; record it in the testbench |
| DUT won't instantiate in harness | Reconcile port order / connect natures with the model/netlist |

### Output Required
- Mixed-signal testbench + cocotb driver/monitor harness
- Assertion/scoreboard list (spec → check)

---

## Stage: connect_module_setup

### Domain Rules
1. Define/import connect rules (E2L, L2E, bidirectional) for every analog↔digital boundary; thresholds supply-relative to `constraints.supply.vdd_v`. Reuse the modeling-domain connect modules where they exist (read `design_state.modeling.connect_modules`).
2. Verify no boundary relies on implicit/default connect-module insertion; count any implicit insertions as connect-rule errors.
3. Confirm drive-strength / resolution consistency so the same boundary behaves identically across the supply-corner range.

### QoR Metrics to Evaluate
- 100% of boundaries have an explicit connect rule (0 implicit insertions)
- Thresholds parameterised vs `supply.vdd_v`
- Drive-strength/resolution consistent across corners

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Implicit connect-module insertion | Add an explicit connect rule at the boundary |
| Boundary behaves differently at Vmin | Parameterise thresholds vs `supply.vdd_v` |

### Output Required
- Connect-rule map (boundary → rule), referencing reused modeling connect modules

---

## Stage: analog_digital_cosim

### Domain Rules
1. Run the cocotb + ngspice/Xyce co-simulation; synchronise the analog and digital time domains (lockstep or rollback) and verify the handshake produces consistent timestamps (no analog/digital time drift).
2. Compare co-sim behaviour against expected functional behaviour; on mismatch, root-cause whether the analog model/netlist is wrong (→ `fix_request` to behavioral-modeling or circuit-design) or the connect rule / testbench is wrong (→ loop back locally).
3. Classify a true analog-vs-expected behavioural mismatch as `functional` (the only `fix_request` class this stage opens — see `VALID_FR_FAILURE`).

### QoR Metrics to Evaluate
- Co-sim runs to completion with no analog/digital time drift
- All assertions pass; no unexpected functional mismatch
- Mismatches root-caused to model/circuit vs testbench

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Analog/digital time drift | Tighten sync step; enable rollback; align analog max-timestep to the digital tick |
| Functional mismatch (model wrong) | Open `fix_request` → behavioral-modeling (`functional`) |
| Functional mismatch (circuit wrong) | Open `fix_request` → circuit-design (`functional`) |

### Output Required
- Co-sim run report + waveforms
- Root-cause note for any mismatch (model / circuit / testbench)

---

## Stage: rnm_regression

### Domain Rules
1. Run the RNM regression suite (Verilator/Icarus + RNM); compare RNM behaviour against the SPICE/co-sim reference and count `rnm_mismatch_count` (cases where RNM diverges beyond tolerance).
2. Track `regression_failures` (failing testcases) across the seed/corner matrix; a single failing seed blocks sign-off.
3. On RNM-vs-SPICE divergence that indicts the model, open a `fix_request` to behavioral-modeling (`failure_class: functional`); on divergence that indicts the circuit, route to circuit-design.

### QoR Metrics to Evaluate
- `rnm_mismatch_count` = 0 (or within documented waivers)
- `regression_failures` = 0 across the seed/corner matrix

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| RNM diverges from SPICE | Re-validate RNM thresholds/quantisation (modeling `fix_request`) |
| Intermittent seed failure | Fix the underlying non-determinism; never waive a real divergence |

### Output Required
- RNM regression report (`rnm_mismatch_count`, `regression_failures` by seed/corner)

---

## Stage: coverage_closure

### Domain Rules
1. Measure functional coverage (covergroups / coverpoints over the spec-relevant state and corner space); close to the target. Coverage holes loop back to ams_testbench to add stimulus (cap 2×).
2. Ensure assertion coverage: every functional assertion has been exercised (not vacuously passing).
3. Distinguish a coverage *gap* (more stimulus needed → ams_testbench loop) from a coverage *fail caused by a real bug* (→ `fix_request`).

### QoR Metrics to Evaluate
- Functional coverage ≥ target (default ≥ 95%)
- Every assertion exercised (no vacuous passes)

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Coverage hole | Add directed/constrained-random stimulus in ams_testbench (loop ×2) |
| Vacuously-passing assertion | Add stimulus that drives the antecedent |

### Output Required
- Functional + assertion coverage report

---

## Stage: ams_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| Functional coverage | ≥ target `functional_coverage_pct` (default 95%) |
| RNM agreement | `rnm_mismatch_count` = 0 (unwaived) |
| Regression | `regression_failures` = 0 across seeds/corners |
| Connect modules | 100% explicit, 0 implicit insertions |
| Co-sim | clean, time-synchronised, all assertions exercised |

### Domain Rules
1. Confirm coverage, RNM agreement, and regression all pass with no open mismatch.
2. Confirm connect-module coverage is complete and the co-sim is time-synchronised.
3. Record results in `design_state.ams`; close any serviced `fix_request` re-validations as PASS.

### Failure Escalation
- Cosim/RNM functional mismatch → open `fix_request` (`failure_class: functional`) → behavioral-modeling or circuit-design
- Coverage gap → ams_testbench (×2)
- Missing connect rule → `connectivity`

### Output Required
- AMS sign-off report (coverage, RNM, regression, connect modules)
- Co-sim waveforms
- `fix_request` entries for any unresolved mismatch

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`ams_testbench`) — hard-fail if missing:**
- `constraints.supply.vdd_v` — for supply-relative connect-module thresholds
- a runnable DUT to verify — `design_state.circuit.netlist`, or a usable model artifact
  (`design_state.modeling.model_source` or `design_state.modeling.osdi`); a bare
  `design_state.modeling` object with no artifact does not qualify (else `spec_gap`)

**Optional (schema defaults apply when absent):**
- functional-coverage target (default 95%)
- `constraints.corners` (sweep matrix defaults to the nominal corner when absent)

Skip constraint validation entirely when invoked in re-validation / fix-request-servicing
mode (a `fix_request.id` was passed in the prompt).

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/ams-verification/run_state.md` as the **first action** before launching any tool:
```markdown
run_id:      ams-verification_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/ams-verification/experiences.jsonl`
keyed by `run_id` (do not append a second line for the same run). `key_metrics` fields:
`functional_coverage_pct`, `rnm_mismatch_count`, `regression_failures`. Set
`signoff_achieved: false` until ams_signoff passes; then `true`. Create the file and parent
directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each mismatch fix as an
observation to entity `analog-design-ams-verification-fixes` after writing to
`experiences.jsonl`. Skip silently if absent — the JSONL file is the canonical record.
