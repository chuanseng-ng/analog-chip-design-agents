# `design_state.json` — shared cross-orchestrator state (analog/mixed-signal + RF)

`design_state.json` lives in the working directory and is the shared state file all
domain orchestrators read at session start and merge into on termination. It mirrors
the role of the reference repo's `design_state.json`, re-targeted to analog/RF.

> **Status: Phase 0 schema sketch.** The authoritative schema, `format_version`
> tiers, and the `history[]` failure-classification rules are finalised in **Phase 1**
> alongside the `meta` pipeline orchestrator. This document defines the constraints
> shape that domain SKILL/orchestrators reference for their QoR thresholds.

## Constraints

Domain QoR gates read thresholds from `design_state.constraints`, falling back to
documented per-skill defaults when a key is absent.

```jsonc
{
  "design_name": "my_ldo",
  "format_version": "0.1",
  "constraints": {
    "supply":   { "vdd_v": 1.8, "vss_v": 0.0 },

    "specs": {                          // analog block specs (per top-level block)
      "dc_gain_db": 60,
      "gbw_hz": 1e7,
      "phase_margin_deg": 60,
      "input_noise_nv_rthz": 10,
      "psrr_db": 70,
      "cmrr_db": 80,
      "offset_mv_max": 5,
      "power_mw": 2.0,
      "settling_ns": 100,
      "thd_db": -60,
      "iip3_dbm": 0
    },

    "rf_specs": {                       // populated for rf-design / em-modeling
      "nf_db": 3,
      "gain_db": 20,
      "s11_db_max": -10,
      "iip3_dbm": -5,
      "p1db_dbm": 0,
      "phase_noise_dbc_hz": -100,
      "pae_pct": 30,
      "evm_pct": 3
    },

    "corners": {                        // PVT + analog statistical
      "process": ["tt", "ss", "ff", "sf", "fs"],
      "mismatch": true,
      "temp_c": [-40, 27, 125],
      "voltage_pct": [-10, 0, 10]
    },

    "yield":   { "target_sigma": 3, "mc_samples": 1000 },
    "area_um2": 50000,
    "pdk": "sky130"                     // sky130 | gf180mcu | ihp-sg13g2 | <proprietary, detect-only>
  }
}
```

### Required vs optional

- **Required at the first design stage** (hard-fail / escalate if missing):
  `supply.vdd_v`, at least one entry in `specs` (or `rf_specs` for RF blocks),
  `corners.process` (≥ 1), and `pdk`.
- **Optional** (per-skill defaults apply): individual `specs`/`rf_specs` fields not
  relevant to the block, `yield.target_sigma` (default 3), `area_um2`,
  `corners.temp_c` / `voltage_pct`.

## Per-domain merged fields

On termination each orchestrator merges its domain block (Phase-1 finalised shape),
e.g.:

```jsonc
{
  "circuit":     { "netlist": "…", "dc_gain_db": null, "phase_margin_deg": null, "signoff": false },
  "sim":         { "specs_pass": false, "mc_yield_sigma": null, "signoff": false },
  "layout":      { "gds": "…", "area_um2": null, "signoff": false },
  "pex":         { "netlist": "…", "signoff": false },
  "post_layout": { "specs_pass": false, "signoff": false },
  "reliability": { "em_margin_pct": null, "ir_drop_pct": null, "signoff": false },
  "char":        { "lib": "…", "signoff": false },
  "rf":          { "nf_db": null, "iip3_dbm": null, "phase_noise_dbc_hz": null, "signoff": false }
}
```

## History trace

A `history[]` array records each stage decision (timestamp, agent, stage, decision,
confidence, `failure_class`, `retry_strategy`, `suggested_next_step`, reason,
`constraint_ref`). The failure-classification enum and `failure_class → retry_strategy`
mapping are carried over from the reference repo and finalised in Phase 1, with analog
additions such as `convergence` and `yield`/`matching` failure classes.
