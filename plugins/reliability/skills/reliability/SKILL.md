---
name: reliability
description: >
  Run electromigration, IR-drop, ESD, latch-up, and aging (HCI/NBTI) analyses on a
  signed-off analog layout and sign off long-term reliability. Use when verifying that
  power/signal routing and devices survive the rated current, voltage, and lifetime, or
  re-validating after a custom-layout / circuit-design fix_request was serviced. Opens
  fix_requests routed to custom-layout (EM/IR) or circuit-design (ESD).
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Reliability

## Invocation

- **If invoked by a user** presenting a reliability task: immediately spawn the
  `analog-chip-design-agents:reliability-orchestrator` agent and pass the full user request and
  any available context. Do not execute stages directly.
- **If invoked by the `reliability-orchestrator` mid-flow** (including re-validation): do not
  spawn a new agent. Treat this file as read-only — return the requested stage rules, sign-off
  criteria, or loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation and
must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/reliability/knowledge.md` — known EM/IR/ESD/latch-up/aging patterns, fixes, and
   PDK/tool quirks. Incorporate its guidance into every check.
2. `memory/reliability/run_state.md` — current run identity for resume-after-interruption.

## Purpose

Sign off long-term reliability of a physically-clean, extracted analog block: electromigration
(EM) current-density margin, IR-drop on the power grid, ESD protection, latch-up immunity, and
aging (HCI/NBTI) degradation over the rated lifetime. Six stages with explicit QoR gates. EM/IR
faults the design cannot self-resolve open a `fix_request` routed to custom-layout (widen/strap);
an ESD shortfall routes to circuit-design (add/resize clamps).

---

## Supported EDA Tools

### Open-Source
- **ngspice** (`ngspice`) — EM/IR estimation harnesses (branch currents → current density; grid
  IR from extracted R network)
- **KLayout** (`klayout`) — density / current-density scripts, wire-width auditing on the PEX'd GDS
- **Magic** (`magic`) — layer/width extraction feeding the EM current-density check

### Proprietary (detect-only — never installed)
- **Cadence Voltus / Legato Reliability** (`voltus`) — EM/IR + aging sign-off
- **Ansys RedHawk / Totem & PathFinder** (`redhawk`) — power-grid EM/IR and ESD
- **Siemens Calibre PERC** (`calibre`) — ESD / latch-up topology checks
- **Magwel** — 3-D EM/IR / ESD field solver

---

## Stage: em_analysis

### Domain Rules
1. Extract per-branch RMS/peak/average currents from the post-layout (PEX) netlist driven at the
   rated `constraints.specs` operating point; map each onto its metal-layer width from the layout.
2. Compare current density against the PDK EM limit per layer (Black's-equation budget at
   `constraints.corners.temp_c` max); compute `em_margin_pct` = (limit − actual) / limit × 100.
3. Bidirectional (AC/signal) vs unidirectional (DC/power) limits differ — apply the correct rule
   per net class; power/ground straps use the DC limit.
4. An EM violation the design cannot self-resolve opens a `fix_request` to custom-layout
   (`failure_class: drc_lvs`, widen/strap the net).

### QoR Metrics to Evaluate
- `em_margin_pct` ≥ 0 on every net (target ≥ 10% guard band)
- All power/ground straps within the DC EM limit at max temperature

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Current density over limit on a strap | fix_request → custom-layout (widen / add parallel strap) |
| Narrow signal net near a driver | fix_request → custom-layout (widen / shorten / split) |

### Output Required
- EM current-density report (per-net margin, worst offenders)

---

## Stage: ir_drop

### Domain Rules
1. Build the power-grid resistance network from the extracted netlist; inject the per-block
   current load and solve static (and dynamic, where switching loads exist) IR drop.
2. Compute `ir_drop_pct` = worst (vdd_rail − local_vdd) / `constraints.supply.vdd_v` × 100; the
   local supply at every device must stay within the analog headroom budget.
3. Check ground bounce symmetrically on the vss network — analog matching is sensitive to it.
4. An IR-drop violation opens a `fix_request` to custom-layout (strap/mesh the grid).

### QoR Metrics to Evaluate
- `ir_drop_pct` ≤ budget (default ≤ 5% of vdd unless `constraints` tightens it)
- Ground bounce within the same budget on vss

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Excessive droop at a far device | fix_request → custom-layout (add grid strap / widen rail) |
| Single-point grid feed | fix_request → custom-layout (mesh the grid / add vias) |

### Output Required
- IR-drop map / report (worst-case droop, grid weak points)

---

## Stage: esd_check

### Domain Rules
1. Verify every pad/IO has a complete ESD path (clamp + diodes) meeting the target protection
   level (e.g. 2 kV HBM); check clamp trigger/hold and series-resistance budget.
2. Confirm cross-domain (supply-to-supply) clamps exist and the discharge current path has
   adequate metal width (ties into EM).
3. An ESD shortfall is a circuit-topology gap, not a routing fault: open a `fix_request` to
   circuit-design (`failure_class: spec_violation`, add/resize the clamp).

### QoR Metrics to Evaluate
- `esd_violations` = 0 (every IO/supply has a qualified discharge path)
- Clamp size / series resistance within the protection budget

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Missing / undersized clamp | fix_request → circuit-design (add / resize ESD device) |
| Discharge metal too narrow | fix_request → custom-layout (widen the ESD bus) |

### Output Required
- ESD coverage report (per-IO path + clamp adequacy)

---

## Stage: latchup_check

### Domain Rules
1. Run topology/geometry latch-up checks: well/substrate tap density and spacing, guard-ring
   continuity around injectors (IO drivers, large switches), n+/p+ spacing rules.
2. Confirm guard rings separate noisy/high-current devices from sensitive analog wells.
3. Latch-up fixes are usually layout (taps/rings): route to custom-layout; a missing guard-ring
   *intent* may route to circuit-design.

### QoR Metrics to Evaluate
- Tap spacing / guard-ring rules pass (0 violations)
- Injector-to-sensitive-well separation within the PDK latch-up rule

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Tap too far from device | fix_request → custom-layout (add well/substrate tap) |
| Missing guard ring at an injector | fix_request → custom-layout (add guard ring) |

### Output Required
- Latch-up check report (tap/guard-ring status)

---

## Stage: aging_analysis

### Domain Rules
1. Apply HCI/NBTI/PBTI aging models at the rated lifetime (e.g. 10 yr) and worst-case
   temperature/voltage corner; re-simulate the key `constraints.specs` on the aged netlist.
2. Compute degradation (e.g. Vth shift, gm/gain loss) and confirm post-aging specs still meet
   their margins; flag the worst-aging device.
3. A fresh-vs-aged spec failure is a design-margin gap: open a `fix_request` to circuit-design
   (`failure_class: spec_violation`, add margin / de-rate stress).

### QoR Metrics to Evaluate
- Post-aging key specs within margin at end-of-life
- Aging degradation (gain/offset/Vth shift) within the budget

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Spec drifts out of range when aged | fix_request → circuit-design (add margin / lower stress) |
| One device dominates aging | fix_request → circuit-design (up-size / re-bias the stressed device) |

### Output Required
- Aging report (degradation per spec, end-of-life margins)

---

## Stage: reliability_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| EM | `em_margin_pct` ≥ 0 on every net (≥ 10% guard preferred) |
| IR-drop | `ir_drop_pct` ≤ budget (default 5% of vdd) |
| ESD | `esd_violations` = 0 (every IO/supply qualified) |
| Latch-up | tap/guard-ring rules pass |
| Aging | end-of-life specs within margin |

### Domain Rules
1. Confirm EM, IR, ESD, latch-up, and aging all pass (or carry only documented waivers).
2. Mark the block reliability-clean and hand off to characterization / tape-out.
3. Close any serviced `fix_request` re-validations as PASS.

### Failure Escalation
- EM / IR fail → `fix_request` (`failure_class: drc_lvs`) → custom-layout (widen / strap)
- ESD / aging spec fail → `fix_request` (`failure_class: spec_violation`) → circuit-design
- Latch-up tap/ring fail → `fix_request` (`failure_class: drc_lvs`) → custom-layout

### Output Required
- Reliability sign-off report (EM, IR, ESD, latch-up, aging)
- `fix_request` entries for any unresolved violations

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`em_analysis`) — hard-fail if missing:**
- `design_state.layout.gds` — the signed-off layout (for metal widths / current density)
- `design_state.pex.netlist` (or `design_state.post_layout`) — the extracted netlist for current
  / IR solving
- `constraints.pdk` — for EM limits, ESD/latch-up rules, aging models
- `constraints.supply.vdd_v` — for IR-drop percentage and ESD budgets

Skip constraint validation entirely when invoked in re-validation / fix-request-servicing mode
(a `fix_request.id` was passed in the prompt).

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/reliability/run_state.md` as the **first action**:
```markdown
run_id:      reliability_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/reliability/experiences.jsonl`
keyed by `run_id`. `key_metrics` fields: `em_margin_pct`, `ir_drop_pct`, `esd_violations`. Set
`signoff_achieved: false` until reliability_signoff passes; then `true`. Create the file and
parent directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each EM/IR/ESD fix as an
observation to entity `analog-design-reliability-fixes` after writing to `experiences.jsonl`.
Skip silently if absent — the JSONL file is the canonical record.
