# Architecture — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain architecture`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| Cascaded NF exceeds the chain target | Raise front-stage gain / lower front-stage NF; move gain earlier so later-stage noise is suppressed by `G1·G2…` |
| Cascaded IIP3 below target | Back-load gain less; add degeneration/linearity to the back stages where distortion accumulates |
| Power budget overruns | Trade gain for current on noise-non-critical stages; share a single bias reference |
| Area budget overruns | Reduce passive sizes / use active filtering; relax matching where the budget allows |
| Budget will not close (noise vs power conflict) | Renegotiate the top spec (spec_capture loop) or change the chain architecture |
| Block needs NF below the kT floor at its allotted current | Raise that block's power/area allocation, or relax the top spec |

## Budgeting Recipes

- **Friis noise cascade:** `F = F1 + (F2−1)/G1 + (F3−1)/(G1·G2) + …` (linear power gains). Keep the first stage's NF low and gain high — it dominates the chain NF.
- **IIP3 cascade:** `1/IIP3_tot = 1/IIP3_1 + G1/IIP3_2 + (G1·G2)/IIP3_3 + …` (linear power units). Later stages dominate distortion; do not pile all gain up front.
- **ENOB → SNDR:** target SNDR ≈ `6.02·N + 1.76` dB; split into a noise floor + distortion budget.
- **Reserves:** keep ≥ 10% power and ≥ 15% area in reserve for routing, matching dummies, and back-annotation surprises.
- **Gain distribution:** enough front-end gain to suppress back-stage noise, but not so much that it crushes IIP3.

## Process / Topology Quirks

- **ihp-sg13g2**: SiGe HBT front-ends enable very low NF — prefer for the first stage of low-noise/RF chains.
- **sky130**: wide native-device Vt spread inflates offset/matching area — budget extra area for matched input pairs.
- **gf180mcu**: 5 V devices give headroom for high-swing output drivers — allocate them to the linearity-critical back stage.
- **freepdk45** (predictive/academic): generous 45 nm planar headroom — useful for exploring topologies before committing to a real PDK; results are not silicon-grade.
- **asap7** (predictive/academic): 7 nm FinFET with **tight Vdd headroom** — favor low-stack/folded topologies and budget for quantized-fin device sizing; no statistical data for yield architecture.
- Differential signalling doubles available swing and cancels even-order distortion — worth the area on linearity-limited chains.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `noise_budget_nv`, `power_budget_mw`, `area_estimate_um2`.)_
