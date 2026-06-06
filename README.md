# analog-chip-design-agents

> Claude Code marketplace plugin — full analog / mixed-signal + RF chip design pipeline.
> 16 plugins · 14 design domains + infrastructure + meta pipeline orchestrator ·
> open-source **and** proprietary EDA tool coverage.

[![Validate](https://github.com/chuanseng-ng/analog-chip-design-agents/actions/workflows/validate.yml/badge.svg)](https://github.com/chuanseng-ng/analog-chip-design-agents/actions/workflows/validate.yml)

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

```bash
npx analog-chip-design-agents     # auto-detect your AI agents + install (add --yes for CI)
bash install.sh                   # clone-and-run alternative (macOS / Linux / Git Bash)
```

Selective install, Windows/PowerShell, other assistants (Copilot / Gemini / OpenCode / Codex),
and QoR-trend tracking are all covered in **[docs/installation.md](docs/installation.md)**.

---

## Documentation

| Doc | What's in it |
|-----|--------------|
| [docs/installation.md](docs/installation.md) | Every install path, all supported agents, QoR trends |
| [docs/architecture.md](docs/architecture.md) | How the Skill + Orchestrator pattern works, repo structure |
| [docs/design_state_schema.md](docs/design_state_schema.md) | Shared cross-orchestrator `design_state.json` schema |
| [docs/pdk_support.md](docs/pdk_support.md) | PDK / tool coverage matrix (detect-only vs run-in-loop) |
| [docs/PLAN.md](docs/PLAN.md) | Design rationale, end-to-end pipeline, phased roadmap |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Phase-by-phase delivery history |
| [docs/FUTURE_WORK.md](docs/FUTURE_WORK.md) | Deferred enhancements (deeper tool / PDK coverage) |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New domain rules, QoR metrics, loop-back
rules, and tool coverage are all welcome. CI (`validate.yml`) must pass before merge.

## License

MIT — see [LICENSE](LICENSE).
