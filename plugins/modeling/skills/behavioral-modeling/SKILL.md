---
name: behavioral-modeling
description: >
  Author, compile, and validate analog behavioral models — Verilog-A, Verilog-AMS, VHDL-AMS,
  and SystemVerilog real-number models — plus the connect modules that bridge analog and
  digital domains. This is the analog-HDL core of the marketplace. Use when building a fast,
  accurate model of an analog block for AMS verification or system simulation.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Behavioral / AMS Modeling

## Invocation

- **If invoked by a user** presenting a modeling task: immediately spawn the
  `analog-chip-design-agents:behavioral-modeling-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `behavioral-modeling-orchestrator` mid-flow** (including fix-request
  servicing): do not spawn a new agent. Treat this file as read-only — return the requested
  stage rules, sign-off criteria, or loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation
and must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/modeling/knowledge.md` — known Verilog-A idioms, OpenVAF/ADMS quirks, convergence
   recipes, RNM pitfalls. Incorporate its guidance into every authoring decision.
2. `memory/modeling/run_state.md` — current run identity (`run_id`, `design_name`, `pdk`,
   `last_stage`) for resume-after-interruption.

## Purpose

Author, compile, and validate analog behavioral models and the connect modules that bridge
analog and digital domains — the "analog HDL" capability. Six stages with explicit QoR gates
and loop-back criteria enforced by the behavioral-modeling orchestrator. A model is only
signed off when it is both **accurate** (vs a SPICE reference) and **faster** than SPICE.

---

## Supported EDA Tools

### Open-Source
- **OpenVAF** (`openvaf`) — Verilog-A → OSDI compiler for ngspice / Xyce; the primary path
- **ADMS** (`admsXml`) — legacy Verilog-A → C model generation
- **ngspice** (`ngspice`) / **Xyce** (`Xyce`) — OSDI loading + model-vs-SPICE co-sim
- **SystemVerilog RNM** (`nettype`/`wreal`) via **Verilator** (`verilator`) / **Icarus** (`iverilog`)
- **Hdl21 + VLSIR** (`python -m hdl21`) — programmatic (Python) analog HDL
- **GHDL-AMS** (`ghdl`) — limited VHDL-AMS support

### Proprietary (detect-only — never installed)
- **Cadence AMS Designer / Xcelium AMS** (`xrun`) — Verilog-AMS / Verilog-A reference
- **Spectre Verilog-A** (`spectre`) — Verilog-A in Spectre
- **Synopsys VCS-AMS / CustomSim** (`vcs`) — AMS co-sim
- **Siemens Symphony / Symphony Pro** — AMS simulation

---

## Stage: model_planning

### Domain Rules
1. Choose the modeling language per use: **Verilog-A** (→ OSDI via OpenVAF for ngspice/Xyce) for continuous analog behaviour with conservation laws; **SystemVerilog RNM** (`nettype`/`wreal`) for fast event-driven signal-flow; **VHDL-AMS** (GHDL-AMS, limited) only when mandated.
2. Define the model's port natures (electrical vs real/wreal vs logic) and the abstraction level (functional / behavioural-with-parasitics) up front.
3. Record the target model-vs-SPICE error tolerance and the parameters that map to `design_state.constraints.specs` (gain, BW, noise, offset) so the model is spec-traceable.
4. Identify the conserved quantities and independent sources the model must expose, and which analog↔digital boundaries (if any) will need connect modules.

### QoR Metrics to Evaluate
- Language choice justified for the use case
- Spec-bearing outputs identified and traced to `constraints.specs`/`rf_specs`
- Error tolerance and abstraction level fixed before authoring

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| RNM chosen for a conservation-law block | Switch to Verilog-A (RNM cannot carry KCL/KVL) |
| No SPICE reference identified | Pick the circuit-design netlist (`design_state.circuit.netlist`) or a reference cell |
| Tolerance left implicit | Fix the error tolerance from the modelled spec before authoring |

### Output Required
- Model plan (language, port natures, abstraction, error tolerance)
- Spec-traceability map (model output → constraint key)

---

## Stage: va_authoring

### Domain Rules
1. Write Verilog-A per the LRM: declare `electrical` disciplines, use `branch`/contribution operators (`<+`), and gate parameter computation with `@(initial_step)` — never recompute constants every evaluation.
2. Ensure continuity and differentiability of all branch contributions; use `$limexp`, `tanh`-smoothed clamps, and `ddx`-friendly forms to keep the Jacobian well-conditioned (avoid hard `if` discontinuities on solution variables).
3. Bound parameters with `from [...]` ranges and provide physical defaults; emit `$strobe`/`$error` only outside the inner solve loop to avoid convergence noise.
4. Model noise explicitly where the block's noise spec matters (`white_noise`, `flicker_noise`) so model-vs-SPICE noise comparison is meaningful.
5. For RNM, drive `wreal`/`nettype` resolution functions and quantize/threshold at digital boundaries; never let `wreal` `'z`/`'x` propagate into arithmetic.

### QoR Metrics to Evaluate
- All branch contributions continuous/differentiable (no hard discontinuity on solve vars)
- Parameters bounded with physical defaults
- Noise modelled where a noise spec applies

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Hard `if` on a solution variable | Replace with `$limexp`/`tanh`-smoothed transition |
| Constants recomputed every step | Hoist to `@(initial_step)` |
| RNM `x`/`z` propagating into math | Add resolution/threshold at the boundary; default `wreal` to a finite value |

### Output Required
- Verilog-A / Verilog-AMS or SystemVerilog-RNM source

---

## Stage: model_compilation

### Domain Rules
1. Compile Verilog-A to OSDI with OpenVAF; treat all OpenVAF warnings (unused params, implicit conversions, non-differentiable constructs) as actionable, not noise.
2. Load the OSDI into ngspice/Xyce and confirm the module instantiates and runs a trivial DC/tran without error before validation.
3. On compile failure, read the OpenVAF diagnostic, fix the offending construct in va_authoring, and recompile (loop, cap 3×). Classify a hard tool crash as `tool_error`; a convergence-shaping construct failure as `convergence`.
4. Record the exact OpenVAF/compiler version and keep generated OSDI artifacts for reproducibility.

### QoR Metrics to Evaluate
- OSDI compiles with 0 errors; warnings triaged
- Module instantiates and runs a trivial DC/tran in ngspice/Xyce

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| OpenVAF compile error (unsupported construct) | Replace with an OSDI-supported form; remove non-differentiable `if` on solve vars |
| OSDI loads but won't instantiate | Check discipline/nature mismatch and port order vs the netlist |
| Non-convergence when OSDI loaded | Smooth discontinuities (`$limexp`/`tanh`); add small conductance to floating nodes |

### Output Required
- Compiled OSDI artifact (+ compiler version)
- Compile/load log (clean)

---

## Stage: connect_rule_setup

### Domain Rules
1. Define connect modules / connect rules (E2L, L2E, E2R, R2E bidirectional) for every analog↔digital boundary the model touches; specify supply-relative thresholds (VIH/VIL referenced to `constraints.supply.vdd_v`) and drive strength / impedance.
2. Ensure connect-module coverage is complete: every crossing net has an explicit rule and no implicit/default insertion is relied upon (flag implicit insertions).
3. Parameterise thresholds and rise/fall so the same connect modules work across the corner supply range.

### QoR Metrics to Evaluate
- 100% of analog↔digital crossings have an explicit connect rule
- Thresholds parameterised vs `supply.vdd_v` (corner-robust)
- No reliance on implicit insertion

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Connect module missing at a boundary | Add an explicit connect rule; disable reliance on implicit insertion |
| Fixed thresholds break at corner Vmin | Parameterise VIH/VIL vs `supply.vdd_v` |

### Output Required
- Connect-module sources + connect-rule map (boundary → rule)

---

## Stage: model_validation

### Domain Rules
1. Co-simulate the model against the SPICE reference (the circuit-design netlist in `design_state.circuit.netlist` if present, else a reference cell) on matched stimuli; compute model-vs-SPICE error % on the spec-bearing outputs (gain, BW, offset, noise).
2. Measure the simulation speed-up factor (SPICE wall-time / model wall-time) — the model must be both accurate AND faster to justify itself.
3. For RNM, measure toggle/branch coverage of the model's behavioural arcs; an under-exercised RNM is not validated.
4. If error > tolerance, loop back to va_authoring (cap 3×) targeting the failing output; classify error > tol as `functional` (behaviour wrong) or `spec_violation` (quantitatively off the spec it models).

### QoR Metrics to Evaluate
- Model-vs-SPICE error ≤ tolerance (default 5%) on each spec-bearing output
- Sim speed-up ≥ target (default ≥ 10×) vs the SPICE reference
- RNM toggle/branch coverage ≥ target (default ≥ 90%) for RNM models

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Model-vs-SPICE error > tol | Add the missing parasitic/noise term; refine parameter extraction from the reference |
| Low sim speed-up | Hoist constant computation to `@(initial_step)`; reduce internal nodes |
| RNM coverage low | Add directed stimulus exercising the unhit behavioural arcs |

### Output Required
- Model-vs-SPICE validation report (error %, speed-up, RNM coverage)

---

## Stage: model_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| Compile | OSDI compiles clean (0 errors), loads in ngspice/Xyce |
| Accuracy | model-vs-SPICE error ≤ tolerance on all spec-bearing outputs |
| Speed-up | ≥ target speed-up factor vs the SPICE reference |
| RNM coverage | ≥ target toggle/branch coverage (RNM models) |
| Connect modules | 100% boundary coverage, explicit rules |

### Domain Rules
1. Review the model against the model plan and the spec-traceability map.
2. Confirm accuracy, speed-up, and (for RNM) coverage all pass with margin.
3. Hand off the compiled OSDI / connect modules to ams-verification; record paths in `design_state.modeling`.

### Failure Escalation
- Accuracy miss the author cannot resolve → va_authoring (×3) → escalate (`functional`/`spec_violation`)
- Compile crash → `tool_error` (regenerate); model-shaping non-convergence → `convergence`
- Missing connect rule → `connectivity`

### Output Required
- Sign-off record (compile, accuracy, speed-up, coverage)
- Compiled OSDI / connect modules + validation report for ams-verification

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`model_planning`) — hard-fail if missing:**
- at least one spec to model — a non-null `constraints.specs`/`rf_specs` entry, or an explicit
  per-block spec passed in (e.g. from `architecture.blocks[]`)

**Required at `connect_rule_setup` (only if the model has analog↔digital boundaries):**
- `constraints.supply.vdd_v` — for supply-relative connect-module thresholds

**Optional:**
- `constraints.pdk` — modeling is technology-light; absence is not a failure

Skip constraint validation entirely when invoked in fix-request-servicing mode (a
`fix_request.id` was passed in the prompt).

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/modeling/run_state.md` as the **first action** before launching any tool:
```markdown
run_id:      modeling_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/modeling/experiences.jsonl`
keyed by `run_id` (do not append a second line for the same run). `key_metrics` fields:
`model_error_pct`, `sim_speedup_x`, `rnm_coverage_pct`. Set `signoff_achieved: false` until
model_signoff passes; then `true`. Create the file and parent directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each applied fix as an
observation to entity `analog-design-modeling-fixes` after writing to `experiences.jsonl`.
Skip silently if absent — the JSONL file is the canonical record.
