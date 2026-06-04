# Circuit Design — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain circuit`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| Two-stage OTA phase margin low at SS/hot | Increase Miller cap; add nulling resistor (~1/gm2) to push the RHP zero into the LHP |
| Device drops out of saturation across corners | Add ≥ 50–100 mV Vds margin over Vdsat; lower current density (raise W) |
| DC gain short of target single-stage | Cascode the output, or add a gain stage; increase L on gain devices |
| Input-referred offset too high | Increase input-pair area (W·L); use larger gm/Id (~15–20) on the input pair |
| Reference fails to start | Add a startup device; verify with a transient from 0 V that the zero-current state is left |
| Reference spread > ±10% over PVT | Use a constant-gm bias instead of absolute-resistor/threshold biasing |

## Successful Sizing Recipes

- Input differential pair: gm/Id ≈ 15–20 (noise/offset/headroom balance).
- Current-source/tail devices: gm/Id ≈ 5–8 (output swing, low noise contribution).
- Gain-critical devices: L > PDK minimum (intrinsic gain, matching); switches: L = min.
- Match critical pairs with equal L, integer-ratio W, same orientation; flag for common-centroid layout.

## PDK Quirks

- **sky130**: native devices have wide Vt spread — budget extra matching area; use `sky130_fd_pr` model corners (tt/ss/ff/sf/fs).
- **gf180mcu**: 5 V devices need explicit thick-oxide selection; check Vds ratings against supply.
- **ihp-sg13g2**: SiGe HBTs available — prefer for low-noise/RF front-ends.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `dc_gain_db`, `phase_margin_deg`, `gbw_hz`, `power_mw`, `erc_errors`.)_
