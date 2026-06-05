# `design_state.json` — shared cross-orchestrator state (analog/mixed-signal + RF)

`design_state.json` lives in the working directory and is the shared state file all
domain orchestrators read at session start and merge into on termination. It mirrors
the role of the reference repo's `design_state.json`, re-targeted to analog/RF.

> **Status: finalised in Phase 1.** The authoritative schema lives in
> [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../plugins/meta/skills/pipeline-orchestration/SKILL.md)
> (§Constraints Schema, §fix_request Schema, §Failure Classification). The working
> baseline is `format_version "1.0"`. This document summarises the constraints shape that
> domain SKILL/orchestrators reference for their QoR thresholds.

## Constraints

Domain QoR gates read thresholds from `design_state.constraints`, falling back to
documented per-skill defaults when a key is absent.

```jsonc
{
  "design_name": "my_ldo",
  "format_version": "1.0",
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

On termination each orchestrator merges its domain block (current merged shape,
Phase 1–4), e.g.:

```jsonc
{
  "architecture": { "chain_type": "…", "blocks": [ { "name": "…", "specs": {…}, "topology_class": "…", "feasibility": "low|medium|high" } ],
                    "noise_budget_nv": null, "power_budget_mw": null, "area_estimate_um2": null, "signoff": false },
  "modeling":    { "model_source": "…", "osdi": "…", "connect_modules": ["…"], "model_error_pct": null, "sim_speedup_x": null, "rnm_coverage_pct": null, "signoff": false },
  "ams":         { "testbench": "…", "functional_coverage_pct": null, "rnm_mismatch_count": null, "regression_failures": null, "specs_pass": false, "signoff": false },
  "circuit":     { "netlist": "…", "dc_gain_db": null, "phase_margin_deg": null, "signoff": false },
  "sim":         { "specs_pass": false, "mc_yield_sigma": null, "signoff": false },
  "layout":      { "gds": "…", "area_um2": null, "matching_sigma_pct": null, "density_pct": null, "signoff": false },
  "physical_verification": { "drc_violations": null, "lvs_errors": null, "antenna_violations": null, "signoff": false },
  "pex":         { "netlist": "…", "r_count": null, "c_count": null, "coupling_caps": null, "signoff": false },
  "post_layout": { "specs_pass": false, "worst_pm_deg": null, "spec_degradation_pct": null, "failing_corners": null, "signoff": false },
  "reliability": { "em_margin_pct": null, "ir_drop_pct": null, "esd_violations": null, "signoff": false },
  "char":        { "lib": "…", "lib_arcs": null, "char_error_pct": null, "corners_covered": null, "signoff": false },
  "rf":          { "nf_db": null, "iip3_dbm": null, "phase_noise_dbc_hz": null, "signoff": false }
}
```

The `architecture` block is **upstream**: it is written by the analog-architecture
orchestrator before circuit design begins, and circuit-design reads
`architecture.blocks[].specs` as its per-block `constraints.specs` source. The physical tier
flows `layout → physical_verification → pex → post_layout`, and the sign-off-depth tier continues
`reliability → char` on the extracted netlist (reliability EM/IR/ESD/latch-up/aging, then
characterization of the `.lib` + behavioral views). AMS verification, physical-verification,
post-layout, and reliability open `fix_request`s with an optional `route_to` hint
(`circuit-design` | `behavioral-modeling` | `custom-layout`) so the pipeline-orchestrator
dispatches the right servicer — e.g. a DRC/LVS fault (`failure_class: drc_lvs`/`connectivity`)
routes to `custom-layout`, a parasitic-induced post-layout spec loss to `custom-layout` or
`circuit-design`, an EM/IR reliability fault to `custom-layout` and an ESD/aging shortfall to
`circuit-design`. Characterization is a terminal consumer: its loop-backs are stage-local and it
escalates to the user rather than opening a cross-domain `fix_request`.

## History trace

A `history[]` array records each stage decision (timestamp, agent, stage, decision,
confidence, `failure_class`, `retry_strategy`, `suggested_next_step`, reason,
`constraint_ref`). The failure-classification enum and `failure_class → retry_strategy`
mapping are carried over from the reference repo and finalised in Phase 1, with analog
additions such as `convergence` and `yield`/`matching` failure classes.
