# analog-chip-design-agents

> Claude Code marketplace plugin — full analog / mixed-signal + RF chip design pipeline.
> 16 plugins · 14 design domains + infrastructure + meta pipeline orchestrator ·
> open-source **and** proprietary EDA tool coverage.

[![Validate](https://github.com/chuanseng-ng/analog-chip-design-agents/actions/workflows/validate.yml/badge.svg)](https://github.com/chuanseng-ng/analog-chip-design-agents/actions/workflows/validate.yml)

> **✅ Status: complete — all 16 plugins implemented (Phases 0–7).** Every domain ships detailed
> stage rules, memory wiring, and the cross-domain `fix_request` loop, alongside one-step installers
> (`install.sh` / `install.ps1`), multi-IDE export (`ides/`), QoR trend tracking
> (`tools/qor_trends.py`), an end-to-end test harness, and CI. See [`CHANGELOG.md`](CHANGELOG.md) for
> the phase-by-phase delivery history, [`PLAN.md`](PLAN.md) for the design rationale and roadmap, and
> [`FUTURE_WORK.md`](FUTURE_WORK.md) for the remaining deferred enhancements (deeper tool/PDK
> coverage).

This marketplace mirrors the architecture of
[`digital-chip-design-agents`](https://github.com/chuanseng-ng/digital-chip-design-agents),
re-targeted to the analog/mixed-signal + RF flow.

---

## Available Plugins

| Plugin Name | Domain | Invoke When You Want To... |
|-------------|--------|----------------------------|
| `analog-design-architecture` | Analog Architecture | Budget noise/linearity/power across a signal chain, allocate block specs |
| `analog-design-modeling` | Behavioral / AMS Modeling | Write/compile Verilog-A/AMS · VHDL-AMS · SystemVerilog RNM; build connect modules |
| `analog-design-circuit` | Circuit (Schematic) Design | Pick a topology, size/bias devices, capture schematic, run pre-layout ERC |
| `analog-design-simulation` | Circuit Simulation | Run DC/AC/transient/noise, corners, Monte-Carlo; sign off electrical specs |
| `analog-design-ams-verification` | AMS Verification | Build AMS testbench, set connect rules, run analog↔digital co-sim, close coverage |
| `analog-design-layout` | Custom Layout | Floorplan, generate matched devices, place/route with symmetry/shielding |
| `analog-design-physical-verification` | Physical Verification | Run DRC, LVS, antenna/ERC, density/DFM and sign off |
| `analog-design-extraction` | Parasitic Extraction | RC + coupling extraction, build back-annotated post-layout netlist |
| `analog-design-post-layout` | Post-Layout Sign-off | Post-PEX corner + MC sim, re-verify specs, gate tape-out |
| `analog-design-reliability` | Reliability | EM / IR-drop / ESD / latch-up / aging analysis and sign-off |
| `analog-design-characterization` | Characterization | Generate Liberty/.lib + behavioral models, characterize timing/power/noise |
| `analog-design-rf` | RF / mmWave Design | S-param, harmonic balance, Pnoise/PAC, IP3, load-pull for LNA/mixer/VCO/PA |
| `analog-design-em` | EM Modeling | Solve EM for passives/antennas, extract/fit S-parameter models |
| `analog-design-ams-integration` | Mixed-Signal Integration | Qualify analog IP, assemble AMS top, chip-level AMS sim |
| `analog-design-infrastructure` | Infrastructure & Memory | Detect analog/RF tools, deploy wrappers, configure MCP, distil memory |
| `analog-design-meta` | Pipeline Orchestration | Drive closed-loop spec↔circuit↔layout feedback with iteration cap |

---

## Install

All 16 plugins are fully implemented.

### Option A — npm (recommended, no clone)

If you have Node.js (≥18), install and enable all 16 plugins with a single
command — no `git clone` and no Python required. The installer copies each
plugin into your Claude Code plugin cache and enables them in `settings.json`,
then you restart Claude Code:

```bash
npx analog-chip-design-agents
```

Re-run the same command to pick up future updates. Works identically on macOS,
Linux, and Windows (a single Node process copies plugins sequentially, so there
is no concurrent-write contention on the cache directory). This currently
installs the Claude Code plugins only; for other IDEs use Option B below.

### Option B — Install script

Install everything in one step with the bundled scripts (they read the plugin list from
`.claude-plugin/marketplace.json`, so they stay in sync):

```bash
./install.sh            # register the marketplace + install all plugins
./install.sh --list     # list the plugins that would be installed
./install.sh analog-design-circuit analog-design-simulation   # install a subset
```

```powershell
./install.ps1           # Windows / PowerShell equivalent
./install.ps1 -List
```

### Option C — Marketplace (selective install)

If you only need specific domains, install them from inside Claude Code:

```text
/plugin marketplace add github:chuanseng-ng/analog-chip-design-agents
/plugin install analog-design-circuit@analog-chip-design-agents
/plugin install analog-design-simulation@analog-chip-design-agents
```

### Other AI assistants

The same domain knowledge is exported to GitHub Copilot, Gemini, OpenCode, and Codex under
[`ides/`](ides/) (generated from the plugin SKILLs by `tools/export_ides.py` — `plugins/` stays the
source of truth). Regenerate after editing a SKILL with `python3 tools/export_ides.py`.

### QoR trends

Track analog/RF QoR across runs from the per-domain memory logs:

```bash
python3 tools/qor_trends.py --design my_ldo            # trend + regression alerts
python3 tools/qor_trends.py --design my_lna --group-by pdk --format csv
```

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
├── ides/                                ← multi-IDE export (Copilot/Gemini/OpenCode/Codex)
├── memory/                              ← per-domain knowledge.md + experiences.jsonl
├── tools/                               ← qor_trends.py, export_ides.py
├── docs/
│   ├── design_state_schema.md           ← shared cross-orchestrator state schema
│   └── templates/                       ← SKILL / orchestrator / plugin.json templates
├── .github/workflows/                   ← validate.yml (CI) + release.yml (tagged release)
├── install.sh / install.ps1            ← one-step plugin installers
├── PLAN.md                              ← full roadmap (domains, stages, tools, phases)
├── CONTRIBUTING.md  CHANGELOG.md  FUTURE_WORK.md  LICENSE
└── README.md
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New domain rules, QoR metrics, loop-back
rules, and tool coverage are all welcome. CI (`validate.yml`) must pass before merge.

## License

MIT — see [LICENSE](LICENSE).
