# Behavioral / AMS Modeling — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain modeling`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| OpenVAF compile error (unsupported construct) | Replace with an OSDI-supported form; remove non-differentiable `if` on solution variables |
| OSDI loads but won't instantiate | Reconcile discipline/nature mismatch and port order against the netlist |
| Non-convergence when OSDI is loaded in ngspice/Xyce | Smooth discontinuities with `$limexp` / `tanh` clamps; add a small conductance to floating internal nodes |
| Model-vs-SPICE error > tolerance | Add the missing parasitic / noise term; refine parameter extraction from the reference |
| Low simulation speed-up | Hoist constant computation to `@(initial_step)`; reduce the number of internal nodes |
| RNM `x`/`z` propagating into arithmetic | Add a resolution/threshold function at the boundary; default `wreal` to a finite value |

## Authoring Recipes

- **Verilog-A idioms:** drive branches with contribution `<+`; compute constants once under `@(initial_step)`; bound parameters with `from [...]` and physical defaults; keep all contributions continuous/differentiable for a well-conditioned Jacobian.
- **Noise:** add `white_noise(...)` and `flicker_noise(...)` where the block's noise spec matters, so model-vs-SPICE noise comparison is meaningful.
- **RNM (`nettype`/`wreal`):** define resolution functions for multi-driver nets; quantise/threshold at digital boundaries; never let `'z`/`'x` reach arithmetic.
- **Connect modules:** parameterise VIH/VIL relative to `supply.vdd_v` so the same module works across the corner supply range; never rely on implicit insertion.

## Tool Quirks

- **OpenVAF vs ADMS**: OpenVAF (→ OSDI) is the primary path for ngspice/Xyce; ADMS (→ C) is legacy and supports a different construct subset — prefer OpenVAF unless a model only compiles under ADMS.
- **ngspice vs Xyce OSDI loading**: load syntax and supported analyses differ — confirm a trivial DC/tran loads before validating.
- **Verilator vs Icarus RNM**: Verilator has the broader `nettype`/`wreal` support; Icarus lags on some real-number constructs — check coverage tooling against the chosen simulator.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `model_error_pct`, `sim_speedup_x`, `rnm_coverage_pct`.)_
