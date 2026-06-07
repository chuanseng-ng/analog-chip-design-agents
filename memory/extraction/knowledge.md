# Parasitic Extraction — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain extraction`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| Net not extracted | Fix the extraction deck / layer map; re-run from extraction_setup |
| Implausibly low R/C count | Deck error — re-select the deck for `constraints.pdk` (extraction_setup ×2) |
| Missing coupling on a high-Z net | Field-solve that net (FastCap); add it to the coupling deck |
| Coupling too large to meet specs | Flag → custom-layout (re-route / shield); `route_to: custom-layout` |
| PEX names don't map to the testbench | Preserve LVS net names; re-annotate |
| PEX netlist too large to simulate | Lump non-critical R/C; keep coupling only on sensitive nets |

## Extraction Recipes

- Pick the extraction type by sensitivity: R-only for digital-ish nets, full RC for analog, RC+coupling for high-Z / matched / clock nets.
- Build the coupling-net list from the layout-sensitivity notes (high-Z nodes, matched diff pairs, clocks).
- Use **Magic `ext2spice`** for RC and **FastCap** field-solving for the few critical high-Z nodes where deck C is insufficient.
- Preserve LVS net/device names through back-annotation so post-layout `.measure` maps to the schematic.
- Sanity-check `r_count`/`c_count` against layout complexity — an order-of-magnitude-low count means a deck/layer-map error.

## PDK / Tool Quirks

- **Magic ext2spice**: set the correct `extresist`/`ext2spice` options per PDK; sky130 needs the sky130 extraction tech file.
- **KLayout PEX**: R is reliable, C is limited — escalate critical coupling to a field solver.
- **gf180mcu / ihp-sg13g2**: confirm the per-layer R/C tables match the foundry corner before trusting accuracy vs golden.
- **freepdk45 / asap7** (predictive/academic): R/C tables are **predictive, not foundry-calibrated** — use PEX for relative/methodology comparisons, never as silicon-accurate parasitics. asap7's multi-patterned metals make coupling especially approximate.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `r_count`, `c_count`, `coupling_caps`.)_
