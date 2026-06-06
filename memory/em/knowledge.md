# EM Modeling — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain em`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| Non-passive S-matrix (eigenvalue of I−SᴴS < 0) | loop back → meshing (refine edges/gaps), then geometry_definition (hard fail — max 2×) |
| Coarse mesh → poor lumped fit | refine the mesh below λ/20 at f_max, skin-depth-aware at conductor edges |
| FDTD energy not decayed (no convergence) | extend timesteps / check excitation & boundary (PML) setup; re-solve |
| Self-resonance falls below the frequency grid | extend the grid past the expected SRF before solving |
| `fit_error_pct` over budget | raise the fit order / use a broadband (vector) fit; if EM data is the limiter, loop back → meshing |
| Fitted model non-passive | enforce passivity in the fit; if unachievable, loop back → meshing |
| SRF / Q implausible vs expectation | check port placement / de-embedding reference planes; re-extract |
| Resource / runtime limit on a 3D solve | reduce the domain / coarsen within λ/20, or escalate resource_limit |

## EM Recipes

- Pick the solver by problem: openEMS (FDTD) for distributed / high-frequency passives and antennas;
  FastHenry/FastCap (quasi-static) for lumped RL/C well below SRF — quasi-static is far faster but
  invalid near resonance.
- Mesh at ≤ λ/20 at the top frequency and refine at conductor edges and coupled gaps
  (skin-depth-aware) — under-resolution is the usual root cause of a non-passive extraction.
- **Passivity is a hard gate**, not a warning: a non-passive Touchstone makes downstream
  circuit-level RF sim unstable. Check both the extracted S-matrix and the fitted model.
- De-embed to defined reference planes before extracting Q/SRF; a misplaced port plane corrupts
  both figures even when the field solve is correct.
- Publish the Touchstone + fitted lumped model into `design_state.em` — that block is the fixed
  data dependency `rf-design` reads (it never re-solves EM itself).

## PDK / Tool Quirks

- **Stack-up from `constraints.pdk`**: conductor thicknesses, dielectric heights, and metal
  conductivity all come from the PDK; without a layer stack there is no geometry to solve.
- **openEMS**: set `TOOL_TIMEOUT_S` for batch MCP short solves; long 3D solves run via Bash and
  write Touchstone directly — read the summary, not the field dump.
- **HFSS / SIwave / EMX / Sonnet / Momentum** (proprietary, detect-only): faster and more accurate
  for complex 3D; use when detected, otherwise openEMS + scikit-rf covers inductors/transformers/
  lines and basic antennas.
- **ihp-sg13g2**: the open RF/SiGe PDK with the thick-metal layers that make on-chip inductors and
  transformers worth EM-modeling in the first place.
- **freepdk45 / asap7** (predictive/academic): not RF/EM targets — no characterized thick-metal
  passive stack, so any EM solve uses predictive geometry only. Stick with `ihp-sg13g2` for
  inductors/transformers.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `q_factor`, `srf_ghz`, `fit_error_pct`.)_
