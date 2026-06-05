# AMS Verification — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain ams-verification`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| Analog/digital time drift in co-sim | Tighten the sync step; enable rollback; align the analog max-timestep to the digital tick |
| Co-sim functional mismatch (model wrong) | Open a `fix_request` → behavioral-modeling (`functional`); set `route_to: behavioral-modeling` |
| Co-sim functional mismatch (circuit wrong) | Open a `fix_request` → circuit-design (`functional`); set `route_to: circuit-design` |
| RNM diverges from SPICE | Re-validate RNM thresholds/quantisation in the model (modeling `fix_request`) |
| Functional coverage hole | Add directed / constrained-random stimulus in `ams_testbench` (loop ×2) |
| Implicit connect-module insertion | Add an explicit connect rule at the boundary; count implicit insertions as errors |
| Vacuously-passing assertion | Add stimulus that drives the antecedent so the check is real |

## Verification Recipes

- **cocotb + ngspice/Xyce harness:** drive the analog DUT through the co-sim handshake; encode every verified spec as a cocotb assertion/scoreboard, never a waveform eyeball.
- **Deterministic regressions:** fix the RNG seed and record it; sweep a seed/corner matrix so a single failing seed is reproducible.
- **Covergroup design:** define coverpoints over the spec-relevant analog state and the PVT corner space; track assertion coverage so no check passes vacuously.
- **Sync trade-off:** lockstep is simpler but slower; rollback is faster but needs a re-startable analog engine — pick per engine support.

## Tool Quirks

- **cocotb ↔ ngspice handshake**: timestamp alignment is the usual source of drift — verify consistent timestamps before trusting a mismatch.
- **Verilator RNM limits**: some real-number constructs are unsupported — confirm the RNM compiles under the chosen simulator before regressing.
- **Xyce mixed-signal vs external cocotb**: Xyce's built-in mixed-signal path and the external cocotb co-sim have different boundary semantics — keep connect rules explicit in both.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `functional_coverage_pct`, `rnm_mismatch_count`, `regression_failures`.)_
