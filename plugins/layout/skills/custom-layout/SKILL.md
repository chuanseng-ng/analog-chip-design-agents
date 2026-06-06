---
name: custom-layout
description: >
  Floorplan, generate matched devices, and place/route analog blocks with symmetry, shielding,
  and matching constraints to a clean, DRC-ready layout. Use when turning a sign-off-ready
  schematic into a GDS layout, or servicing a fix_request that repairs the layout after a
  DRC/LVS or parasitic-degradation failure.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Custom Layout

## Invocation

- **If invoked by a user** presenting a layout task: immediately spawn the
  `analog-chip-design-agents:custom-layout-orchestrator` agent and pass the full user request
  and any available context. Do not execute stages directly.
- **If invoked by the `custom-layout-orchestrator` mid-flow** (including fix-request
  servicing): do not spawn a new agent. Treat this file as read-only — return the requested
  stage rules, sign-off criteria, or loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation
and must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/layout/knowledge.md` — known matching recipes, density/antenna fixes, PDK layer
   quirks. Incorporate its guidance into every placement/routing decision.
2. `memory/layout/run_state.md` — current run identity (`run_id`, `design_name`, `pdk`,
   `last_stage`) for resume-after-interruption.

## Purpose

Turn a sign-off-ready schematic + netlist into a DRC-ready GDS layout that honours analog
matching, symmetry, and shielding constraints. Six stages with explicit QoR gates and
loop-back criteria enforced by the custom-layout orchestrator. Custom-layout also **services**
fix_requests routed to it (DRC/LVS repairs from physical-verification; parasitic-reduction
from post-layout / extraction).

---

## Supported EDA Tools

### Open-Source
- **Magic** (`magic`) — layout editor + DRC/extraction; sky130/gf180mcu/ihp-sg13g2 support (freepdk45/asap7 predictive PDKs are usable but academic — asap7 FinFET/multi-patterning rules are best handled in KLayout)
- **KLayout** (`klayout`) — layout viewer/editor, DRC/LVS decks, scripting (Python/Ruby)
- **gdsfactory / gdstk** (`python -m gdsfactory`) — programmatic GDS generation
- **ALIGN** / **MAGICAL** — analog layout automation (place & route)
- **BAG / BAG3** layout generators — generator-based parametric layout

### Proprietary (detect-only — never installed)
- **Cadence Virtuoso Layout** (`virtuoso`) — XL / GXL / EAD (constraint-driven, electrically-aware)
- **Synopsys Custom Compiler Layout** (`custom_compiler`)
- **Siemens Tanner L-Edit** (`l-edit`)
- **Silvaco Expert** — full-custom layout

---

## Stage: layout_floorplan

### Domain Rules
1. Read the block hierarchy and area target from `design_state.architecture` / `design_state.circuit` and `constraints.area_um2`; allocate per-block regions with aspect ratios suited to matching.
2. Place symmetry axes and reserve channels for sensitive/bias routing; keep matched differential paths on a common axis.
3. Budget guard-ring / shielding area for noise-sensitive and high-Z nodes flagged in circuit-design's layout-sensitivity notes.
4. Reserve area for fill, dummies, and antenna diodes so later finishing does not overflow the floorplan.

### QoR Metrics to Evaluate
- Floorplan area ≤ `constraints.area_um2` with ≥ 10% reserve
- Symmetry axes defined for all matched pairs
- Sensitive-net channels reserved

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Aspect ratio fights matching | Re-shape the block region; rotate to align matched gates |
| No room for guard rings | Re-budget floorplan; merge non-critical blocks |

### Output Required
- Floorplan (block regions, symmetry axes, reserved channels)

---

## Stage: device_generation

### Domain Rules
1. Generate matched devices with common-centroid / interdigitation per the circuit-design matching flags; equal L, integer-ratio W, same orientation.
2. Add dummy devices at array edges to equalise the lithographic environment of matched pairs.
3. Use the PDK's recommended device generators / PCells; never hand-draw matched arrays where a generator exists.
4. Tie bulks/wells correctly at the device level and stamp well-tap rings on matched arrays.

### QoR Metrics to Evaluate
- Matched arrays common-centroid / interdigitated with edge dummies
- Bulk/well taps present on every array
- Devices pass cell-level DRC

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Mismatch from edge effects | Add/extend dummy rows; widen the common-centroid array |
| Missing well tap | Stamp tap ring; tie to the documented bias net |

### Output Required
- Generated matched-device cells + device-matching report

---

## Stage: analog_placement

### Domain Rules
1. Place devices symmetrically about the floorplan axes; keep matched pairs adjacent and equidistant from heat/IR sources.
2. Minimise the length and asymmetry of sensitive/high-Z nets; place the input pair away from digital/switching aggressors.
3. Group by current domain; keep high-current and small-signal devices separated to limit substrate/IR coupling.
4. Honour the routing channels reserved in the floorplan.

### QoR Metrics to Evaluate
- Symmetry of matched placements (mirror about the axis)
- Sensitive-net wirelength minimised
- Aggressor/victim separation respected

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Asymmetric matched placement | Mirror about the symmetry axis; equalise neighbour context |
| Input pair near aggressor | Re-place away from switching nets; add shielding |

### Output Required
- Placed layout with symmetry honoured

---

## Stage: analog_routing

### Domain Rules
1. Route matched/differential nets with equal length and symmetric layer usage; shield sensitive and bias lines with grounded guard traces.
2. Width-size power/bias routing for EM and IR; keep bias lines low-impedance.
3. Avoid routing aggressors over victims; insert shielding or spacing where coupling matters.
4. Keep antenna ratios within PDK limits as you route (defer diode insertion to finishing).

### QoR Metrics to Evaluate
- Matched-net length/layer symmetry
- Sensitive nets shielded; bias lines wide/low-Z
- No coupling-critical aggressor-over-victim crossings

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Matched nets length-mismatched | Add matched detours; route on symmetric layers |
| Coupling onto a high-Z node | Re-route with spacing; add a shield trace |

### Output Required
- Routed layout (matched, shielded sensitive nets)

---

## Stage: layout_finishing

### Domain Rules
1. Insert metal fill to meet density windows without violating sensitive-net spacing; exclude fill over matched/high-Z nodes where it perturbs matching.
2. Add antenna diodes where antenna ratios exceed PDK limits.
3. Add dummy fill and complete well/substrate taps; finalise seal-ring / IO context if at block top.
4. Re-confirm matching is not disturbed by fill/dummies.

### QoR Metrics to Evaluate
- Density within the PDK window
- Antenna ratios within limits
- Matching unperturbed by fill

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Fill perturbs matching | Add fill-exclude over matched/high-Z nets |
| Density below window | Add dummy fill in non-critical regions |

### Output Required
- Finished layout (fill, diodes, taps)

---

## Stage: layout_check

### Sign-off Pass Criteria (all must pass before hand-off to physical-verification)
| Check | Criterion |
|-------|-----------|
| Pre-DRC geometry | clean (no obvious spacing/width/density flags) |
| Matching/symmetry | matched arrays common-centroid + symmetric placement/routing |
| Shielding | sensitive/bias nets shielded |
| Antenna | ratios within PDK limits |
| Density | within the PDK window |

### Domain Rules
1. Run an in-tool geometry/DRC pre-check (Magic/KLayout) and resolve obvious violations before handing to physical-verification.
2. Confirm matching, symmetry, shielding, density, and antenna readiness against the QoR gates.
3. Hand off the GDS + device-matching report to physical-verification (DRC/LVS) and extraction.

### Failure Escalation
- Geometry/spacing fail → analog_routing (×3)
- Placement asymmetry fail → analog_placement (×3)
- Loop exceeds cap → escalate to the user

### Output Required
- GDS / layout database
- Device-matching report
- Pre-DRC summary + layout-sensitivity notes for extraction

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`layout_floorplan`) — hard-fail if missing:**
- `design_state.circuit.netlist` (or `schematic_ref`) — the design to lay out
- `constraints.pdk` — for layers, design rules, and device generators

**Optional (schema defaults apply when absent):**
- `constraints.area_um2` — area gating skipped (with a note) when absent

Skip constraint validation entirely when invoked in fix-request-servicing mode (a
`fix_request.id` was passed in the prompt).

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/layout/run_state.md` as the **first action** before launching any tool:
```markdown
run_id:      layout_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/layout/experiences.jsonl`
keyed by `run_id` (do not append a second line for the same run). `key_metrics` fields:
`matching_sigma_pct`, `density_pct`, `area_um2`. Set `signoff_achieved: false` until
layout_check passes; then `true`. Create the file and parent directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each applied fix as an
observation to entity `analog-design-layout-fixes` after writing to `experiences.jsonl`.
Skip silently if absent — the JSONL file is the canonical record.
