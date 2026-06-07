# Characterization — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain characterization`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| Missing corner / pin / arc in the generated `.lib` | back-fill from the timing/power tables and re-emit; check the corner grid against `constraints.corners` |
| Non-monotonic NLDM delay/transition table | loop back → char_setup; add index points around the inflection or re-measure that point (hard fail — breaks downstream timing) |
| Model-vs-SPICE error over budget | loop back → char_setup; densify the slew/load grid where the macro is most non-linear |
| Table hole / NaN at one corner | re-run the failing sweep point with widened convergence settings |
| Operating point falls outside the index range | extend the slew/load axes so the integration point is bracketed (no extrapolation at use) |
| Implausible / non-monotonic leakage vs V/T | re-measure with the correct bias state and a longer settling window |
| Noise outlier at a single corner | re-run with a longer transient / finer AC grid |
| Wrong units or operating_conditions in `.lib` header | fix the header template and regenerate |

## Characterization Recipes

- Drive the corner grid from `constraints.corners` (process × `voltage_pct` × `temp_c`); record
  `corners_covered` and confirm it equals the required count before sign-off.
- Choose slew/load index axes that **bracket** the real integration operating point — downstream
  tools must interpolate, never extrapolate.
- Validate against SPICE at **off-grid** spot checks (points that are not characterization nodes);
  on-grid points trivially match and hide interpolation error.
- Check monotonicity of every table as a gate independent of `char_error_pct` — a small average
  error can still hide a non-monotonic inversion that breaks timing closure.
- Power: capture state-dependent leakage for analog bias branches; confirm power trends are
  physically monotonic vs voltage/temperature (a sign flip means a measurement-window error).

## PDK / Tool Quirks

- **sky130 / gf180mcu / ihp-sg13g2**: confirm the device model corner names map to the `.lib`
  `operating_conditions` you emit; mismatched corner labels silently de-correlate timing/power.
- **freepdk45 / asap7** (predictive/academic): corner/model data is predictive and often
  typical-only — characterize what exists, label the `.lib` as predictive, and do not present the
  results as silicon-qualified timing/power.
- **Liberate / SiliconSmart / Solido** (proprietary, detect-only): consume the same testbench
  harness and emit NLDM/CCS directly; prefer them for large arc counts when detected. The
  open-source flow (ngspice/Xyce + Python writers) covers NLDM and basic CCS.
- **Solido ML** (proprietary, detect-only): can reduce the sweep count via ML sampling — only when
  detected; otherwise sweep the full grid.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `lib_arcs`, `char_error_pct`, `corners_covered`.)_
