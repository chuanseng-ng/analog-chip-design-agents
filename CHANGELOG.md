# Changelog

## [Unreleased] — Phase 5: RF & EM

### Added

- **`analog-design-rf` — RF/mmWave design (implemented).** Seven stages (`rf_spec →
  topology_matching → sparameter_analysis → harmonic_balance → noise_linearity →
  loadpull_optimization → rf_signoff`) closing an LNA/mixer/VCO/PLL/PA block against the
  `rf_specs` table across corners — S-parameter + Rollett `K`-factor stability, harmonic balance,
  Pnoise/PAC noise & IP3, and load-pull for PAE/EVM. **Terminal/branch consumer:** loop-backs are
  stage-local (spec/stability → `topology_matching`, ×2; convergence → `harmonic_balance`, ×2); it
  does **not** open cross-domain fix_requests. Reads the `em` block (Touchstone + fitted lumped
  model) as a **fixed passive data dependency**; when a passive is the limiter it escalates to the
  user recommending an EM re-solve. Writes the expanded `rf` block (`nf_db`, `gain_db`, `iip3_dbm`,
  `phase_noise_dbc_hz`, `p1db_dbm`, `pae_pct`, `evm_pct`, `k_factor`, `s11_db`).
- **`analog-design-em` — EM modeling (implemented).** Seven stages (`em_setup →
  geometry_definition → meshing → em_solve → sparameter_extraction → model_fitting → em_signoff`)
  solving an on-chip passive/antenna, extracting a **passive** (hard-gated) Touchstone S-matrix, and
  fitting a lumped equivalent for circuit-level RF sim. Terminal/branch producer: loop-backs are
  stage-local (passivity/fit → `meshing`/`geometry_definition`, ×2); a fundamental geometry/stackup
  gap escalates. Publishes the new `em` block (`touchstone`, `fitted_model`, `q_factor`, `srf_ghz`,
  `fit_error_pct`, `passivity_pass`) that rf-design consumes.
- **Memory seeds.** `memory/{rf,em}/knowledge.md` seeded with known patterns; `distill.py` already
  registered both domains and their metrics.
- **Schema docs.** `docs/design_state_schema.md` per-domain merged fields now carry the fuller `rf`
  block and the new `em` block, with a flow note describing the `em → rf` data dependency and the
  terminal-consumer status of the RF emphasis tier.

### Notes

- RF/EM are deliberately **not** wired into the meta `fix_request` loop (no `route_to`/`created_by`/
  `failure_class` enum changes) — mirroring the `architecture` and `characterization` precedent.
  The alternative (automating RF↔circuit-design and em↔rf re-solves via fix_requests) is recorded
  as a deferred enhancement in [`FUTURE_WORK.md`](FUTURE_WORK.md).
- The remaining 1 domain (Phase 6: `ams-integration`) stays **skeleton** SKILL/orchestrator.

## [Unreleased] — Phase 4: sign-off depth

### Added

- **`analog-design-reliability` — reliability (implemented).** Six stages (`em_analysis →
  ir_drop → esd_check → latchup_check → aging_analysis → reliability_signoff`) with EM
  current-density margin, power-grid IR-drop, ESD path coverage, latch-up tap/guard-ring checks,
  and HCI/NBTI aging on the extracted netlist. **Opens** fix_requests → custom-layout (EM/IR,
  `failure_class: drc_lvs`) or circuit-design (ESD/aging, `failure_class: spec_violation`). Writes
  the `reliability` block (`em_margin_pct`, `ir_drop_pct`, `esd_violations`).
- **`analog-design-characterization` — characterization (implemented).** Seven stages
  (`char_setup → timing_char → power_char → noise_char → liberty_generation → model_validation →
  char_signoff`) characterizing timing/power/noise across PVT corners, emitting validated Liberty
  (`.lib`) + behavioral models with model-vs-SPICE and monotonicity gates. Terminal consumer:
  loop-backs are stage-local (`model_validation → char_setup`, ×2); a fundamental gap escalates to
  the user rather than opening a cross-domain fix_request. Writes the `char` block (`lib`,
  `lib_arcs`, `char_error_pct`, `corners_covered`).
- **Memory seeds.** `memory/{reliability,characterization}/knowledge.md` seeded with known
  patterns; `distill.py` already registered both domains and their metrics.
- **Schema docs.** `docs/design_state_schema.md` per-domain merged fields now carry the fuller
  `reliability` and `char` blocks, and the flow note extends through the sign-off-depth tier.

### Notes

- The remaining 3 domains (Phases 5–6: `rf`, `em`, `ams-integration`) stay **skeleton**
  SKILL/orchestrators. *(Phase 5 since implemented `rf` and `em`; only `ams-integration` remains.)*

## [Unreleased] — Phase 3: physical-design tier

### Added

- **`analog-design-layout` — custom layout (implemented).** Six stages (`layout_floorplan →
  device_generation → analog_placement → analog_routing → layout_finishing → layout_check`)
  with common-centroid/interdigitation matching, symmetric placement, shielded routing, and
  pre-DRC checks. **Services** fix_requests routed to custom-layout (DRC/LVS repair, parasitic
  reduction). Writes the `layout` block.
- **`analog-design-physical-verification` — physical verification (implemented).** Five stages
  (`drc → lvs → antenna_erc → density_dfm → pv_signoff`) with Magic/KLayout DRC, Netgen LVS,
  antenna/ERC, and density checks. **Opens** fix_requests → custom-layout
  (`failure_class: drc_lvs`/`connectivity`, `route_to: custom-layout`). Writes the
  `physical_verification` block.
- **`analog-design-extraction` — parasitic extraction (implemented).** Five stages
  (`extraction_setup → rc_extraction → coupling_extraction → netlist_back_annotation →
  pex_signoff`) building the back-annotated PEX netlist; the `pex_signoff` checkpoint; flags
  large parasitic degradation to custom-layout. Writes the `pex` block.
- **`analog-design-post-layout` — post-layout sign-off (implemented).** Five stages
  (`pex_netlist_assembly → post_layout_corner_sim → spec_reverification → margin_analysis →
  tapeout_signoff`) re-closing specs on the extracted netlist; the `tapeout_signoff`
  human-approval checkpoint. **Opens** fix_requests → custom-layout (parasitic) or
  circuit-design (fundamental). Writes the `post_layout` block.
- **Meta fix_request routing (enhanced).** Added `custom-layout` to the `route_to` enum and
  `drc_lvs`/`connectivity` to the fix_request `failure_class` enum (and to `VALID_FR_FAILURE`
  in CI); added `custom-layout-orchestrator` as a servicer plus physical-verification/
  parasitic-extraction producers to the participants/dispatch wiring, closing the
  DRC/LVS→layout and parasitic→layout repair loops.
- **Memory seeds.** `memory/{layout,physical-verification,extraction,post-layout}/knowledge.md`
  seeded with known patterns; `distill.py` already registered the four domains and metrics.
- **Schema docs.** `docs/design_state_schema.md` per-domain merged fields now carry the fuller
  `layout`/`pex`/`post_layout` blocks and a new `physical_verification` block.

### Notes

- The remaining 5 domains (Phases 4–6) stay **skeleton** SKILL/orchestrators.

## [Unreleased] — Phase 2: architecture, modeling & AMS verification

### Added

- **`analog-design-architecture` — analog architecture (implemented).** Five stages
  (`spec_capture → signal_chain_budgeting → topology_partitioning → behavioral_feasibility →
  architecture_signoff`) with Friis noise / IIP3-cascade budgeting rules, per-block power/area
  allocation, QoR gates keyed to `constraints.specs`/`rf_specs`/`area_um2`, the
  `architecture_signoff` checkpoint, and memory wiring. As the upstream domain it writes the
  `architecture` block to `design_state.json`; circuit-design reads `architecture.blocks[].specs`
  as its per-block spec source.
- **`analog-design-modeling` — behavioral / AMS modeling (implemented).** Six stages
  (`model_planning → va_authoring → model_compilation → connect_rule_setup → model_validation →
  model_signoff`) with Verilog-A/OSDI (OpenVAF) authoring + convergence rules, connect-module
  setup, model-vs-SPICE accuracy/speed-up/RNM-coverage gates, fix-request-servicing mode (it
  services model faults routed from AMS verification), and memory wiring.
- **`analog-design-ams-verification` — AMS verification (implemented).** Six stages
  (`ams_testbench → connect_module_setup → analog_digital_cosim → rnm_regression →
  coverage_closure → ams_signoff`) with cocotb co-sim, RNM regression, functional-coverage
  closure, and the fix-request-opening flow. Opens `fix_request`s with an optional `route_to`
  hint routed to behavioral-modeling (model fault) or circuit-design (circuit fault).
- **Meta fix_request routing (enhanced).** Added the optional `route_to` field to the
  `fix_request` schema and taught the pipeline-orchestrator to dispatch the chosen servicer
  (circuit-design by default, behavioral-modeling when indicated), closing the AMS→modeling
  repair loop. Existing fixtures unchanged (the field is optional; legacy routing preserved).
- **Memory seeds.** `memory/architecture/knowledge.md`, `memory/modeling/knowledge.md`, and
  `memory/ams-verification/knowledge.md` seeded with known patterns; `distill.py` already
  registered the three domains and their metric fields.
- **Schema docs.** `docs/design_state_schema.md` per-domain merged fields now include the
  `architecture`, `modeling`, and `ams` blocks.

### Notes

- The remaining 9 domains (Phases 3–6) stay **skeleton** SKILL/orchestrators.

## [Unreleased] — Phase 1: core analog spine

### Added

- **`analog-design-meta` — pipeline orchestration (implemented).** Authoritative
  `design_state.json` schema at `format_version "1.0"`: the analog/RF `constraints` schema
  (supply, `specs`, `rf_specs`, PVT + mismatch `corners`, `yield`), the analog `fix_request`
  schema (`spec_violation | convergence | functional | yield`, `suspected_circuit`,
  `circuit_response`), failure-classification → retry-strategy mapping, per-stage `history[]`,
  iteration cap, and approval checkpoints. Ships the `pipeline-orchestrator` agent and two
  worked fixtures (`examples/design_state.fix_request.json`, `examples/design_state.checkpoint.json`).
- **`analog-design-circuit` — circuit (schematic) design (implemented).** Six stages
  (topology_selection → device_sizing → biasing → schematic_capture → pre_layout_erc →
  design_review) with gm/Id sizing rules, QoR gates, common-issue tables, fix-request-servicing
  mode, constraint validation, the `schematic_signoff` checkpoint, and memory wiring.
- **`analog-design-simulation` — circuit simulation (implemented).** Eight stages
  (testbench_setup → dc_op → ac/transient/noise → corner_analysis → monte_carlo → sim_signoff),
  opening `fix_request`s (spec_violation / yield) routed to circuit-design, with corner/MC
  closure rules and memory wiring.
- **`analog-design-infrastructure` — infrastructure + memory-keeper (implemented).**
  Six-stage tool detection/install/wrapper/MCP/validation flow for analog/RF tools; the
  `memory-keeper` skill plus `distill.py` (registers all 16 domains incl. `infrastructure`);
  output-filtering wrappers (`wrap-ngspice/xyce/magic/klayout/netgen/openvaf/openems.sh`); MCP
  batch adapter + interactive ngspice **session** adapter; and 8 MCP config snippets.
- **Memory system**: `memory/README.md`, seeded `knowledge.md` for `circuit`, `sim`,
  `infrastructure`, `meta`, and `memory/designs/.gitkeep`.
- **CI** (`validate.yml`): added `design_state.json` fixture validation (analog `fix_request`
  + checkpoint schemas, history `failure_class`→`retry_strategy` mapping) and the
  infrastructure-memory integration check (`knowledge.md` + `distill.py` registration).

### Notes
- The other 12 domains remain Phase 0 skeletons until their implementation phase (PLAN.md §12).
- Provisional §13 defaults from Phase 0 are unchanged (prefix `analog-design-`, 16 plugins, MIT, sky130-primary).

## [Unreleased] — Phase 0: skeleton & conventions

### Added

- **Repository plan** (`PLAN.md`): full roadmap for an analog/mixed-signal + RF
  Claude Code marketplace mirroring `digital-chip-design-agents` — 16 plugins
  (14 design domains + `infrastructure` + `meta`), per-domain stages/QoR/loop-backs,
  open-source and proprietary tool coverage, the analog `design_state.json` schema,
  and a 6-phase implementation roadmap.
- **Marketplace registry** (`.claude-plugin/marketplace.json`): all 16 plugins
  registered under the `analog-design-<domain>` prefix, marketplace name
  `analog-chip-design-agents`, version `0.1.0`.
- **16 plugin skeletons** (`plugins/<domain>/`): each with a `.claude-plugin/plugin.json`
  manifest, a skeleton `SKILL.md` (frontmatter, purpose, supported open-source +
  proprietary tools, stage sequence, QoR metrics, output requirements), and a
  skeleton orchestrator agent (stage sequence, loop-back rules, sign-off criteria).
  Detailed per-stage Domain Rules and memory/`design_state.json` wiring are deferred
  to each domain's implementation phase.
  - `infrastructure` additionally registers the `memory-keeper` skill.
- **CI** (`.github/workflows/validate.yml`): validates every `plugin.json`,
  `marketplace.json` path resolution, SKILL.md required sections, orchestrator
  frontmatter + required sections, and count consistency (agents == marketplace == 16,
  skills ≥ 16). Extended in later phases for `design_state.json` fixtures, IDE configs,
  and memory integration.
- **Shared state schema** (`docs/design_state_schema.md`): the analog/RF
  `design_state.json` constraints schema (electrical + RF specs, PVT + mismatch
  corners, yield) and per-domain merged fields.
- **Templates** (`docs/templates/`): `SKILL.template.md`, `orchestrator.template.md`,
  and `plugin.template.json` for adding/implementing plugins.
- **Project docs**: `README.md` (marketplace overview + plugin table + phase status),
  `CONTRIBUTING.md` (standards, local validation, PR checklist).

### Notes — decisions adopted from PLAN.md §13

These provisional defaults were used to scaffold Phase 0 and can be revisited before
the domains are fleshed out:

- Plugin prefix: `analog-design-<domain>`.
- Plugin count: **16** (kept `post-layout` sign-off as a standalone plugin).
- License: MIT; same author/homepage/repository convention as the reference repo.
- Default open PDKs targeted: sky130 (primary), gf180mcu, ihp-sg13g2 (RF/SiGe);
  proprietary foundry PDKs are detect-only.
