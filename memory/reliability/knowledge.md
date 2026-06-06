# Reliability — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain reliability`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| EM current density over the layer limit on a power/ground strap | fix_request → custom-layout (widen / add parallel strap); `failure_class: drc_lvs` |
| EM violation on a narrow signal net near a strong driver | fix_request → custom-layout (widen / shorten / split the net); `failure_class: drc_lvs` |
| IR-drop droop at a far device exceeds the headroom budget | fix_request → custom-layout (add grid strap / mesh / widen rail); `failure_class: drc_lvs` |
| Ground bounce breaks analog matching | fix_request → custom-layout (symmetric vss grid / more vias) |
| Missing or undersized ESD clamp on an IO/supply | fix_request → circuit-design (add / resize clamp); `failure_class: spec_violation` |
| ESD discharge metal too narrow | fix_request → custom-layout (widen the ESD bus) |
| Well/substrate tap too far from device (latch-up) | fix_request → custom-layout (add tap) |
| Missing guard ring at an injector | fix_request → custom-layout (add guard ring) |
| Aged spec (gain/offset/Vth) drifts out of range at end-of-life | fix_request → circuit-design (add margin / de-rate / up-size the stressed device); `failure_class: spec_violation` |

## Reliability Analysis Recipes

- Extract per-branch RMS/peak/average currents from the **PEX** netlist at the rated operating
  point; map each onto its metal width to get current density. Use the **DC** EM limit for
  power/ground straps and the **bidirectional** limit for signal nets.
- Apply Black's-equation limits at the **worst-case (max) temperature** corner — EM lifetime is
  strongly temperature-dependent.
- Solve IR drop on the extracted R grid; report `ir_drop_pct` against `vdd_v`. Chase the worst
  droop first — it usually shares a root cause (single-point feed) with the next-worst nodes.
- For ESD, walk every pad/supply for a complete clamp+diode path and check the series-resistance
  and discharge-metal-width budget; cross-domain (supply-to-supply) clamps are easy to miss.
- For aging, re-simulate the key specs on the HCI/NBTI-aged netlist at the rated lifetime and the
  worst V/T corner; flag the single dominant-aging device.

## PDK / Tool Quirks

- **sky130 / gf180mcu / ihp-sg13g2**: EM current-density limits are per metal layer and depend on
  temperature — confirm you load the correct `temp_c` limit table, not the room-temperature one.
- **gf180mcu**: thick-metal top layers carry higher EM budgets — use them for power straps.
- **freepdk45 / asap7** (predictive/academic): EM/IR/aging limits are predictive, not
  silicon-qualified — report reliability margins as advisory and flag the PDK as non-manufacturable.
- **Voltus / RedHawk** (proprietary, detect-only): consume the extracted parasitic + current
  profile; prefer them for full-chip EM/IR when detected. Open-source flow estimates per-net only.
- **Calibre PERC** (proprietary, detect-only): topology-aware ESD/latch-up rule checks — superior
  to geometric-only checks when available.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `em_margin_pct`, `ir_drop_pct`, `esd_violations`.)_
