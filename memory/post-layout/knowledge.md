# Post-Layout Sign-off — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain post-layout`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| PM / CMRR lost to coupling on a high-Z node | fix_request → custom-layout (shield/re-route); `route_to: custom-layout` |
| Bandwidth/GBW lost to added load C | fix_request → custom-layout (reduce net C) or circuit-design (re-size); per cause |
| Fundamental stability-margin loss | fix_request → circuit-design (re-compensate); `route_to: circuit-design` |
| Non-convergence with parasitics | Re-tune solver options / `.nodeset` — do not relax specs |
| Probe net not found in PEX netlist | Re-map names; re-extract with preserved net names |

## Re-sim & Margin Recipes

- Reuse the **pre-layout `.measure` testbench** on the PEX netlist so specs compare like-for-like.
- Re-run the full PVT corner set (and Monte-Carlo where yield matters) on the extracted netlist; collect worst-case + limiting corner per spec.
- Attribute every post-layout miss to a parasitic cause (added C on high-Z, coupling, R on a bias line) to choose the fix route: parasitic → custom-layout, fundamental → circuit-design.
- Track `spec_degradation_pct` vs pre-layout; phase margin (`worst_pm_deg`) is the most parasitic-sensitive spec — check it first.
- The added parasitics change convergence: re-tune solver options, never specs.

## Tool Quirks

- **ngspice / Xyce** on extracted netlists: large flat PEX netlists favour Xyce (parallel); load once via the session MCP and sweep corners.
- Read `.measure` summary files, not raw `.lis` — extracted-netlist logs are very large.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `worst_pm_deg`, `spec_degradation_pct`, `failing_corners`.)_
