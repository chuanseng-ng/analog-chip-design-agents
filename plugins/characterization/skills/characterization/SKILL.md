---
name: characterization
description: >
  Characterize timing, power, and noise of a signed-off analog/mixed macro across PVT corners
  and generate validated Liberty (.lib) + behavioral models for downstream integration. Use when
  building the abstract views a chip-level / digital flow consumes, or re-running after a setup
  fix. Loop-backs are stage-local (model_validation → char_setup); a fundamental model gap escalates.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Characterization

## Invocation

- **If invoked by a user** presenting a characterization task: immediately spawn the
  `analog-chip-design-agents:characterization-orchestrator` agent and pass the full user request
  and any available context. Do not execute stages directly.
- **If invoked by the `characterization-orchestrator` mid-flow** (including re-validation): do not
  spawn a new agent. Treat this file as read-only — return the requested stage rules, sign-off
  criteria, or loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation and
must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/characterization/knowledge.md` — known .lib generation patterns, sweep/corner recipes,
   monotonicity fixes, and PDK/tool quirks. Incorporate its guidance into every stage.
2. `memory/characterization/run_state.md` — current run identity for resume-after-interruption.

## Purpose

Produce the validated abstract views of a signed-off, extracted analog/mixed macro: timing, power,
and noise characterized across the required PVT corners, written as Liberty (`.lib`) plus
behavioral models, and validated against SPICE. Seven stages with explicit QoR gates.
Characterization is a **terminal consumer** — its loop-backs are stage-local retries
(`model_validation → char_setup`); it does not open cross-domain `fix_request`s. A characterization
that cannot converge on a valid model after the retry cap escalates to the user.

---

## Supported EDA Tools

### Open-Source
- **ngspice** / **Xyce** (`ngspice` / `xyce`) — sweep harnesses driving the characterization grid
- **Python `.lib` writers** — emit NLDM/CCS-style Liberty tables from the sweep results
- **scipy / numpy** — monotonicity checks, interpolation, model fitting

### Proprietary (detect-only — never installed)
- **Cadence Liberate** (`liberate`) — characterization + .lib generation
- **Synopsys SiliconSmart** (`siliconsmart`)
- **Siemens Solido ML Characterization** (`solido`)
- **Altos** (legacy)

---

## Stage: char_setup

### Domain Rules
1. Read the macro interface (pins, supplies, analog/digital boundary) from the signed-off
   `design_state.pex.netlist` (preferred) or `circuit.netlist`; identify the arcs/measurements to
   characterize (timing arcs, power states, noise bands).
2. Build the corner/voltage/temperature grid from `constraints.corners` (process × `voltage_pct` ×
   `temp_c`); record `corners_covered`. Define the input slew / output load index axes.
3. Validate the testbench harness drives every required measurement before launching the sweep.

### QoR Metrics to Evaluate
- Full corner/slew/load grid defined (`corners_covered` = required count)
- Every required arc/measurement has a testbench

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Missing corner in the grid | extend the sweep matrix from `constraints.corners` |
| Undriven arc/measurement | add the measurement to the harness before sweeping |

### Output Required
- Characterization setup (corner grid, index axes, arc list, harness)

---

## Stage: timing_char

### Domain Rules
1. Sweep the timing arcs over the slew × load grid at every corner; extract delay and transition
   (and constraint arcs — setup/hold — where the macro has clocked boundaries).
2. Populate NLDM (and CCS where required) tables; confirm the index ranges bracket the real
   operating slews/loads (no extrapolation at use).
3. Record `lib_arcs` (count of characterized arcs).

### QoR Metrics to Evaluate
- All timing arcs characterized across the grid (no holes)
- Index ranges bracket the integration operating point

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Table hole / NaN at a corner | re-run the failing sweep point; widen convergence settings |
| Operating point outside the index range | extend slew/load axes and re-sweep |

### Output Required
- Timing tables (delay / transition / constraint per arc per corner)

---

## Stage: power_char

### Domain Rules
1. Characterize leakage (per state) and internal/switching power over the same grid; capture
   state-dependent leakage for analog bias branches.
2. Confirm power scales sensibly with voltage/temperature (a non-physical sign flip signals a
   measurement error).

### QoR Metrics to Evaluate
- Leakage + internal power characterized across the grid
- Power trends physically monotonic vs V/T (no sign flips)

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Implausible leakage at a corner | re-measure with the correct bias state |
| Power non-monotonic vs voltage | check the measurement window / settling time |

### Output Required
- Power tables (leakage + dynamic per state per corner)

---

## Stage: noise_char

### Domain Rules
1. Characterize the analog-relevant noise (input-referred noise, PSRR/CMRR vs frequency where the
   macro spec defines them) across corners; emit as model parameters or a noise view.
2. Confirm noise degrades monotonically with the expected stressors; flag outliers for re-sim.

### QoR Metrics to Evaluate
- Noise characterized across the required corners
- Noise trends consistent (no unexplained outliers)

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Noise outlier at one corner | re-run with a longer transient / finer AC grid |
| PSRR/CMRR band missing | extend the frequency sweep to the spec band |

### Output Required
- Noise tables / view (input-referred noise, PSRR/CMRR vs freq)

---

## Stage: liberty_generation

### Domain Rules
1. Assemble the timing/power/noise tables into a complete `.lib` per corner (correct
   `operating_conditions`, units, library/cell headers, pin directions, related-pin arcs).
2. Confirm completeness: every pin, arc, and required corner present; `compute lib_arcs` total
   matches the characterized set.
3. Lint the generated `.lib` (parse-clean, no missing default templates).

### QoR Metrics to Evaluate
- `.lib` parse-clean and complete (all pins/arcs/corners)
- Units / operating_conditions correct per corner

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Missing arc/pin in .lib | back-fill from timing/power tables; re-emit |
| Wrong operating_conditions/units | fix the header template; regenerate |

### Output Required
- Liberty (`.lib`) files, one per required corner

---

## Stage: model_validation

### Domain Rules
1. Re-simulate the macro at independent spot checks (corner/slew/load points not on the
   characterization grid nodes) and compare the `.lib`/behavioral-model prediction against SPICE;
   compute `char_error_pct` = max |model − spice| / spice × 100.
2. Check **monotonicity** of every NLDM table (delay/transition must not invert across the index)
   — a non-monotonic table breaks downstream timing and is a hard fail.
3. On a validation failure (error over budget or non-monotonic table), loop back to `char_setup`
   (max 2×) to refine the grid/measurement; if still failing after the cap, escalate to the user.

### QoR Metrics to Evaluate
- `char_error_pct` ≤ budget (default ≤ 5% vs SPICE)
- Every table monotonic across its index axes

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Model error over budget | loop back → char_setup (densify the grid / fix the measurement) |
| Non-monotonic NLDM table | loop back → char_setup (add index points / re-measure the inflection) |

### Output Required
- Validation report (model-vs-SPICE error, monotonicity per table)

---

## Stage: char_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| Completeness | `.lib` complete across every required corner (all pins/arcs) |
| Accuracy | `char_error_pct` ≤ budget (default 5% vs SPICE) |
| Coverage | `corners_covered` = required corner/voltage/temperature count |
| Monotonicity | every characterized table monotonic |

### Domain Rules
1. Confirm completeness, accuracy, coverage, and monotonicity all pass.
2. Mark the macro characterized and publish the `.lib` + behavioral models for integration.
3. Close any serviced re-validation as PASS.

### Failure Escalation
- Validation fail after the retry cap → escalate to the user with the failing
  corner/arc/error and a recommendation (do **not** open a cross-domain fix_request — a
  fundamental, design-level gap is reported to the user, who may route it to circuit-design).

### Output Required
- Characterization sign-off report (completeness, accuracy, coverage, monotonicity)
- Published `.lib` + behavioral models

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`char_setup`) — hard-fail if missing:**
- `design_state.pex.netlist` (or `design_state.circuit.netlist`) — the netlist to characterize
- `constraints.pdk` — for device models / corner definitions
- `constraints.corners` — process / `voltage_pct` / `temp_c` defining the characterization grid

Skip constraint validation entirely when invoked in re-validation / fix-request-servicing mode
(a `fix_request.id` was passed in the prompt).

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/characterization/run_state.md` as the **first action**:
```markdown
run_id:      characterization_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/characterization/experiences.jsonl`
keyed by `run_id`. `key_metrics` fields: `lib_arcs`, `char_error_pct`, `corners_covered`. Set
`signoff_achieved: false` until char_signoff passes; then `true`. Create the file and parent
directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each validation fix as an
observation to entity `analog-design-characterization-fixes` after writing to `experiences.jsonl`.
Skip silently if absent — the JSONL file is the canonical record.
