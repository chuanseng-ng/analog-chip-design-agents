---
name: ams-integration
description: >
  Qualify analog IP, assemble the mixed-signal top, define boundary/connect rules, run chip-level
  AMS simulation, and check power intent through integration sign-off. Use when integrating
  signed-off analog/RF blocks into a mixed-signal top, or re-validating after an integration fix.
  Opens fix_requests routed to custom-layout, circuit-design, or behavioral-modeling.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Mixed-Signal Top Integration

## Invocation

- **If invoked by a user** presenting a mixed-signal top-integration task: immediately spawn the
  `analog-chip-design-agents:ams-integration-orchestrator` agent and pass the full user request
  and any available context. Do not execute stages directly.
- **If invoked by the `ams-integration-orchestrator` mid-flow** (including re-validation): do not
  spawn a new agent. Treat this file as read-only — return the requested stage rules, sign-off
  criteria, or loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation and
must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/ams-integration/knowledge.md` — known connect-rule pitfalls, supply-domain crossing
   recipes, ESD/IO-ring checklists, UPF/power-intent consistency tactics, top-LVS net-matching
   fixes. Incorporate its guidance.
2. `memory/ams-integration/run_state.md` — current run identity for resume-after-interruption.

## Purpose

Assemble the mixed-signal top from signed-off analog/RF/digital IP: qualify each block, build the
top netlist, define boundary/connect rules, run chip-level AMS simulation, and verify power intent
through integration sign-off. Six stages with explicit QoR gates. This is the **top-level
integration domain** — it consumes every upstream block's signed-off artifact and, on a fault it
cannot absorb, opens a `fix_request` the pipeline-orchestrator routes to the offending domain
(custom-layout for a top-LVS/connectivity fault, circuit-design for a functional/spec miss,
behavioral-modeling for a connect-module/RNM fault).

---

## Supported EDA Tools

### Open-Source
- **cocotb** (`python -m cocotb`) + **ngspice** / **Xyce** — chip-level analog-digital co-sim
- **KLayout** (`klayout`) / **Magic** (`magic`) + **Netgen** (`netgen`) — top-level LVS / connectivity
- **Verilator** (`verilator`) / **Icarus** (`iverilog`) — digital + RNM at the top

### Proprietary (detect-only — never installed)
- **Cadence Virtuoso** (`virtuoso`) — top assembly / hierarchy editor
- **Cadence Xcelium AMS / AMS Designer** (`xrun`), **Spectre AMS** (`spectre`) — chip-level AMS sim
- **Synopsys VCS-AMS / CustomSim** (`vcs`) — AMS co-sim; UPF/power-intent flows
- **Siemens Symphony** — AMS + digital co-sim
- **UPF power-intent flows** (Synopsys/Cadence) — supply-network / isolation / level-shifter intent

---

## Stage: ip_qualification

### Domain Rules
1. Enumerate every block to integrate (analog, RF, digital) and confirm each is **signed off**
   upstream: read `design_state.<domain>.signoff` for the producing domain (e.g.
   `circuit`/`post_layout` for analog blocks, `rf`/`em` for RF, `char` for an abstracted `.lib`,
   `physical_verification`/`pex` for the GDS/extracted view). A block whose `signoff` is not `true`
   is **not qualified** — do not assemble around it.
2. Collect each block's integration views (top netlist/GDS path, abstract/LEF, `.lib`, connect
   modules, pin list, supply pins) and verify pin/port consistency against the intended top
   interface. A missing required view is a `spec_gap` (escalate), not a silent default.
3. Record the qualified block set and any waivers; an unqualified block blocks `top_assembly`.

### QoR Metrics to Evaluate
- 100% of integrated blocks have `signoff: true` in their producing domain (or an explicit waiver)
- Every block exposes the integration views the top needs (netlist/GDS, pins, supplies, connect modules)
- Pin/port lists are consistent with the planned top interface

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Block not signed off upstream | Block integration; route the block back to its domain (do not waive a real gap) |
| Missing integration view (no `.lib`/abstract) | Escalate (`spec_gap`) — request the view from the producing domain |
| Pin/supply mismatch vs top interface | Reconcile the interface; re-confirm against the block's signed-off pin list |

### Output Required
- Qualified-IP list (block → producing domain, signoff status, views, supplies)
- Any waivers with justification

---

## Stage: top_assembly

### Domain Rules
1. Assemble the mixed-signal top: instantiate every qualified block, wire the inter-block nets,
   IO ring, and supply network into a single top netlist (and GDS hierarchy where a physical top
   is built). Read each block's netlist from `design_state.<domain>.netlist`/`gds`.
2. Build the IO/ESD ring: every signal/supply pad gets its pad cell and ESD clamp; flag any pad
   missing a clamp as an incomplete ring (gated at `power_intent_check`).
3. Keep analog islands isolated: route sensitive analog supplies/grounds separately, add guard
   rings/shields per the block's requirements; this is the **power-intent rework loop-back target**.

### QoR Metrics to Evaluate
- All qualified blocks instantiated; inter-block nets fully connected (no dangling top pins)
- IO ring present; every pad has a pad cell + ESD clamp
- Analog islands have isolated supply/ground and shielding

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Dangling top net / unconnected block pin | Complete the top wiring; re-check against the pin list |
| Pad missing ESD clamp | Add the clamp to the IO ring (re-check at `power_intent_check`) |
| Analog island sharing a noisy supply | Split the supply / add isolation (loop-back target for power-intent fail) |

### Output Required
- Assembled mixed-signal top netlist (+ GDS hierarchy where applicable)
- IO/ESD ring map and supply-network plan

---

## Stage: boundary_connect_rules

### Domain Rules
1. Define explicit connect rules (E2L, L2E, bidirectional) for **every** analog↔digital boundary
   at the top; thresholds supply-relative to the crossing domain's `constraints.supply.vdd_v`.
   Reuse the modeling/ams-verification connect modules where they exist
   (`design_state.modeling.connect_modules`, `design_state.ams`).
2. For every supply-domain crossing, require a level-shifter and/or isolation cell per the power
   intent; a crossing without one is a `connectivity` fault.
3. Count any implicit/default connect-module insertion as a `connect_rule_errors` increment — no
   boundary may rely on implicit insertion.

### QoR Metrics to Evaluate
- 100% of analog↔digital boundaries have an explicit connect rule (`connect_rule_errors` = 0)
- Every supply-domain crossing has the required level-shifter/isolation cell
- Connect-rule thresholds parameterised vs the crossing domain's `supply.vdd_v`

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Implicit connect-module insertion | Add an explicit connect rule at the boundary |
| Supply crossing without level-shifter | Insert the level-shifter/isolation cell (`connectivity`) |
| Boundary behaves differently at Vmin | Parameterise thresholds vs the crossing `supply.vdd_v` |

### Output Required
- Top-level connect-rule map (boundary → rule), with level-shifter/isolation coverage

---

## Stage: chip_level_ams_sim

### Domain Rules
1. Run the chip-level AMS co-simulation (cocotb + ngspice/Xyce, or the proprietary AMS engine):
   exercise the top-level functional scenarios across the inter-block boundaries; every checked
   spec maps to a pass/fail assertion/scoreboard, never a waveform eyeball.
2. Synchronise the analog and digital time domains (no time drift) and confirm inter-block
   handshakes behave correctly with the connect rules in place.
3. Root-cause any failure: a top-LVS/connectivity fault → `fix_request` to custom-layout
   (`connectivity`); a block functional/spec miss exposed at the top → `fix_request` to
   circuit-design (`functional`/`spec_violation`); an RNM/connect-module divergence → `fix_request`
   to behavioral-modeling (`functional`). A testbench/connect-rule error loops back locally.

### QoR Metrics to Evaluate
- Chip-level AMS sim runs to completion with no analog/digital time drift (`ams_sim_pass`)
- All top-level functional assertions pass; inter-block handshakes correct
- Failures root-caused to a domain (layout/circuit/model) vs the top testbench

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Analog/digital time drift | Tighten sync step; align analog max-timestep to the digital tick |
| Top-LVS / connectivity fault | Open `fix_request` → custom-layout (`connectivity`) |
| Block functional/spec miss at the top | Open `fix_request` → circuit-design (`functional`/`spec_violation`) |
| RNM/connect-module divergence | Open `fix_request` → behavioral-modeling (`functional`) |

### Output Required
- Chip-level AMS sim report + waveforms
- Root-cause note for any failure (domain + fix_request id)

---

## Stage: power_intent_check

### Domain Rules
1. Check power-intent (UPF/CPF or the open-flow equivalent) consistency: every power domain,
   isolation, level-shifter, and retention intent matches the assembled top; flag inconsistencies.
2. Verify the IO/ESD ring is complete (every pad clamped) and analog-island isolation holds
   (no sensitive supply/ground merged into a noisy domain).
3. A power-intent inconsistency loops back to `top_assembly` for rework (max 2×); a residual
   connectivity fault opens a `fix_request` to custom-layout.

### QoR Metrics to Evaluate
- Power-intent consistent: 0 unmatched isolation/level-shifter/domain crossings (`power_intent_pass`)
- IO/ESD ring complete (`esd_ring_complete`): every pad clamped
- Analog-island isolation holds (`island_isolation_pass`)

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| UPF isolation/level-shifter inconsistency | Loop back → `top_assembly` to insert/fix the cell (×2) |
| Pad missing ESD clamp | Loop back → `top_assembly` to complete the ring |
| Analog island merged into noisy supply | Loop back → `top_assembly` to re-isolate; if physical, `fix_request` → custom-layout |

### Output Required
- Power-intent / connectivity consistency report
- IO/ESD ring and analog-island isolation checklist

---

## Stage: integration_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| Top-level LVS | clean — devices + nets matched (`top_lvs_errors` = 0) |
| Chip-level AMS sim | passes, time-synchronised, all assertions exercised (`ams_sim_pass`) |
| Connect modules | 100% explicit, 0 implicit insertions (`connect_rule_errors` = 0) |
| Power intent | consistent (`power_intent_pass`) |
| IO/ESD ring | complete (`esd_ring_complete`) |
| Analog islands | isolated (`island_isolation_pass`) |

### Domain Rules
1. Confirm every sign-off check above passes with no open `fix_request` against the top.
2. This is a **human-approval checkpoint** (`integration_signoff`) — the natural tape-out-level
   gate for the assembled chip. Do not set `signoff=true` until approved when configured.
3. Record results in `design_state.ams_integration`; close any serviced `fix_request`
   re-validations as PASS.

### Failure Escalation
- Top-LVS / connectivity fault → `fix_request` (`connectivity`) → custom-layout
- Block functional/spec miss → `fix_request` (`functional`/`spec_violation`) → circuit-design
- RNM/connect-module divergence → `fix_request` (`functional`) → behavioral-modeling
- Power-intent inconsistency → `top_assembly` rework (×2) → escalate

### Output Required
- Integration sign-off report (LVS, AMS sim, connect modules, power intent, IO ring, isolation)
- Chip-level AMS waveforms
- `fix_request` entries for any unresolved fault

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`ip_qualification`) — hard-fail if missing:**
- `constraints.supply.vdd_v` — for supply-relative connect-rule thresholds and power-intent checks
- at least one qualified block with a runnable integration view — a signed-off
  `design_state.<domain>` block exposing a netlist/GDS (a bare object with no artifact does not
  qualify, else `spec_gap`)
- `constraints.pdk` — for top-level LVS and the IO/ESD ring

**Optional (schema defaults apply when absent):**
- `constraints.corners` (top-level AMS sweep matrix defaults to the nominal corner when absent)

Skip constraint validation entirely when invoked in re-validation / fix-request-servicing mode
(a `fix_request.id` was passed in the prompt).

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/ams-integration/run_state.md` as the **first action** before launching any tool:
```markdown
run_id:      ams-integration_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/ams-integration/experiences.jsonl`
keyed by `run_id` (do not append a second line for the same run). `key_metrics` fields:
`top_lvs_errors`, `ams_sim_pass`, `connect_rule_errors`. Set `signoff_achieved: false` until
integration_signoff passes; then `true`. Create the file and parent directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each integration fix as an
observation to entity `analog-design-ams-integration-fixes` after writing to `experiences.jsonl`.
Skip silently if absent — the JSONL file is the canonical record.
