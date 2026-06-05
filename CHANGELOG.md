# Changelog

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
