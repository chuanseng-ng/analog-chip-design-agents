---
name: post-layout-signoff
description: >
  Run post-PEX corner and Monte-Carlo simulation on the extracted netlist, re-verify specs
  against the pre-layout design, and gate tape-out. Use when closing a block's specs on the
  extracted netlist, quantifying parasitic degradation, or driving the tape-out approval gate.
  Opens fix_requests routed to custom-layout or circuit-design on post-layout spec loss.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Post-Layout Sign-off

## Invocation

- **If invoked by a user** presenting a post-layout sign-off task: immediately spawn the
  `analog-chip-design-agents:post-layout-signoff-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `post-layout-signoff-orchestrator` mid-flow** (including re-validation):
  do not spawn a new agent. Treat this file as read-only — return the requested stage rules,
  sign-off criteria, or loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation
and must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/post-layout/knowledge.md` — known parasitic-degradation patterns, stability/CMRR
   loss recipes, corner re-sim pitfalls. Incorporate its guidance into every analysis.
2. `memory/post-layout/run_state.md` — current run identity for resume-after-interruption.

## Purpose

Close the design on the extracted (PEX) netlist: re-run corners/Monte-Carlo, re-verify specs
versus the pre-layout design, quantify parasitic degradation, and gate tape-out. Five stages
with explicit QoR gates. On a post-layout spec loss the sign-off cannot absorb, this domain
opens a `fix_request` routed to custom-layout (parasitic reduction) or circuit-design
(re-design). The final `tapeout_signoff` stage is a human-approval checkpoint.

---

## Supported EDA Tools

### Open-Source
- **ngspice** (`ngspice`) / **Xyce** (`Xyce`) — corner/MC simulation on the extracted netlist
- **PySpice** (`python -m PySpice`) — scripted corner / Monte-Carlo orchestration and post-processing

### Proprietary (detect-only — never installed)
- **Cadence Spectre / Spectre X / APS** (`spectre`)
- **Synopsys PrimeSim / FineSim** (`primesim`)
- **Siemens AFS (Analog FastSPICE)** (`afs`)

---

## Stage: pex_netlist_assembly

### Domain Rules
1. Assemble the post-layout testbench around the PEX netlist from `design_state.pex.netlist`, reusing the pre-layout `.measure` testbench so specs compare like-for-like.
2. Confirm device/net names map between the PEX netlist and the testbench; resolve any unmapped probes.
3. Include the PDK model corners and the sign-off corner set from `constraints.corners`.

### QoR Metrics to Evaluate
- PEX netlist + testbench assemble and name-map
- Sign-off corner set present

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Probe net not found in PEX | Re-map names; re-extract with preserved net names |
| Missing corner includes | Add the PDK corner `.lib` lines |

### Output Required
- Assembled post-layout testbench (PEX netlist + `.measure`)

---

## Stage: post_layout_corner_sim

### Domain Rules
1. Re-run AC/transient/noise `.measure` across every corner in `constraints.corners` (and Monte-Carlo where yield matters) on the extracted netlist.
2. Collect the worst-case per spec and the limiting corner, exactly as circuit-simulation does pre-layout.
3. Use tight solver tolerances; the added parasitics can change convergence — re-tune options, not specs.

### QoR Metrics to Evaluate
- All specs measured at every corner on the extracted netlist
- Limiting corner identified per spec

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Non-convergence with parasitics | Re-tune solver options / `.nodeset` (don't relax specs) |
| Corner missing | Add the corner to the sweep |

### Output Required
- Post-layout corner matrix (spec × corner, worst-case highlighted)

---

## Stage: spec_reverification

### Domain Rules
1. Compare each post-layout spec against `constraints.specs` (the same gates circuit-simulation used); a miss at any corner is a post-layout `spec_violation`.
2. Attribute each miss to its parasitic cause (added C on a high-Z node, coupling, R on a bias line) to choose the fix route.
3. Decide the route: parasitic-reduction faults → custom-layout; fundamental margin loss → circuit-design.

### QoR Metrics to Evaluate
- Every spec passes at every corner on the extracted netlist
- Each miss attributed to a parasitic cause

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| PM/CMRR lost to coupling | `fix_request` → custom-layout (shield/re-route), `route_to: custom-layout` |
| Fundamental margin loss | `fix_request` → circuit-design (re-compensate), `route_to: circuit-design` |

### Output Required
- Spec-reverification table (pre- vs post-layout, cause per miss)

---

## Stage: margin_analysis

### Domain Rules
1. Quantify degradation vs pre-layout per spec (`spec_degradation_pct`) and the remaining margin at the limiting corner.
2. Flag parasitic-induced stability / CMRR / PSRR loss explicitly; confirm phase margin (`worst_pm_deg`) still meets spec with margin.
3. Assess Monte-Carlo yield on the extracted netlist where applicable.

### QoR Metrics to Evaluate
- `spec_degradation_pct` within the acceptable budget
- `worst_pm_deg` ≥ `specs.phase_margin_deg` with margin
- `failing_corners` = 0

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Degradation over budget | `fix_request` (custom-layout or circuit-design per cause) |
| Stability margin thin | `fix_request` → circuit-design (re-compensate) |

### Output Required
- Margin / degradation analysis (per spec, vs pre-layout)

---

## Stage: tapeout_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| Post-layout specs | pass at all sign-off corners on the extracted netlist |
| Degradation | `spec_degradation_pct` within budget |
| Stability | `worst_pm_deg` ≥ `specs.phase_margin_deg` with margin |
| Yield | Monte-Carlo yield ≥ `constraints.yield.target_sigma` (where applicable) |
| Tape-out gate | `tapeout_signoff` checkpoint approved (human) |

### Domain Rules
1. Confirm every post-layout spec passes with margin and degradation is within budget.
2. Honour the `tapeout_signoff` checkpoint — halt for human approval before declaring tape-out ready.
3. Produce the tape-out checklist; close any serviced `fix_request` re-validations as PASS.

### Failure Escalation
- Post-layout spec miss (parasitic) → `fix_request` (`spec_violation`, `route_to: custom-layout`)
- Post-layout spec miss (fundamental) → `fix_request` (`spec_violation`, `route_to: circuit-design`)
- Loop exceeds cap → escalate at the tape-out gate

### Output Required
- Post-layout sign-off report
- Margin / degradation analysis
- Tape-out checklist + `fix_request` entries for any unresolved violations

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`pex_netlist_assembly`) — hard-fail if missing:**
- `design_state.pex.netlist` — the extracted netlist to sign off
- at least one non-null entry in `constraints.specs` — the specs to re-verify
- `constraints.corners.process` (≥ 1) — the sign-off corner set

**Optional (schema defaults apply when absent):**
- `constraints.specs.phase_margin_deg` (default: 60)
- `constraints.yield.target_sigma` (default: 3)

Skip constraint validation entirely when invoked in re-validation / fix-request-servicing mode.

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/post-layout/run_state.md` as the **first action**:
```markdown
run_id:      post-layout_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/post-layout/experiences.jsonl`
keyed by `run_id`. `key_metrics` fields: `worst_pm_deg`, `spec_degradation_pct`,
`failing_corners`. Set `signoff_achieved: false` until tapeout_signoff passes; then `true`.
Create the file and parent directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each post-layout fix as an
observation to entity `analog-design-post-layout-fixes` after writing to `experiences.jsonl`.
Skip silently if absent — the JSONL file is the canonical record.
