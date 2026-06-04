# Changelog

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
