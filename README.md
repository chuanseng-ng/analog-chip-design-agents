# analog-chip-design-agents

> Claude Code marketplace plugin — full analog / mixed-signal + RF chip design pipeline.
> 16 plugins · 14 design domains + infrastructure + meta pipeline orchestrator ·
> open-source **and** proprietary EDA tool coverage.

[![Validate](https://github.com/chuanseng-ng/analog-chip-design-agents/actions/workflows/validate.yml/badge.svg)](https://github.com/chuanseng-ng/analog-chip-design-agents/actions/workflows/validate.yml)

> **🚧 Status: Phase 0 (skeleton & conventions).** The repository structure,
> marketplace registry, per-plugin manifests, CI, and the shared `design_state.json`
> schema are in place. Each domain currently ships a **skeleton** SKILL/orchestrator
> that captures its stage sequence, tool lists, and QoR metrics; detailed per-stage
> rules are filled in across phases 1–6. See [`PLAN.md`](PLAN.md) for the full roadmap
> and phase order.

This marketplace mirrors the architecture of
[`digital-chip-design-agents`](https://github.com/chuanseng-ng/digital-chip-design-agents),
re-targeted to the analog/mixed-signal + RF flow.

---

## Available Plugins

| Plugin Name | Domain | Invoke When You Want To... | Phase |
|-------------|--------|----------------------------|-------|
| `analog-design-architecture` | Analog Architecture | Budget noise/linearity/power across a signal chain, allocate block specs | 2 |
| `analog-design-modeling` | Behavioral / AMS Modeling | Write/compile Verilog-A/AMS · VHDL-AMS · SystemVerilog RNM; build connect modules | 2 |
| `analog-design-circuit` | Circuit (Schematic) Design | Pick a topology, size/bias devices, capture schematic, run pre-layout ERC | 1 |
| `analog-design-simulation` | Circuit Simulation | Run DC/AC/transient/noise, corners, Monte-Carlo; sign off electrical specs | 1 |
| `analog-design-ams-verification` | AMS Verification | Build AMS testbench, set connect rules, run analog↔digital co-sim, close coverage | 2 |
| `analog-design-layout` | Custom Layout | Floorplan, generate matched devices, place/route with symmetry/shielding | 3 |
| `analog-design-physical-verification` | Physical Verification | Run DRC, LVS, antenna/ERC, density/DFM and sign off | 3 |
| `analog-design-extraction` | Parasitic Extraction | RC + coupling extraction, build back-annotated post-layout netlist | 3 |
| `analog-design-post-layout` | Post-Layout Sign-off | Post-PEX corner + MC sim, re-verify specs, gate tape-out | 3 |
| `analog-design-reliability` | Reliability | EM / IR-drop / ESD / latch-up / aging analysis and sign-off | 4 |
| `analog-design-characterization` | Characterization | Generate Liberty/.lib + behavioral models, characterize timing/power/noise | 4 |
| `analog-design-rf` | RF / mmWave Design | S-param, harmonic balance, Pnoise/PAC, IP3, load-pull for LNA/mixer/VCO/PA | 5 |
| `analog-design-em` | EM Modeling | Solve EM for passives/antennas, extract/fit S-parameter models | 5 |
| `analog-design-ams-integration` | Mixed-Signal Integration | Qualify analog IP, assemble AMS top, chip-level AMS sim | 6 |
| `analog-design-infrastructure` | Infrastructure & Memory | Detect analog/RF tools, deploy wrappers, configure MCP, distil memory | 1 |
| `analog-design-meta` | Pipeline Orchestration | Drive closed-loop spec↔circuit↔layout feedback with iteration cap | 1 |

---

## Install (preview)

> Domains are skeletons until their phase lands; installing now gives you the
> structure and planned scope, not yet the full flow logic.

```text
/plugin marketplace add github:chuanseng-ng/analog-chip-design-agents
/plugin install analog-design-circuit@analog-chip-design-agents
/plugin install analog-design-simulation@analog-chip-design-agents
```

A one-step `install.sh` / `install.ps1` and multi-IDE export (Copilot/Gemini/
OpenCode/Codex), matching the reference repo, arrive in **Phase 6**.

---

## How It Works

Each plugin installs two things, exactly as in the reference repo:

1. **A Skill** (`plugins/<domain>/skills/<skill>/SKILL.md`) — domain knowledge Claude
   reads before executing: stage-by-stage rules, QoR metrics, supported open-source
   and proprietary tools, and output requirements.

2. **An Orchestrator Agent** (`plugins/<domain>/agents/<domain>-orchestrator.md`) — a
   subagent that sequences stages, enforces pass/fail criteria, applies loop-back
   rules when a stage fails, and escalates when human input is needed.

The 14 design domains map to the end-to-end analog/mixed-signal + RF pipeline
diagrammed in [`PLAN.md` §3](PLAN.md). Cross-domain feedback (e.g. a failed
Monte-Carlo run looping back to circuit design) is driven by the `meta` pipeline
orchestrator through a shared `design_state.json`
([schema](docs/design_state_schema.md)).

---

## Repo Structure

```
analog-chip-design-agents/
├── .claude-plugin/marketplace.json      ← registry of all 16 plugins
├── plugins/                             ← one isolated dir per plugin
│   └── <domain>/
│       ├── .claude-plugin/plugin.json
│       ├── agents/<domain>-orchestrator.md
│       └── skills/<skill>/SKILL.md
├── docs/
│   ├── design_state_schema.md           ← shared cross-orchestrator state schema
│   └── templates/                       ← SKILL / orchestrator / plugin.json templates
├── .github/workflows/validate.yml       ← CI: validates manifests, skills, agents
├── PLAN.md                              ← full roadmap (domains, stages, tools, phases)
├── CONTRIBUTING.md  CHANGELOG.md  LICENSE
└── README.md
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New domain rules, QoR metrics, loop-back
rules, and tool coverage are all welcome. CI (`validate.yml`) must pass before merge.

## License

MIT — see [LICENSE](LICENSE).
