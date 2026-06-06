# RF / mmWave Design — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain rf`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| `K < 1` (potentially unstable) in-band | loop back → topology_matching; add stabilization (series R / resistive feedback) or re-match |
| Return loss misses `s11_db_max` | loop back → topology_matching; re-tune the input/output matching network |
| HB fails to converge at high drive | retry harmonic_balance with more harmonics / source-stepping / continuation (max 2×) |
| `nf_db` over target, limiter = inductor Q | escalate recommending an em re-solve for a higher-Q passive (no local fix) |
| `iip3_dbm` / phase-noise miss from the circuit | loop back → topology_matching; re-bias / re-top |
| `pae_pct` / `evm_pct` miss with a realizable load | loop back → topology_matching; re-size the output stage per the load-pull optimum |
| Optimum load needs a passive beyond Q/SRF | escalate recommending an em re-solve of the output passive |
| Match operating above a passive's SRF | re-select / re-match below SRF; escalate to em if no on-chip option |

## RF Recipes

- Drive the spec table from `constraints.rf_specs` (fall back to `constraints.specs` for a baseband
  block); record which specs are in scope by block class (PA → pae/p1db/evm; VCO/PLL → phase noise;
  LNA/mixer → nf/gain/s11/iip3) before designing.
- Read S-parameters from the tool summary / Touchstone file, never raw frequency dumps; large HB
  spectra and S-param matrices overflow context.
- Consume the EM-fitted passive model from `design_state.em` (Touchstone + lumped fit) — never an
  ideal inductor at sign-off; the EM Q/SRF directly set NF and matching feasibility.
- Treat `k_factor` ≥ 1 (Rollett) as a stability gate **independent** of spec margin — a design can
  meet gain/NF and still be conditionally unstable.
- Two loop-back triggers both target `topology_matching`: small-signal (s11/K) from
  sparameter_analysis, and large-signal (nf/iip3/phase-noise/pae) from noise_linearity /
  loadpull_optimization. HB non-convergence retries `harmonic_balance` settings, not the topology.

## PDK / Tool Quirks

- **ihp-sg13g2** (SiGe BiCMOS): the RF-capable open PDK — HBTs for LNA/PA/VCO; prefer it over
  sky130/gf180mcu for true RF blocks.
- **freepdk45 / asap7** (predictive/academic): not RF PDKs — no HBTs and no characterized passive
  stack; asap7's FinFETs can model mm-wave FET behavior only as predictive exploration. For real RF
  blocks stay on `ihp-sg13g2`.
- **Qucs-S vs Xyce HB**: Qucs-S has a friendlier HB front-end; Xyce HB scales better for large
  multi-tone problems. If both are present, prefer Xyce for many corners.
- **Spectre RF / ADS / AWR MWO** (proprietary, detect-only): superior HB/Pnoise/load-pull
  convergence; use when detected, otherwise the open flow (Qucs-S/Xyce HB + scikit-rf) covers
  S-param, HB, and basic load-pull.
- **scikit-rf**: use for K/Δ stability, de-embedding, and Touchstone manipulation — it does not
  solve circuits, only post-processes S-parameters.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `nf_db`, `gain_db`, `iip3_dbm`, `phase_noise_dbc_hz`.)_
