# Custom Layout — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain layout`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| Matched-pair mismatch from edge effects | Add/extend edge dummy rows; widen the common-centroid array |
| Asymmetric matched placement | Mirror about the symmetry axis; equalise neighbour context |
| Matched nets length/layer mismatched | Add matched detours; route both on symmetric layers |
| Coupling onto a high-Z node | Re-route with spacing; add a grounded shield trace |
| Antenna ratio exceeded | Add an antenna diode or jog the metal to a higher layer |
| Density below the PDK window | Add dummy fill in non-critical regions (fill-exclude over matched/high-Z nets) |
| Fill perturbs matching | Add a fill-exclude region over matched and high-Z nets |

## Matching & Placement Recipes

- Match critical pairs with **common-centroid / interdigitation**: equal L, integer-ratio W, same orientation, edge dummies.
- Keep matched pairs adjacent and equidistant from heat/IR sources; place the input pair away from switching aggressors.
- Reserve shielded channels for sensitive/bias nets in the floorplan; route bias lines wide and low-impedance.
- Budget ≥ 10% floorplan reserve for guard rings, fill, dummies, and antenna diodes.
- Group by current domain — keep high-current drivers away from small-signal devices to limit substrate/IR coupling.

## PDK Layer Quirks

- **sky130**: wide native-device Vt spread inflates matching area — budget extra dummies; use Magic + KLayout sky130 DRC decks.
- **gf180mcu**: 5 V devices need thick-oxide layers and larger spacing — check enclosure rules on matched arrays.
- **ihp-sg13g2**: SiGe HBT layout has dedicated device generators — prefer them over hand-drawn arrays.
- **freepdk45** (predictive/academic): coarse single-patterning 45 nm rules — good for didactic/topology layout; not silicon-grade.
- **asap7** (predictive/academic): 7 nm FinFET on a fixed fin/track grid with **multi-patterning (layer coloring)** on lower metals; snap devices to the fin pitch and the routing tracks, and keep colorable spacing — KLayout handles the coloring decks better than Magic.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `matching_sigma_pct`, `density_pct`, `area_um2`.)_
