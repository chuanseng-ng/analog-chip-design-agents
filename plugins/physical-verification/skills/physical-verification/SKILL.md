---
name: physical-verification
description: >
  Run DRC, LVS, antenna/ERC, and density/DFM checks on an analog layout and sign off a
  physically-clean GDS. Use when verifying a custom layout against the foundry rule deck and
  the source netlist, or re-validating after a custom-layout fix_request was serviced. Opens
  fix_requests routed to custom-layout on DRC/LVS failures.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Physical Verification

## Invocation

- **If invoked by a user** presenting a physical-verification task: immediately spawn the
  `analog-chip-design-agents:physical-verification-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `physical-verification-orchestrator` mid-flow** (including re-validation):
  do not spawn a new agent. Treat this file as read-only — return the requested stage rules,
  sign-off criteria, or loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation
and must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/physical-verification/knowledge.md` — known DRC waiver patterns, LVS debug recipes,
   antenna fixes, PDK deck quirks. Incorporate its guidance into every check.
2. `memory/physical-verification/run_state.md` — current run identity for resume-after-interruption.

## Purpose

Verify a custom layout against the foundry rule deck and the source netlist: DRC, LVS,
antenna/ERC, and density/DFM, ending in a physically-clean sign-off. Five stages with explicit
QoR gates. On a DRC or LVS failure the layout cannot self-resolve, this domain opens a
`fix_request` routed by the pipeline-orchestrator to custom-layout.

---

## Supported EDA Tools

### Open-Source
- **Magic** (`magic`) — DRC and device extraction for LVS
- **Netgen** (`netgen`) — LVS (layout-vs-schematic netlist comparison)
- **KLayout** (`klayout`) — DRC / LVS decks (sky130/gf180mcu/ihp-sg13g2; predictive freepdk45/asap7, the latter with multi-patterning/coloring rules), antenna checks

### Proprietary (detect-only — never installed)
- **Siemens Calibre nmDRC / nmLVS** (`calibre`) — industry DRC/LVS sign-off
- **Synopsys IC Validator (ICV)** (`icv`)
- **Cadence Pegasus / Assura** (`pegasus`)
- **Silvaco Guardian** — DRC/LVS/ERC

---

## Stage: drc

### Domain Rules
1. Run the foundry DRC deck (Magic + KLayout) for the target `constraints.pdk`; resolve every violation to 0 unwaived.
2. Fix spacing/width/enclosure now; defer density/antenna-adjacent rules to their dedicated stages.
3. Document any intentional waiver with a foundry-acceptable justification; an undocumented waiver is a failure.
4. A DRC failure the layout cannot self-resolve opens a `fix_request` to custom-layout (`failure_class: drc_lvs`).

### QoR Metrics to Evaluate
- `drc_violations` = 0 (unwaived)
- All waivers documented

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Spacing/width violation | fix_request → custom-layout (re-route/re-space) |
| Enclosure/via rule | fix_request → custom-layout (fix the via stack) |

### Output Required
- DRC report (clean or with documented waivers)

---

## Stage: lvs

### Domain Rules
1. Extract the layout devices (Magic) and compare against the source `design_state.circuit.netlist` with Netgen; devices **and** nets must match.
2. Resolve shorts, opens, and device-parameter mismatches; a net mismatch is a `connectivity` fault, a device mismatch a `drc_lvs` fault.
3. Confirm bulk/well connectivity matches the schematic intent.
4. An LVS failure the layout cannot self-resolve opens a `fix_request` to custom-layout.

### QoR Metrics to Evaluate
- `lvs_errors` = 0 (devices + nets matched)
- Bulk/well connectivity matches schematic

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Net short/open | fix_request → custom-layout (`connectivity`) |
| Device parameter mismatch | fix_request → custom-layout (`drc_lvs`) |

### Output Required
- LVS report (device + net match status)

---

## Stage: antenna_erc

### Domain Rules
1. Run antenna checks; confirm gate antenna ratios are within PDK limits (diodes are added in custom-layout finishing).
2. Run geometric ERC: floating gates, missing taps, unintended high-impedance gate nets.
3. Route any residual antenna/ERC fixes back to custom-layout.

### QoR Metrics to Evaluate
- `antenna_violations` = 0
- ERC clean (no floating gates / missing taps)

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Antenna ratio exceeded | fix_request → custom-layout (add diode / jog metal) |
| Floating gate | fix_request → custom-layout (tie / add tap) |

### Output Required
- Antenna + ERC report

---

## Stage: density_dfm

### Domain Rules
1. Verify metal/poly density within the PDK window (per layer, per window); flag under/over-filled regions.
2. Run available DFM / recommended-rule checks; report (do not necessarily block) recommended-rule hits.
3. Route density fixes to custom-layout finishing (fill add/remove).

### QoR Metrics to Evaluate
- Density within the PDK window for every layer
- DFM recommended-rule hits reported

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Density below window | fix_request → custom-layout (add dummy fill) |
| Density above window | fix_request → custom-layout (thin fill near the net) |

### Output Required
- Density / DFM report

---

## Stage: pv_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| DRC | `drc_violations` = 0 (unwaived) |
| LVS | `lvs_errors` = 0 (devices + nets matched) |
| Antenna | `antenna_violations` = 0 |
| ERC | clean (no floating gates / missing taps) |
| Density | within the PDK window |

### Domain Rules
1. Confirm DRC, LVS, antenna, ERC, and density all pass (or carry only documented waivers).
2. Mark the layout physically clean and hand off to extraction.
3. Close any serviced `fix_request` re-validations as PASS.

### Failure Escalation
- DRC fail → `fix_request` (`failure_class: drc_lvs`) → custom-layout
- LVS net mismatch → `fix_request` (`failure_class: connectivity`) → custom-layout
- LVS device mismatch → `fix_request` (`failure_class: drc_lvs`) → custom-layout

### Output Required
- PV sign-off report (DRC, LVS, antenna, ERC, density)
- `fix_request` entries for any unresolved violations

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`drc`) — hard-fail if missing:**
- `design_state.layout.gds` — the layout to verify
- `constraints.pdk` — for the rule/extraction decks
- `design_state.circuit.netlist` — the LVS reference (required at `lvs`)

Skip constraint validation entirely when invoked in re-validation / fix-request-servicing mode
(a `fix_request.id` was passed in the prompt).

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/physical-verification/run_state.md` as the **first action**:
```markdown
run_id:      physical-verification_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in
`memory/physical-verification/experiences.jsonl` keyed by `run_id`. `key_metrics` fields:
`drc_violations`, `lvs_errors`, `antenna_violations`. Set `signoff_achieved: false` until
pv_signoff passes; then `true`. Create the file and parent directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each DRC/LVS fix as an
observation to entity `analog-design-physical-verification-fixes` after writing to
`experiences.jsonl`. Skip silently if absent — the JSONL file is the canonical record.
