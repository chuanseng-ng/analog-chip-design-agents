---
name: circuit-simulation
description: >
  Analog circuit simulation — testbench setup, DC operating point, AC, transient, noise,
  stability, PVT corners, and Monte-Carlo yield analysis, ending in electrical-spec
  sign-off. Use when verifying an analog block's specs across corners, debugging
  convergence, or closing Monte-Carlo yield on a SPICE netlist.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Circuit Simulation

## Invocation

- **If invoked by a user** presenting a simulation/spec-closure task: immediately spawn the
  `analog-chip-design-agents:circuit-simulation-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `circuit-simulation-orchestrator` mid-flow**: do not spawn a new
  agent. Treat this file as read-only — return the requested stage rules, sign-off criteria,
  or loop-back guidance.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/sim/knowledge.md` — known convergence fixes, successful solver options, corner
   pitfalls, PDK model quirks.
2. `memory/sim/run_state.md` — current run identity for resume-after-interruption.

## Purpose

Verify an analog block's electrical specifications across the full PVT + mismatch space and
close Monte-Carlo yield. Eight stages with explicit QoR gates. On a spec violation that the
testbench cannot resolve, this domain opens a `fix_request` routed to circuit-design by the
pipeline-orchestrator.

---

## Supported EDA Tools

### Open-Source
- **ngspice** (`ngspice`) — DC/AC/tran/noise; `.measure`, `.dc`, `.ac`, `.noise`, `.tran`
- **Xyce** (`Xyce`) — parallel SPICE for large netlists and big Monte-Carlo sweeps
- **gnucap** (`gnucap`) — general circuit analysis
- **Qucs-S** (`qucs-s`) — simulation front-end driving ngspice/Xyce
- **PySpice** (`python -m PySpice`) — scripted corner/Monte-Carlo orchestration and post-processing

### Proprietary (detect-only — never installed)
- **Cadence Spectre / Spectre X / APS** (`spectre`) — industry analog simulator
- **Synopsys HSPICE** (`hspice`) / **PrimeSim** (`primesim`) / **FineSim** (`finesim`)
- **Siemens AFS (Analog FastSPICE)** (`afs`) / **Eldo** (`eldo`)
- **Silvaco SmartSpice** / **Empyrean ALPS / NanoSpice**

---

## Stage: testbench_setup

### Domain Rules
1. Build a reusable testbench: stimulus sources, loads, supply, and `.param`-driven corner/temperature hooks.
2. Include the PDK model library with corner-selectable `.lib` statements (tt/ss/ff/sf/fs).
3. Define `.measure` statements for every spec (gain, GBW, PM, noise, offset, settling, power) — never read specs by eye.
4. Use realistic load and source impedance from the block spec; document assumptions.
5. Keep one testbench per analysis where solver settings differ (e.g. tran vs noise).

### QoR Metrics to Evaluate
- All specs covered by a `.measure` (no manual reads)
- Testbench netlists cleanly (no missing models/params)

### Output Required
- Testbench netlist(s) with parameterised corner hooks
- `.measure` block covering every spec

---

## Stage: dc_op

### Domain Rules
1. Solve the DC operating point; confirm every device is in its intended region.
2. Check node voltages against expected bias; flag devices within 50 mV of triode.
3. Verify bias-current mirrors match expected ratios.
4. On non-convergence: apply `.nodeset`/`.ic`, raise `gmin`/`gmin steps`, enable source stepping before declaring failure.

### QoR Metrics to Evaluate
- All amplifying devices in saturation (Vds − Vdsat ≥ 50 mV)
- Bias currents within ±5% of target
- Convergence achieved

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| DC non-convergence | `.nodeset` key nodes; `gmin stepping`; `source stepping` |
| Device in triode | Feed back to circuit-design (re-bias) |

### Output Required
- DC operating-point report (per-device region, Id, Vds, Vgs)

---

## Stage: ac_analysis

### Domain Rules
1. Run `.ac` over a decade range spanning DC to ≥ 10× expected GBW.
2. Measure DC gain, GBW (unity-gain frequency), phase margin, and gain margin.
3. For feedback blocks, break the loop correctly (e.g. Middlebrook / replica) to get true loop gain.
4. Check PSRR/CMRR with the appropriate small-signal injection.

### QoR Metrics to Evaluate
- DC gain ≥ `design_state.constraints.specs.dc_gain_db`
- GBW ≥ `design_state.constraints.specs.gbw_hz`
- Phase margin ≥ `design_state.constraints.specs.phase_margin_deg` (default: 60)
- PSRR/CMRR ≥ `specs.psrr_db` / `specs.cmrr_db` (when specified)

### Output Required
- AC report (gain, GBW, PM, GM, PSRR, CMRR)

---

## Stage: transient

### Domain Rules
1. Run large- and small-signal transient: slew, settling, overshoot, step response.
2. Measure settling time to the spec's error band; measure slew rate on both edges.
3. Use tight `reltol`/`abstol` for settling measurements; verify timestep does not alias.
4. Check startup/power-on behaviour for biased blocks.

### QoR Metrics to Evaluate
- Settling time ≤ `design_state.constraints.specs.settling_ns` (when specified)
- Slew rate meets spec; overshoot within bound
- No unexpected oscillation/ringing

### Output Required
- Transient report (slew, settling, overshoot)

---

## Stage: noise_analysis

### Domain Rules
1. Run `.noise` to get input-referred noise density and integrated noise over the band of interest.
2. Identify dominant noise contributors (device + flicker vs thermal); report top contributors.
3. For sampled systems, fold noise correctly (kT/C, aliasing) — document the bandwidth used.

### QoR Metrics to Evaluate
- Input-referred noise ≤ `design_state.constraints.specs.input_noise_nv_rthz` (when specified)
- Integrated noise / SNR meets the block spec

### Output Required
- Noise report (density, integrated, top contributors)

---

## Stage: corner_analysis

### Domain Rules
1. Sweep all process corners in `design_state.constraints.corners.process` × temperature (`corners.temp_c`) × supply (`corners.voltage_pct`).
2. Re-run AC/tran/noise `.measure` at every corner; collect the worst case per spec.
3. Flag the limiting corner for each spec (e.g. PM worst at SS/125C/Vmin).
4. A spec failing at any corner that the testbench cannot fix is a **`spec_violation`** → open a `fix_request`.

### QoR Metrics to Evaluate
- Every spec passes at **all** corners (worst-case margin ≥ 0)
- Limiting corner identified per spec

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| PM fails at slow/hot corner | fix_request → circuit-design (re-compensate) |
| Gain low at fast/cold | fix_request → circuit-design (re-bias / cascode) |

### Output Required
- Corner matrix (spec × corner, worst-case highlighted)

---

## Stage: monte_carlo

### Domain Rules
1. Run Monte-Carlo (process + mismatch) for `design_state.constraints.yield.mc_samples` samples.
2. Compute mean, sigma, and Cpk for offset, gain, PM, and other sensitive specs.
3. Estimate yield sigma vs `design_state.constraints.yield.target_sigma`; report the limiting spec.
4. A yield miss the testbench cannot resolve is a **`yield`** failure → open a `fix_request`.

### QoR Metrics to Evaluate
- Yield sigma ≥ `design_state.constraints.yield.target_sigma` (default: 3)
- Offset/mismatch within `specs.offset_mv_max`

### Output Required
- Monte-Carlo report (histograms, mean/sigma/Cpk, estimated yield)

---

## Stage: sim_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| All AC specs | pass at all corners |
| All transient specs | pass at all corners |
| Noise | within spec |
| Monte-Carlo yield | ≥ `design_state.constraints.yield.target_sigma` |
| Convergence | clean across all runs |

### Failure Escalation
- Spec miss across corners → open `fix_request` (`failure_class: spec_violation`) → circuit-design
- Yield miss → open `fix_request` (`failure_class: yield`) → circuit-design
- Persistent non-convergence → `failure_class: convergence`, retry with clean testbench/options; if still failing, escalate

### Output Required
- Sign-off report (all analyses, all corners, MC yield)
- Spec-compliance table (target vs worst-case)
- `fix_request` entries for any unresolved violations

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`testbench_setup`) — hard-fail if missing:**
- `constraints.supply.vdd_v`
- at least one non-null entry in `constraints.specs` (or `constraints.rf_specs`)
- `constraints.corners.process` (≥ 1 entry)

**Optional (schema defaults apply when absent):**
- `constraints.specs.phase_margin_deg` (default: 60)
- `constraints.corners.temp_c` (default: `[27]`), `constraints.corners.voltage_pct` (default: `[0]`)
- `constraints.yield.target_sigma` (default: 3), `constraints.yield.mc_samples` (default: 1000)

Skip constraint validation entirely when invoked in fix-request-servicing/re-validation mode.

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/sim/run_state.md` first:
```markdown
run_id:      sim_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```

### Write on stage completion
Upsert one JSON record in `memory/sim/experiences.jsonl` keyed by `run_id`. `key_metrics`
fields: `worst_pm_deg`, `worst_gain_db`, `mc_yield_sigma`, `failing_corners`,
`convergence_failures`. Set `signoff_achieved: false` until sim_signoff passes. Create the
file and parent directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each convergence/spec fix as
an observation to entity `analog-design-sim-fixes`. Skip silently if absent.
