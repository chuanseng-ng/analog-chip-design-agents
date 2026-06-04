---
name: circuit-design
description: >
  Analog circuit (schematic) design — topology selection, device sizing via gm/Id,
  biasing, schematic capture, pre-layout ERC, and design review. Use when designing
  an op-amp, comparator, bandgap, LDO, bias generator, or any analog block from a
  block specification through to a sign-off-ready schematic and netlist.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Circuit (Schematic) Design

## Invocation

- **If invoked by a user** presenting a circuit design task: immediately spawn the
  `analog-chip-design-agents:circuit-design-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `circuit-design-orchestrator` mid-flow** (including fix-request
  servicing): do not spawn a new agent. Treat this file as read-only — return the
  requested stage rules, sign-off criteria, or loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive
delegation and must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/circuit/knowledge.md` — known topology pitfalls, successful sizing recipes,
   PDK device quirks. Incorporate its guidance into every stage decision.
2. `memory/circuit/run_state.md` — current run identity (`run_id`, `design_name`, `pdk`,
   `last_stage`) for resume-after-interruption.

## Purpose

Guide analog block design from topology choice through a sign-off-ready, ERC-clean
schematic and SPICE netlist meeting the block's pre-layout electrical specs. Six stages
with explicit QoR gates and loop-back criteria enforced by the circuit-design orchestrator.

---

## Supported EDA Tools

### Open-Source
- **xschem** (`xschem`) — schematic capture and SPICE netlist export; de-facto open analog schematic tool, integrates with sky130/gf180mcu/ihp-sg13g2 PDKs
- **ngspice** (`ngspice`) — in-the-loop DC/AC sweeps during sizing
- **Qucs-S** (`qucs-s`) — schematic + simulation front-end
- **Hdl21 + VLSIR** (`python -m hdl21`) — programmatic (Python) analog schematic generation
- **BAG / BAG3** — generator-based analog design framework
- **gm/Id toolkits** — lookup-table-based sizing (Python; from characterized device data)

### Proprietary (detect-only — never installed)
- **Cadence Virtuoso Schematic Editor** (`virtuoso`) — schematic capture with ADE
- **Synopsys Custom Compiler** (`custom_compiler`) — schematic and design entry
- **Siemens Tanner S-Edit** (`s-edit`) — schematic capture
- **MunEDA WiCkeD** / **Siemens Solido** — automated sizing, optimization, and yield

---

## Stage: topology_selection

### Domain Rules
1. Map each block spec (gain, bandwidth, noise, power, supply) to a candidate topology class (e.g. telescopic, folded-cascode, two-stage Miller, current-mirror OTA).
2. Reject topologies that cannot meet headroom from `design_state.constraints.supply.vdd_v` (count stacked Vds,sat + Vgs against supply).
3. For each viable candidate, record the dominant trade-off (gain vs swing, speed vs power, noise vs area).
4. Prefer the simplest topology that meets all specs with margin — do not over-design.
5. Document why the selected topology meets `design_state.constraints.specs` (or `rf_specs` for RF blocks).

### QoR Metrics to Evaluate
- Headroom feasibility: stacked Vdsat budget ≤ `supply.vdd_v` with ≥ 10% margin
- Predicted gain/bandwidth from hand analysis vs `specs.dc_gain_db` / `specs.gbw_hz`
- Topology count evaluated (target ≥ 2 candidates before selection)

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Insufficient headroom at low VDD | Switch to folded-cascode or current-reuse topology |
| Gain target unreachable single-stage | Add a second (Miller-compensated) stage |
| Noise target hard at low power | Increase input-pair gm (gm/Id), use PMOS input for 1/f |

### Output Required
- Topology decision record (candidates, trade-offs, selection rationale)
- Hand-analysis sizing targets (gm, Id, gm/Id per device)

---

## Stage: device_sizing

### Domain Rules
1. Size with the **gm/Id methodology**: pick gm/Id per device role (input pair high gm/Id ~15–20 for noise/offset; current sources low gm/Id ~5–8 for output swing).
2. Derive W/L from gm/Id lookup tables for the target `pdk`; never guess W/L blindly.
3. Keep all transistors in the intended region (saturation for amplifying devices) with ≥ 50–100 mV Vds margin over Vdsat.
4. Match critical pairs (input differential pair, current mirrors) — equal L, integer-ratio W, same orientation; flag for common-centroid layout.
5. Set channel length above PDK minimum for gain-critical devices (intrinsic gain, matching); minimum L only for speed-critical/switch devices.
6. Iterate sizing against ngspice DC operating-point until the gm/Id and bias targets are met.

### QoR Metrics to Evaluate
- DC gain vs `specs.dc_gain_db`; GBW vs `specs.gbw_hz`
- All devices in saturation (Vds − Vdsat ≥ 50 mV) at the nominal corner
- Input-referred offset / matching consistent with `specs.offset_mv_max`
- Power vs `specs.power_mw`

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Device leaves saturation over corners | Add Vds margin; lower current density (raise W) |
| Gain low | Increase L on gain devices; add cascode |
| Power over budget | Reduce bias current; raise gm/Id on non-critical branches |

### Output Required
- Device sizing table (W, L, multiplicity, gm/Id, Id per device)
- DC operating-point report

---

## Stage: biasing

### Domain Rules
1. Design a PVT-robust bias generator (constant-gm or bandgap-referenced) — do not rely on absolute resistor/threshold values.
2. Mirror reference currents with matched devices; cascode mirrors where output impedance matters.
3. Provide startup circuitry for any self-biased reference; verify it leaves the degenerate (zero-current) state.
4. Budget bias headroom and ensure mirror devices stay saturated across corners.
5. Keep bias-line routing low-impedance and shielded (flag for layout).

### QoR Metrics to Evaluate
- Reference current spread across PVT (target < ±10%)
- Startup verified (no stable zero-current state)
- Bias devices in saturation across corners

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Reference fails to start | Add/repair startup device; verify with tran from 0V |
| Large current spread over PVT | Use constant-gm bias; trim resistor type |

### Output Required
- Bias network schematic + reference-current report
- Startup verification (tran from 0)

---

## Stage: schematic_capture

### Domain Rules
1. Capture the full schematic in xschem (or generator code in Hdl21/BAG) with the selected sizing.
2. Parameterise device sizes and bias currents as symbols for easy sweep/corner runs.
3. Add explicit pin labels, supply/ground, and a documented testbench symbol for reuse.
4. Export a clean SPICE netlist targeting the chosen simulator; include the PDK model/corner include lines.
5. Keep hierarchy clean — one subcircuit per reusable block.

### QoR Metrics to Evaluate
- Netlist exports without unresolved symbols/models
- All device parameters resolve (no defaulted/zero sizes)

### Output Required
- Schematic source (`.sch` / generator script)
- Exported SPICE netlist with PDK includes

---

## Stage: pre_layout_erc

### Domain Rules
1. Run electrical-rule checks: floating gates/nets, shorted supplies, undriven inputs, missing bulk/well ties.
2. Verify every MOS bulk is tied correctly (or to a documented well/bias net).
3. Check for unintended DC paths VDD→VSS and missing series elements.
4. Confirm device terminals are connected (no dangling drain/source).
5. Resolve all ERC errors before review; document any intentional waivers.

### QoR Metrics to Evaluate
- ERC errors = 0 (unwaived)
- Bulk/well connectivity: 100% of devices tied

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Floating bulk | Tie to supply/well-bias net |
| Undriven node | Add bias or remove dangling device |

### Output Required
- ERC report (clean or with documented waivers)

---

## Stage: design_review

### Sign-off Pass Criteria (all must pass at the nominal corner; corners are closed in circuit-simulation)
| Check | Criterion |
|-------|-----------|
| DC gain | ≥ `design_state.constraints.specs.dc_gain_db` |
| Phase margin | ≥ `design_state.constraints.specs.phase_margin_deg` (default: 60) |
| GBW | ≥ `design_state.constraints.specs.gbw_hz` |
| Power | ≤ `design_state.constraints.specs.power_mw` |
| Offset / matching | within `design_state.constraints.specs.offset_mv_max` |
| ERC | 0 unwaived errors |
| All devices | in intended region with margin |

### Domain Rules
1. Review the schematic against the topology decision record and sizing table.
2. Confirm pre-layout AC/transient results meet specs with margin at nominal.
3. Flag layout-sensitive nets (matching pairs, sensitive high-Z nodes, bias lines) for the custom-layout domain.
4. Hand off the netlist + spec table to circuit-simulation for full corner/MC closure.

### Failure Escalation
- Spec miss at nominal → device_sizing
- Topology cannot meet spec → topology_selection
- ERC error → pre_layout_erc

### Output Required
- Pre-layout sign-off record (specs vs targets at nominal)
- Annotated netlist + layout-sensitivity notes for custom-layout
- Spec table for circuit-simulation corner closure

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`topology_selection`) — hard-fail if missing:**
- `constraints.supply.vdd_v` — supply for headroom budgeting
- at least one non-null entry in `constraints.specs` (or `constraints.rf_specs` for RF blocks)
- `constraints.pdk` — for device models / gm-Id tables

**Optional (schema defaults apply when absent):**
- `constraints.specs.phase_margin_deg` (default: 60)
- `constraints.yield.target_sigma` (default: 3)

Skip constraint validation entirely when invoked in fix-request-servicing mode (a
`fix_request.id` was passed in the prompt).

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/circuit/run_state.md` as the **first action** before launching any tool:
```markdown
run_id:      circuit_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/circuit/experiences.jsonl`
keyed by `run_id` (do not append a second line for the same run). `key_metrics` fields:
`dc_gain_db`, `phase_margin_deg`, `gbw_hz`, `power_mw`, `erc_errors`. Set
`signoff_achieved: false` until design_review passes; then `true`. Create the file and
parent directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each applied fix as an
observation to entity `analog-design-circuit-fixes` after writing to `experiences.jsonl`.
Skip silently if absent — the JSONL file is the canonical record.
