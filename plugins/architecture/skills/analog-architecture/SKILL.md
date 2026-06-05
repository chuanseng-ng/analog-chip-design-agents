---
name: analog-architecture
description: >
  Capture top-level analog/mixed-signal specs, budget noise/linearity/power across a signal
  chain, allocate per-block specifications, and assess feasibility before circuit design
  begins. Use when planning a receiver front-end, data-converter front-end, sensor AFE,
  PLL/clock, or PMIC from a system spec down to a per-block specification contract.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Analog Architecture

## Invocation

- **If invoked by a user** presenting an architecture/budgeting task: immediately spawn the
  `analog-chip-design-agents:analog-architecture-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `analog-architecture-orchestrator` mid-flow**: do not spawn a new
  agent. Treat this file as read-only — return the requested stage rules, sign-off criteria,
  or loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation
and must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/architecture/knowledge.md` — known budgeting recipes, cascade pitfalls,
   process/topology trade-offs. Incorporate its guidance into every allocation decision.
2. `memory/architecture/run_state.md` — current run identity (`run_id`, `design_name`,
   `pdk`, `last_stage`) for resume-after-interruption.

## Purpose

Translate a top-level system specification into a closed, feasible per-block specification
contract. Architecture is the **upstream** domain: it budgets noise, linearity, power, and
area across the signal chain and hands circuit-design a per-block spec table. Five stages
with explicit QoR gates and loop-back criteria enforced by the analog-architecture
orchestrator. Architecture is intentionally **technology-light** — it runs from system specs
and does not require a `pdk`.

---

## Supported EDA Tools

### Open-Source
- **Python budgeting** (`python`, NumPy / **scikit-rf**) — cascaded noise/linearity/power math
- **Jupyter** (`jupyter`) — interactive budget exploration and documentation
- **ngspice** (`ngspice`) / **Xyce** (`Xyce`) — behavioral-source sanity checks of allocations

### Proprietary (detect-only — never installed)
- **Cadence ADE Assembler / Spectre** (`spectre`) — system/behavioral verification
- **Keysight SystemVue** — system-level signal-chain modeling
- **MATLAB / Simulink** (`matlab`) — system models and budget analysis

---

## Stage: spec_capture

### Domain Rules
1. Capture the top-level system specs from design intent: full-chain SNR or ENOB, total gain, bandwidth, input signal level, supply (`design_state.constraints.supply.vdd_v`), total power (`constraints.specs.power_mw`), and area (`constraints.area_um2`). Record each as a budget target.
2. Classify the chain type (receiver front-end, data-converter front-end, sensor AFE, PLL/clock, PMIC) — the class fixes which budget (noise vs linearity vs power) dominates.
3. Translate system requirements into budgetable quantities: input-referred noise (nV/√Hz or integrated µVrms over BW), IIP3/THD targets, and per-stage gain. For RF chains use `constraints.rf_specs` (`nf_db`, `iip3_dbm`, `gain_db`).
4. Establish the reference impedance and signal convention (single-ended vs differential, 50 Ω vs high-Z) so noise and linearity math is consistent across blocks.
5. Flag any spec that is null but required for budgeting as a `spec_gap` escalation candidate — do not invent a missing top-level target.

### QoR Metrics to Evaluate
- All required top-level budget targets present and non-null (or `spec_gap` raised)
- Chain type classified; dominant budget identified
- Signal convention and reference impedance recorded

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Missing top-level noise/linearity target | Raise `spec_gap`; request the system spec from the user |
| Ambiguous single-ended vs differential | Fix the convention before budgeting; differential doubles swing, halves even-order distortion |
| ENOB given but no noise/distortion split | Allocate ENOB to a noise floor + distortion budget (e.g. 6.02·N + 1.76 dB SNDR target) |

### Output Required
- System-spec record (targets, chain type, dominant budget)
- Signal convention + reference-impedance note

---

## Stage: signal_chain_budgeting

### Domain Rules
1. Compute the cascaded noise budget with the Friis equation: `F = F1 + (F2−1)/G1 + (F3−1)/(G1·G2) + …` (linear power gains); allocate so early stages carry low NF / high gain. Convert to input-referred noise density and integrate over BW.
2. Compute the cascaded linearity budget: `1/IIP3_tot = 1/IIP3_1 + G1/IIP3_2 + (G1·G2)/IIP3_3 + …` (linear power units); later stages dominate distortion as gain accumulates, so back-load gain only as far as the noise budget allows.
3. Allocate the power budget per block as a fraction of `constraints.specs.power_mw`, weighting blocks by their noise/linearity demand (low-noise input stages and output drivers get more); keep ≥ 10% reserve.
4. Estimate per-block area as a fraction of `constraints.area_um2` from device-count / passive-area heuristics; keep ≥ 15% reserve for routing and matching dummies.
5. Verify the budget closes: summed allocations meet the top spec with margin. If noise + linearity + power cannot simultaneously close, mark the chain infeasible and trigger the spec_capture renegotiation loop.

### QoR Metrics to Evaluate
- Cascaded input-referred noise ≤ target (`specs.input_noise_nv_rthz` × √BW, or `rf_specs.nf_db`) with ≥ 1 dB margin
- Cascaded IIP3 ≥ `specs.iip3_dbm` (or `rf_specs.iip3_dbm`); cascaded THD ≤ `specs.thd_db`
- Σ per-block power ≤ `specs.power_mw` with ≥ 10% reserve
- Σ per-block area ≤ `area_um2` with ≥ 15% reserve

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Cascaded NF exceeds target | Raise front-stage gain / lower front-stage NF; move gain earlier in the chain |
| Cascaded IIP3 below target | Reduce back-stage gain or add back-stage linearity (degeneration); back-load gain less |
| Power budget overruns | Trade gain for current on noise-non-critical stages; share bias |
| Budget cannot close (noise vs power conflict) | Renegotiate top spec (spec_capture loop) or change chain architecture |

### Output Required
- Cascaded budget worksheet (noise, IIP3, power, area per stage)
- Budget-closure summary with per-spec margin

---

## Stage: topology_partitioning

### Domain Rules
1. Partition the chain into implementable blocks (LNA, mixer, VGA, filter, ADC driver, bias/reference, etc.) and assign each its allocated noise/linearity/gain/power/area sub-budget.
2. For each block, name a candidate circuit-topology class feasible at `constraints.supply.vdd_v` — headroom check: stacked Vdsat + Vgs ≤ vdd with ≥ 10% margin — so circuit-design inherits a viable starting point.
3. Choose partition boundaries that minimise inter-block matching/interface sensitivity (do not split a matched differential path across blocks).
4. Produce the **per-block specification table** — the contract handed to circuit-design — keyed to `constraints.specs` / `rf_specs` field names so downstream QoR gates compare like-for-like.

### QoR Metrics to Evaluate
- Every block has a non-null allocated spec set
- Every block has a supply-feasible candidate topology class
- Partition boundaries do not bisect matched paths

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| No topology meets headroom at low VDD | Re-allocate gain; choose folded/current-reuse class; flag for circuit-design |
| Matched pair split across blocks | Move the boundary so the pair stays in one block |
| Block sub-budget infeasible alone | Merge with a neighbour or re-allocate from reserve |

### Output Required
- Block partition diagram / list
- Per-block specification table (keyed to `specs` / `rf_specs`)

---

## Stage: behavioral_feasibility

### Domain Rules
1. Sanity-check each block's allocated spec with a first-order behavioral model (Python/NumPy, or an ngspice/Xyce behavioral source) — e.g. an ideal-gain + noise-source model to confirm the noise allocation is physically reachable at the allotted power.
2. Cross-check the cascaded budget end-to-end with a chain-level behavioral sim; confirm integrated output noise / distortion meets the top spec with the allocated per-block numbers.
3. Flag blocks whose allocation requires unrealistic FoM (e.g. NF below the kT floor at the allotted current) and loop back to topology_partitioning to re-allocate.
4. Record feasibility risk (low/medium/high) per block for the sign-off record and for circuit-design prioritisation.

### QoR Metrics to Evaluate
- Chain-level behavioral sim meets top spec with the allocated numbers
- No block requires sub-kT-floor noise or unphysical FoM
- Per-block feasibility risk recorded

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Block needs NF below kT floor at allotted current | Raise the block's power/area allocation, or relax the top spec |
| Chain sim misses top spec despite closed paper budget | Re-check cascade gains; account for impedance mismatch loss |
| Feasibility high-risk on the dominant block | Prioritise it for early circuit-design; widen its reserve |

### Output Required
- Per-block behavioral feasibility results
- Chain-level behavioral verification + per-block risk rating

---

## Stage: architecture_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| Noise budget | cascaded input-referred noise ≤ target (`specs.input_noise_nv_rthz` / `rf_specs.nf_db`) with margin |
| Linearity budget | cascaded IIP3 ≥ `specs.iip3_dbm` (or `rf_specs.iip3_dbm`); THD ≤ `specs.thd_db` |
| Power budget | Σ block power ≤ `specs.power_mw` |
| Area budget | Σ block area ≤ `area_um2` |
| Per-block specs | every block has a feasible, allocated spec set |
| Feasibility | no block flagged infeasible by behavioral_feasibility |

### Domain Rules
1. Review the per-block spec table against the cascaded budget and the behavioral feasibility results.
2. Confirm every budget (noise, linearity, power, area) closes with margin and no block is infeasible.
3. Hand the per-block specification table to circuit-design as its `constraints.specs` source per block; downstream circuit-design reads `architecture.blocks[].specs`.

### Failure Escalation
- Budget cannot close → spec_capture (renegotiate top spec) → escalate
- Block infeasible at allocation → topology_partitioning (re-allocate)
- Missing top-level spec → escalate (`failure_class: spec_gap`)

### Output Required
- Signed architecture record (budgets vs targets, per-block specs)
- Per-block specification contract for circuit-design
- Feasibility / risk assessment

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`spec_capture`) — hard-fail if missing:**
- `constraints.supply.vdd_v` — for per-block headroom feasibility
- at least one top-level budget target among `constraints.specs.power_mw`, `input_noise_nv_rthz`, `iip3_dbm` (or the `rf_specs` equivalents), or `constraints.area_um2`

**Optional (no default required):**
- `constraints.pdk` — architecture is technology-light; absence is not a failure
- `constraints.area_um2` — area budgeting is skipped (with a note) when absent

Architecture does not run in fix-request-servicing mode — it is upstream of the circuit
repair loop and neither opens nor services `fix_request`s in this phase.

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/architecture/run_state.md` as the **first action** before launching any tool:
```markdown
run_id:      architecture_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/architecture/experiences.jsonl`
keyed by `run_id` (do not append a second line for the same run). `key_metrics` fields:
`noise_budget_nv`, `power_budget_mw`, `area_estimate_um2`. Set `signoff_achieved: false`
until architecture_signoff passes; then `true`. Create the file and parent directories if
they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each budgeting decision as an
observation to entity `analog-design-architecture-fixes` after writing to `experiences.jsonl`.
Skip silently if absent — the JSONL file is the canonical record.
