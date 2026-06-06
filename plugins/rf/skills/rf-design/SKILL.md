---
name: rf-design
description: >
  Design and verify an RF/mmWave block (LNA, mixer, VCO, PLL, PA): topology selection and
  matching, S-parameter, harmonic-balance, Pnoise/PAC, IP3, and load-pull analyses, signed off
  against the RF spec table across corners. Use when designing or re-running an RF block. Loop-backs
  are stage-local first (spec/stability → topology_matching, convergence → harmonic_balance); when a
  cap is exhausted RF opens a cross-domain fix_request (circuit-design for device rework, em-modeling
  for a passive shortfall) and reads the EM-modeling passive model as a data dependency.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: RF / mmWave Design

## Invocation

- **If invoked by a user** presenting an RF design task: immediately spawn the
  `analog-chip-design-agents:rf-design-orchestrator` agent and pass the full user request and any
  available context. Do not execute stages directly.
- **If invoked by the `rf-design-orchestrator` mid-flow** (including re-validation after a serviced
  fix_request): do not spawn a new agent. Treat this file as read-only — return the requested stage
  rules, sign-off criteria, or loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation and
must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/rf/knowledge.md` — known matching/stability fixes, HB convergence recipes, phase-noise
   and load-pull patterns, and PDK/tool quirks. Incorporate its guidance into every stage.
2. `memory/rf/run_state.md` — current run identity for resume-after-interruption.

## Purpose

Design and verify an RF/mmWave block — select and match the topology, extract S-parameters, run
harmonic-balance / Pnoise / IP3 / load-pull, and sign off against the RF spec table across the
required corners. Seven stages with explicit QoR gates. RF design is a **cross-domain producer** —
its loop-backs are stage-local first (spec/stability fail → `topology_matching`; non-convergence →
`harmonic_balance` settings); when a stage-local cap is exhausted and the block still misses spec it
**opens** a cross-domain `fix_request`. It **reads** the EM-modeling passive model (Touchstone +
fitted lumped model) from `design_state.em` as a data dependency; a limiter traced to a passive
opens a `fix_request` with `route_to: em-modeling` (an automated EM re-solve), while a device-level
spec miss opens one with `route_to: circuit-design`. The pipeline-orchestrator re-validates the fix
via this orchestrator.

---

## Supported EDA Tools

### Open-Source
- **Qucs-S** (`qucs-s`) — schematic + harmonic-balance front-end (RF capable)
- **Xyce** (`xyce`) — parallel SPICE with harmonic balance
- **ngspice** (`ngspice`) — small-signal / transient (limited native RF)
- **scikit-rf** (Python `skrf`) — S-parameter math, stability (K/Δ), de-embedding
- **openEMS** (`openEMS`) — passive co-reference / S-param cross-check

### Proprietary (detect-only — never installed)
- **Cadence Spectre RF** (`spectre`) — S-param/HB/Pnoise/PAC/load-pull
- **Keysight ADS / GoldenGate** (`ads`)
- **Cadence AWR Microwave Office** (`awr`)
- **Synopsys HSPICE-RF** (`hspice`)
- **AFS-RF** (Analog FastSPICE RF)

---

## Stage: rf_spec

### Domain Rules
1. Read the RF block intent (block class LNA/mixer/VCO/PLL/PA, frequency band, source/load
   impedance, supply) and the target spec table from `constraints.rf_specs` (preferred) or
   `constraints.specs`; record which specs are in scope for the block class (PA → `pae_pct` /
   `p1db_dbm` / `evm_pct`; VCO/PLL → `phase_noise_dbc_hz`; LNA/mixer → `nf_db` / `gain_db` /
   `s11_db_max` / `iip3_dbm`).
2. Bind the passive data dependency: if the block uses on-chip inductors/transformers/lines, read
   `design_state.em.touchstone` + `design_state.em.fitted_model`; if absent, treat the passive as
   ideal/approximate and flag the assumption for later escalation.
3. Build the corner set from `constraints.corners` (process × `voltage_pct` × `temp_c`) and the
   analysis frequency grid covering the band plus the harmonics of interest.

### QoR Metrics to Evaluate
- All block-relevant `rf_specs` present and bounded
- Passive model bound from `design_state.em`, or explicitly flagged as ideal
- Corner / frequency grid covers the band + the harmonics needed downstream

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| No `rf_specs` for the block class | escalate constraint_gap — require the governing RF spec(s) before proceeding |
| EM passive model missing for an on-chip inductor | read `design_state.em`; if absent, flag the ideal-passive assumption and WARN (may drive a later escalation) |

### Output Required
- RF spec table (block class, in-scope specs + targets, band, source/load Z, passive-model
  binding, corner/frequency grid)

---

## Stage: topology_matching

### Domain Rules
1. Select/confirm the topology for the block class and synthesize input/output (and inter-stage)
   matching networks toward the target source/load impedance, using the bound EM passive models
   where on-chip passives are used (read Q/SRF from `design_state.em`).
2. Verify the matching network trends `s11`/`s22` toward `rf_specs.s11_db_max` in-band and does
   not push any passive past its self-resonant frequency.
3. This is the **loop-back target**: on a downstream spec/stability fail, re-enter here to re-match
   or re-top (max 2×).

### QoR Metrics to Evaluate
- In-band input/output match trending to `s11_db_max`
- Matching components within passive Q/SRF limits
- Topology supports every in-scope spec

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Match operating above a passive's SRF | re-select / re-match below SRF; if no on-chip option exists, open fix_request → em-modeling for a re-solve |
| Cannot hit `s11_db_max` with the chosen topology | re-top (loop-back target) — add a matching section or change topology class |

### Output Required
- Topology choice + matching-network netlist with component values and the referenced passive models

---

## Stage: sparameter_analysis

### Domain Rules
1. Run small-signal S-parameter analysis across the band/corners; extract `s11`/`s22` (return
   loss), `s21` (gain), and compute the Rollett stability factor `K` (and `B1`/`Δ`) from the
   S-matrix with scikit-rf.
2. Read S-params from the tool summary / Touchstone file, never raw frequency dumps; flag any
   non-passive S-matrix as a tool/setup error.
3. Where on-chip passives are used, confirm the S-params reflect the EM-fitted model (not an ideal
   substitute).

### QoR Metrics to Evaluate
- `s11_db`/`s22` ≤ `rf_specs.s11_db_max` in-band
- `gain_db` (S21) ≥ target
- `k_factor` ≥ 1 in-band where unconditional stability is required

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| `K < 1` (potentially unstable) in-band | loop back → topology_matching: add stabilization / re-match |
| Return loss misses `s11_db_max` | loop back → topology_matching: re-tune the matching network |

### Output Required
- S-parameter / Touchstone results + stability table (`s11_db`, `s22`, `gain_db`/S21, `k_factor`
  per corner)

---

## Stage: harmonic_balance

### Domain Rules
1. Run harmonic-balance (Qucs-S / Xyce HB; Spectre RF if detected) for large-signal behaviour —
   gain compression, conversion gain (mixer), oscillation/tuning (VCO); set tone count/order and
   oversampling adequate for the spectral content.
2. On non-convergence, this is the **convergence loop target**: re-run with adjusted HB settings
   (more harmonics, source stepping, continuation) — max 2×.
3. Read the HB summary (`p1db_dbm`, compression, harmonic levels) from the tool summary file, not
   the raw spectrum.

### QoR Metrics to Evaluate
- HB converged at all required corners / drive levels
- `p1db_dbm` extracted
- Harmonic / spur levels within budget

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| HB fails to converge at high drive | retry with more harmonics / source-stepping / continuation (max 2×) |
| Excess harmonic / spur content | revisit bias/topology — loop back → topology_matching if structural |

### Output Required
- HB report (`p1db_dbm`, compression curve, harmonic/spur levels per corner)

---

## Stage: noise_linearity

### Domain Rules
1. Run Pnoise/PAC (and HB-based two-tone) to extract `nf_db` (LNA/mixer), `iip3_dbm`/IIP2, and
   `phase_noise_dbc_hz` at the spec offset(s) (VCO/PLL); compute from the tool's noise/spectrum
   summary.
2. Compare each extracted metric to its `rf_specs` target; a spec miss is the second **loop-back
   trigger** to `topology_matching` (max 2×).
3. If the noise/linearity limiter traces to an on-chip passive's loss/Q (from `design_state.em`),
   do not loop locally — open a fix_request → em-modeling for an automated re-solve.

### QoR Metrics to Evaluate
- `nf_db` ≤ target
- `iip3_dbm` ≥ target
- `phase_noise_dbc_hz` ≤ target at the spec offset

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| `nf_db` over target, limiter = inductor Q | open fix_request → em-modeling (higher-Q passive) — no local fix |
| `iip3_dbm` / phase-noise miss from the circuit | loop back → topology_matching: re-bias / re-top (max 2×) |

### Output Required
- Noise + linearity report (`nf_db`, `iip3_dbm`, `phase_noise_dbc_hz` per corner) with limiter
  attribution

---

## Stage: loadpull_optimization

### Domain Rules
1. For PA/driver blocks, run load-pull (HB-swept load impedance) to find the load for target
   `pae_pct` / `p1db_dbm` / Pout, and (where in spec) evaluate `evm_pct` under modulated drive;
   for non-PA blocks, confirm the optimum source/load and compute `evm_pct` if specified, else
   pass through.
2. Confirm the load-pull optimum is realizable with the available (EM-modeled) output match; if it
   demands a passive beyond Q/SRF, open a fix_request → em-modeling for a re-solve.
3. A `pae_pct`/`evm_pct` miss loops back to `topology_matching` (max 2×).

### QoR Metrics to Evaluate
- `pae_pct` ≥ target and `p1db_dbm`/Pout ≥ target at the chosen load
- `evm_pct` ≤ target where specified

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Optimum load needs a passive beyond Q/SRF | open fix_request → em-modeling to re-solve the output passive |
| `pae_pct`/`evm_pct` miss with a realizable load | loop back → topology_matching: re-size the output stage / re-match (max 2×) |

### Output Required
- Load-pull contours + chosen load; `pae_pct` / `p1db_dbm` / Pout / `evm_pct` table per corner

---

## Stage: rf_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| Spec compliance | every in-scope `rf_specs` (nf/gain/s11/iip3/p1db/phase-noise/pae/evm) meets target across the required corners |
| Stability | `k_factor` ≥ 1 in-band where unconditional stability is required |
| Convergence | all S-param/HB/Pnoise analyses converged at every corner |
| Passive validity | on-chip passives used the EM-fitted model (no ideal substitute at sign-off) |

### Domain Rules
1. Confirm spec compliance, stability, convergence, and passive validity all pass.
2. Mark the block signed off and publish the RF spec-compliance table + Touchstone/HB/Pnoise
   reports.
3. Close any serviced re-validation (after a circuit-design rework or em-modeling re-solve) as PASS.

### Failure Handling
- Spec/stability fail after the stage-local retry cap → open a cross-domain `fix_request`
  (`route_to: circuit-design` for a device-level miss, or `route_to: em-modeling` when the limiter
  is an on-chip passive); terminate with `decision: escalate` so the pipeline-orchestrator dispatches
  the servicer and re-validates via this orchestrator.
- Escalate to the user only for a genuine `spec_gap` (ambiguous/missing spec) or when the
  cross-domain iteration cap is hit.

### Output Required
- RF sign-off report (spec compliance, stability, convergence, passive validity)
- Published S-parameter / HB / Pnoise artifacts

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`rf_spec`) — hard-fail if missing:**
- `constraints.supply.vdd_v` — bias / headroom
- at least one non-null entry in `constraints.rf_specs` (or `constraints.specs` for a baseband
  block) — the spec(s) to close
- `constraints.pdk` — device models / passive layer stack

`constraints.corners.process` falls back to `["tt"]` with a WARN if absent. Skip constraint
validation entirely when invoked in re-run / fix-servicing mode (a `fix_request.id` or a serviced
em re-solve reference was passed in the prompt).

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/rf/run_state.md` as the **first action**:
```markdown
run_id:      rf_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/rf/experiences.jsonl` keyed by
`run_id`. `key_metrics` fields: `nf_db`, `gain_db`, `iip3_dbm`, `phase_noise_dbc_hz`. Set
`signoff_achieved: false` until rf_signoff passes; then `true`. Create the file and parent
directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each matching/stability/HB fix as
an observation to entity `analog-design-rf-fixes` after writing to `experiences.jsonl`. Skip
silently if absent — the JSONL file is the canonical record.
