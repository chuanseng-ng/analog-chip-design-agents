# Changelog

## [Unreleased] — feat/agent-auto-detect: detect the AI agent platform and install natively

### Added

- **Auto-detection of installed AI coding agents.** Running the installer with no
  `--ide` flag now detects which of the five supported agents (Claude Code, OpenAI
  Codex, OpenCode, Gemini, GitHub Copilot) are present, prints what it found and
  where each would write, and installs to them after a confirmation prompt. An
  agent counts as installed if its CLI is on `PATH` **or** its config directory
  exists (`~/.claude`, `~/.codex`, `~/.config/opencode`, `~/.gemini`); Copilot is
  project-scoped and detected via the `gh` / `copilot` CLI. New `bin/detect.mjs`
  is the single source of truth for the detection signatures (mirrored natively in
  `install.sh` / `install.ps1`).
- **`--yes` / `-y` (sh, mjs) and `-Yes` (ps1)** to skip the confirmation prompt;
  detection also auto-proceeds in non-interactive shells (CI, pipes).

### Changed

- **`bin/install.mjs` now installs all five targets natively in Node — no Python
  dependency.** Ported from digital-chip-design-agents: the Copilot / Gemini /
  OpenCode / Codex generators run at install time from the `plugins/` SKILLs.
  Gemini and OpenCode embed runtime file references, so under `npx` the referenced
  payload is copied to a durable `~/.analog-chip-design-agents/payload/<version>/`
  so references survive package-dir reclamation. Explicit `--ide` (including
  `all`) bypasses detection.
- **`install.sh` / `install.ps1` rewritten to parity** with the npm installer:
  detection-by-default, `--ide`/`-IDE` (`claude|copilot|gemini|opencode|codex|all`),
  `--global`, `--yes`/`-y` (`-Yes`), and per-IDE native generation. They still
  require `python3` (the Claude block reads plugin versions and merges
  `settings.json`); the fully Python-free path is the npm installer. The previous
  Claude-only `claude plugin install` marketplace wrapper (and its `--list` /
  positional-plugin args) is removed.
- **`ides/` is now install-time templates, not committed exports.** The Copilot
  header + `applyto-map.json`, `gemini-header.md`, `opencode-base.json`, and Codex
  header drive install-time generation. Removed `tools/export_ides.py`, its CI
  freshness gate in `validate.yml`, its pytest suite, and the committed
  `ides/gemini/GEMINI.md` / `ides/opencode/AGENTS.md` mirrors — `plugins/` remains
  the single source of truth.
- **`README.md`** documents auto-detection, the `--yes` flag, per-IDE explicit
  install, and that the npm path installs every supported target with no Python.

## [Unreleased] — Repo quality: schema, tests & end-to-end harness

### Added

- **Machine-readable `design_state.json` schema.** `docs/design_state.schema.json` (JSON Schema
  2020-12) encodes the enums, required fields, and the `failure_class → retry_strategy` map. CI now
  validates the example fixtures against it via `jsonschema`, replacing ~115 lines of hand-rolled,
  drift-prone enum checks in `validate.yml`. A negative fixture under
  `plugins/meta/skills/pipeline-orchestration/examples/invalid/` proves the schema rejects bad input.
- **End-to-end validation harness** (closes the deferred item in [`FUTURE_WORK.md`](FUTURE_WORK.md)).
  `tests/e2e/run_pipeline.py` is a dependency-free replica of the meta dispatch rules that drives
  `design_state.json` through `open → claimed → fixed`, honouring `route_to`/`created_by` routing,
  the cross-domain iteration cap, the checkpoint gate, and the sign-off criteria. Two reference
  designs under `examples/designs/` (`ldo_pm`, `lna_nf`) serve as worked examples; `tests/test_e2e.py`
  asserts sign-off, cap escalation, checkpoint gating, intake halt, and schema-validity of emitted
  state.
- **Python tool test suite.** `tests/` adds pytest coverage for the previously untested
  `tools/qor_trends.py`, `tools/export_ides.py`, and the memory-keeper `distill.py`, run by a new
  `tests` CI job.
- **CI: `ides/` freshness gate.** `validate.yml` now runs `tools/export_ides.py --check` so the
  generated multi-IDE exports cannot silently drift from the `plugins/` SKILLs. Push/PR branch
  triggers were aligned (dropped the stale `master`).
- **Real tool path: ngspice smoke test.** A PDK-independent deck
  (`examples/designs/ldo_pm/smoke/divider.sp`) runs through
  `plugins/infrastructure/tools/wrap-ngspice.sh` in `tests/test_tool_smoke.py` (skipped where the
  binary is absent), promoting ngspice from detect-only to *smoke*. New coverage matrix at
  [`docs/pdk_support.md`](docs/pdk_support.md) makes the detect-only vs run-in-loop boundary explicit
  (partially addresses the deferred *deeper tool / PDK coverage* item).

## [Unreleased] — Phase 7: RF/EM cross-domain integration

### Added

- **RF wired into the meta cross-domain `fix_request` loop.** `rf-design` is no longer a
  terminal/branch consumer — it is now a cross-domain **producer**. After its stage-local caps
  (`topology_matching` for a spec/stability miss, `harmonic_balance` for non-convergence) are
  exhausted and the block still misses spec, the `rf-design-orchestrator` **opens** a `fix_request`
  (`created_by: rf-design-orchestrator`, `failure_class: spec_violation`, `retry_strategy: refine`)
  routed to `circuit-design` (device-level rework) or `em-modeling` (an on-chip passive is the
  limiter — low Q / under-spec SRF). User escalation is now reserved for a genuine `spec_gap` or a
  cross-domain-cap hit.
- **`em-modeling` as a cross-domain servicer.** `em-modeling` now **services** rf-design-raised
  `fix_request`s (`route_to: em-modeling`): claims the entry (`open→claimed`), re-solves the passive
  toward a higher-Q / higher-SRF target, republishes the `em` block (Touchstone + fitted lumped
  model), and closes it (`status: fixed`) with a `circuit_response` (`files_changed` = the
  republished Touchstone / fitted-model artifacts). It still never *opens* a `fix_request` itself.
- **Meta wiring.** `plugins/meta` (pipeline-orchestration skill + pipeline-orchestrator agent) add
  `rf-design-orchestrator` to the `created_by` enum and `em-modeling` to the `route_to` enum; the
  participants table, ownership rules, and dispatch pattern add em-modeling as a servicer and
  rf-design as the re-validation target (re-validation is selected by `created_by`). Spawn forms add
  `analog-design-em:em-modeling-orchestrator` (servicer) and `analog-design-rf:rf-design-orchestrator`
  (re-validation).
- **Schema + fixture.** `docs/design_state_schema.md` rewrites the RF emphasis tier from
  "terminal/deferred" to the now-wired cross-domain routing. The CI fixture
  `plugins/meta/skills/pipeline-orchestration/examples/design_state.fix_request.json` gains a
  representative RF→em-modeling fix_request (NF limited by inductor Q, serviced by an EM re-solve and
  re-validated by RF).

### Notes

- Reuses the existing `failure_class: spec_violation → retry_strategy: refine` mapping — no new
  failure-class enum, so `validate.yml` (`VALID_FR_FAILURE` / `RETRY_STRATEGY_MAP`) is unchanged.
- Closes the sole RF/EM enhancement deferred from Phase 5 (see [`FUTURE_WORK.md`](FUTURE_WORK.md)).
  The remaining deferred items are the end-to-end validation harness and deeper tool/PDK coverage.
- `ides/` regenerated from the updated RF/EM SKILLs via `tools/export_ides.py`.

## [Unreleased] — Phase 6: integration & polish

### Added

- **`analog-design-ams-integration` — mixed-signal top integration (implemented).** The last
  skeleton domain is filled in. Six stages (`ip_qualification → top_assembly →
  boundary_connect_rules → chip_level_ams_sim → power_intent_check → integration_signoff`) qualify
  signed-off analog/RF/digital IP, assemble the mixed-signal top (netlist + IO/ESD ring + supply
  network), define explicit top-level connect/level-shifter rules, run chip-level AMS co-sim, and
  check power intent through a human-approval sign-off (chip tape-out gate). Full per-stage Domain
  Rules, QoR gates, Common-Issues tables, constraint validation, and memory wiring. **Wired into
  the meta cross-domain loop:** opens fix_requests routed to `custom-layout` (top-LVS/connectivity,
  `failure_class: connectivity`), `circuit-design` (block functional/spec miss, `functional`/
  `spec_violation`), or `behavioral-modeling` (connect-module/RNM divergence, `functional`); the
  pipeline-orchestrator re-validates via the ams-integration orchestrator. Writes the new
  `ams_integration` block (`top_netlist`, `top_lvs_errors`, `ams_sim_pass`, `connect_rule_errors`,
  `functional_coverage_pct`, `power_intent_pass`, `esd_ring_complete`, `island_isolation_pass`).
- **Meta wiring.** `plugins/meta` (skill + pipeline-orchestrator agent) add
  `ams-integration-orchestrator` as a fix_request producer and a re-validation dispatch target.
  `docs/design_state_schema.md` adds the `ams_integration` block and describes its downstream
  cross-domain routing. `memory/ams-integration/knowledge.md` seeded with known patterns
  (`distill.py` already registered the domain + its `top_lvs_errors`/`ams_sim_pass`/
  `connect_rule_errors` metrics).
- **Distribution.** `install.sh` / `install.ps1` — one-step installers that register the
  marketplace and install every plugin read from `.claude-plugin/marketplace.json` (supports a
  `--list` flag and an explicit plugin subset).
- **Multi-IDE export.** `ides/` (Copilot / Gemini / OpenCode / Codex) generated from the plugin
  SKILLs by `tools/export_ides.py` (with a `--check` mode for CI); `plugins/` stays the source of
  truth.
- **Tooling.** `tools/qor_trends.py` — trends analog/RF QoR metrics (`dc_gain_db`,
  `phase_margin_deg`, `nf_db`, `power_mw`, `mc_yield_sigma`, `ir_drop_pct`, the ams-integration
  metrics, …) across runs from the per-domain `experiences.jsonl`, with regression alerts and
  `--group-by pdk|tool|domain`.
- **Release CI.** `.github/workflows/release.yml` — on a `v*` tag (or manual dispatch), reuses
  `validate.yml` as a gate, packages the marketplace (tar.gz + zip), and publishes a GitHub Release
  with auto-generated notes.

### Notes

- Wiring **RF/EM** into the meta fix_request loop remains a separate deferred enhancement
  (see [`FUTURE_WORK.md`](FUTURE_WORK.md)); only `ams-integration` gains meta wiring in this phase.
- All 16 plugins are now fully implemented — Phase 6 completes the roadmap.

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
