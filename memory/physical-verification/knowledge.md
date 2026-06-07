# Physical Verification — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain physical-verification`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| DRC spacing/width violation | fix_request → custom-layout (re-route/re-space); `failure_class: drc_lvs` |
| DRC enclosure/via violation | fix_request → custom-layout (fix the via stack); `failure_class: drc_lvs` |
| LVS net short/open | fix_request → custom-layout; `failure_class: connectivity` |
| LVS device-parameter mismatch | fix_request → custom-layout; `failure_class: drc_lvs` |
| Antenna ratio exceeded | fix_request → custom-layout (add diode / jog metal) |
| Floating gate / missing tap (ERC) | fix_request → custom-layout (tie / add well tap) |
| Density outside the PDK window | fix_request → custom-layout (add/thin dummy fill) |

## DRC / LVS Debug Recipes

- Run DRC with Magic **and** KLayout decks; reconcile differences before waiving anything.
- For LVS, extract devices with Magic and compare with Netgen against the LVS-matched `circuit.netlist`; chase the first net mismatch — downstream errors are usually cascades.
- Confirm bulk/well connectivity matches the schematic intent — a missing well tie is a common LVS net mismatch.
- Document every waiver with a foundry-acceptable justification; an undocumented waiver is a sign-off failure.

## PDK Deck Quirks

- **sky130**: use the official `sky130_fd_pr` DRC/LVS decks; some recommended (non-blocking) rules fire on dense fill.
- **gf180mcu**: thick-oxide 5 V devices have distinct spacing/enclosure rules — verify the correct device layer is selected.
- **ihp-sg13g2**: HBT and MIM-cap layers have dedicated LVS device recognition — confirm the device extraction rules are loaded.
- **freepdk45** (predictive/academic): classic single-patterning DRC deck; sign-off here is methodology validation only — non-manufacturable.
- **asap7** (predictive/academic): 7 nm FinFET decks include **multi-patterning/coloring and density checks**; LVS must recognize FinFET devices by fin count. Run KLayout for the coloring rules; treat results as predictive.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `drc_violations`, `lvs_errors`, `antenna_violations`.)_
