# Circuit Simulation — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` (`/analog-design-infrastructure:memory-keeper --domain sim`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| DC non-convergence | Add `.nodeset` on key bias nodes; enable `gmin` stepping then `source` stepping; relax then re-tighten `reltol` |
| Transient "timestep too small" | Add small parasitic caps on high-Z nodes; reduce `reltol`/`abstol` mismatch; check for ideal switches causing discontinuities |
| `.measure` returns `failed`/0 | Trigger/target conditions never met — widen the measurement window or fix the stimulus before declaring a spec fail |
| Spec passes nominal, fails SS/125C/Vmin | Real spec_violation — open a fix_request to circuit-design (re-compensate/re-bias), do not loosen the testbench |
| Monte-Carlo yield short | Yield failure — open a fix_request; centring/area changes belong in circuit-design |

## Successful Solver Flags (ngspice / Xyce)

- ngspice: `set ngbehavior=hsa` for HSPICE-style includes; `option gmin=1e-12 gminsteps=10`; `option method=gear` for ringing-prone tran.
- Xyce: `.options nonlin maxstep=...`; use `.STEP`/sampling for large Monte-Carlo; run with MPI for >1000 samples.
- Always select PDK corner via `.lib "<pdk>.lib" <corner>` — never hardcode device params.

## Corner / MC Practice

- Worst PM is usually SS/hot/Vmin; worst gain at FF/cold; check both extremes plus tt/27C.
- Use mismatch + process Monte-Carlo (not process-only) for offset and yield-sigma.

## Metric Baselines

_(Populated by `memory-keeper`: `worst_pm_deg`, `worst_gain_db`, `mc_yield_sigma`, `failing_corners`, `convergence_failures`.)_
