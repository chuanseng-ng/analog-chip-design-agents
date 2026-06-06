# analog-chip-design-agents

> Claude Code marketplace plugin — full analog / mixed-signal + RF chip design pipeline.
> 16 plugins · 14 design domains + infrastructure + meta pipeline orchestrator ·
> open-source **and** proprietary EDA tool coverage.

[![Validate](https://github.com/chuanseng-ng/analog-chip-design-agents/actions/workflows/validate.yml/badge.svg)](https://github.com/chuanseng-ng/analog-chip-design-agents/actions/workflows/validate.yml)

> **✅ Status: complete — all 16 plugins implemented (Phases 0–7).** Every domain ships detailed
> stage rules, memory wiring, and the cross-domain `fix_request` loop, alongside auto-detecting
> installers (`npx`, `install.sh` / `install.ps1`) that target Claude Code plus Copilot / Gemini /
> OpenCode / Codex, QoR trend tracking
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

If you have Node.js (≥18), run a single command — no `git clone` and no Python
required. With no flags the installer **detects which AI coding agents you have
installed** (Claude Code, OpenAI Codex, OpenCode, Gemini, GitHub Copilot), shows
what it found and where each would write, and installs to them after a
confirmation:

```bash
npx analog-chip-design-agents            # detect installed agents + confirm
npx analog-chip-design-agents --yes      # detect + install, no prompt (CI-friendly)
```

Detection treats an agent as installed if its CLI is on `PATH` **or** its config
directory exists (e.g. `~/.claude`, `~/.codex`, `~/.config/opencode`,
`~/.gemini`). For Claude Code it copies every plugin into your plugin cache and
enables them in `settings.json`; for the others it generates the matching context
files (see Option D). All five targets are handled natively in Node — no Python.

To target a specific agent (or all of them) explicitly and skip detection:

```bash
npx analog-chip-design-agents --ide claude     # or codex | opencode | gemini | copilot | all
npx analog-chip-design-agents --ide gemini --global
```

Re-run any of these to pick up future updates. Works identically on macOS, Linux,
and Windows (a single Node process copies plugins sequentially, so there is no
concurrent-write contention on the cache directory).

### Option B — Install script

Clone the repo and run one script. Like the npm installer, running it with no
flags **auto-detects your installed agents** and installs to them after a
confirmation (add `--yes` / `-y` on `install.sh`, or `-Yes` on `install.ps1`, to
skip the prompt). The shell scripts require `python3`; for a Python-free install
use the npm path (Option A).

```bash
bash install.sh          # macOS / Linux / Git Bash
```

```powershell
.\install.ps1            # Windows / PowerShell
```

### Option C — Marketplace (selective install)

If you only need specific domains, install them from inside Claude Code:

```text
/plugin marketplace add github:chuanseng-ng/analog-chip-design-agents
/plugin install analog-design-circuit@analog-chip-design-agents
/plugin install analog-design-simulation@analog-chip-design-agents
```

### Option D — Other AI assistants (Copilot / Gemini / OpenCode / Codex CLI)

These targets are auto-detected by Options A and B, but you can also install one
explicitly. The npm installer and the shell scripts both support every target
natively; run from your analog design project directory with `--ide`:

```bash
npx analog-chip-design-agents --ide copilot    # .github/instructions/ in your project
npx analog-chip-design-agents --ide gemini     # GEMINI.md (or ~/GEMINI.md with --global)
npx analog-chip-design-agents --ide opencode   # opencode.json; use /mode analog-<domain>
npx analog-chip-design-agents --ide codex      # AGENTS.md (or ~/.codex/instructions.md with --global)
```

Domain knowledge is loaded from the plugin SKILLs at install time — `plugins/`
stays the single source of truth, and the `ides/` templates supply each
assistant's header/glob configuration. Re-run to pick up updates.

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
├── bin/                                 ← npm installer (install.mjs) + agent detection (detect.mjs)
├── ides/                                ← install-time templates (Copilot/Gemini/OpenCode/Codex)
├── memory/                              ← per-domain knowledge.md + experiences.jsonl
├── tools/                               ← qor_trends.py
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
