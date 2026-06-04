---
name: infrastructure
description: >
  EDA tool detection, wrapper deployment, and MCP configuration for analog/mixed-signal +
  RF design environments. Use when setting up a workstation, verifying tool availability
  before a domain flow, or generating per-tool install scripts with TCL modulefiles.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Infrastructure Setup

## Invocation

- **If invoked by a user** presenting a setup task: immediately spawn the
  `analog-chip-design-agents:infrastructure-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `infrastructure-orchestrator` mid-flow**: do not spawn a new agent.
  Treat this file as read-only — return the requested stage rules or sign-off criteria.

## Purpose
Detect open-source and proprietary analog/RF EDA tools, generate installation scripts for
missing open-source tools, deploy output-filtering shell wrappers that emit compact JSON
instead of raw SPICE `.lis`/`.measure` and DRC/LVS logs, configure MCP server templates, and
validate the environment before any domain orchestrator begins work.

---

## Supported EDA Tools

### Open-Source
- **ngspice** (`ngspice`) — SPICE simulator; loads Verilog-A via OSDI
- **Xyce** (`Xyce`) — parallel SPICE; harmonic balance; large MC
- **gnucap** (`gnucap`) — general circuit analysis
- **Qucs-S** (`qucs-s`) — schematic + simulation front-end (RF capable)
- **xschem** (`xschem`) — analog schematic capture and netlisting
- **Magic** (`magic`) — layout editor, DRC, and extraction
- **Netgen** (`netgen`) — LVS
- **KLayout** (`klayout`) — layout viewer, DRC/LVS, GDS/OASIS
- **OpenVAF** (`openvaf`) — Verilog-A → OSDI compiler
- **ADMS** (`admsXml`) — legacy Verilog-A → C model compiler
- **openEMS** (`openEMS`) — FDTD electromagnetic solver
- **FastHenry** (`fasthenry`) / **FastCap** (`fastcap`) — inductance/capacitance field solvers
- **gmsh** (`gmsh`) — mesh generation for EM
- **scikit-rf** (Python package `skrf`) — S-parameter / network analysis
- **PySpice** (Python package `PySpice`) — scripted SPICE corner/Monte-Carlo control
- **cocotb** (Python package `cocotb`) — analog↔digital co-simulation control
- **Hdl21** (Python package `hdl21`) — programmatic analog hardware description
- **gdstk** (Python package `gdstk`) / **gdsfactory** — layout generation
- **Verilator** (`verilator`) / **Icarus Verilog** (`iverilog`) — digital + RNM co-sim
- **GTKWave** (`gtkwave`) — waveform viewer
- **open_pdks** — sky130 / gf180mcu / ihp-sg13g2 PDK installer
- **uv** (`uv`) — fast Python package/project manager (required for PySpice/cocotb installs)

### Proprietary (detect only — never install)
- **Cadence Virtuoso** (`virtuoso`) — schematic/layout/ADE
- **Cadence Spectre / Spectre X / APS** (`spectre`) — analog/RF simulation
- **Cadence Xcelium AMS / AMS Designer** (`xrun`) — Verilog-AMS / mixed-signal
- **Cadence Quantus QRC** (`quantus`) — parasitic extraction
- **Cadence Pegasus** (`pegasus`) — DRC/LVS
- **Cadence Liberate** (`liberate`) — characterization
- **Synopsys HSPICE** (`hspice`) / **PrimeSim** (`primesim`) / **FineSim** (`finesim`) — SPICE
- **Synopsys Custom Compiler** (`custom_compiler`) — schematic/layout
- **Synopsys StarRC** (`StarXtract`) — extraction
- **Synopsys IC Validator** (`icv`) — DRC/LVS
- **Siemens Calibre** (`calibre`) — DRC/LVS/PEX/PERC
- **Siemens Symphony / AFS** (`afs`) — AMS / Analog FastSPICE
- **Siemens Solido** (`solido`) — variation / ML characterization
- **Keysight ADS** (`ads`) — RF circuit + EM
- **Ansys HFSS** (`hfss`) — 3D EM
- **Sonnet** (`sonnet`) — planar EM

---

## MCP Architecture — Two Tiers

### Tier 1: Batch MCP servers (short, self-contained runs)
| MCP config | Tool | Typical duration |
|------------|------|-----------------|
| `mcp-ngspice.json` | ngspice single analysis | seconds–minutes |
| `mcp-xyce.json` | Xyce single analysis / HB | minutes |
| `mcp-magic.json` | Magic DRC / extract | minutes |
| `mcp-klayout.json` | KLayout DRC/LVS | minutes |
| `mcp-netgen.json` | Netgen LVS | seconds–minutes |
| `mcp-openvaf.json` | OpenVAF Verilog-A compile | seconds |
| `mcp-openems.json` | openEMS short solve | minutes (set TOOL_TIMEOUT_S) |

The adapter is `plugins/infrastructure/tools/mcp-adapter.py`.

### Tier 2: Interactive session MCP servers (stateful, query-based)
| MCP config | Tool | Exposed tools |
|------------|------|---------------|
| `mcp-ngspice-session.json` | ngspice interactive control | `load_netlist`, `run_analysis`, `measure`, `alter_param`, `run_corner`, `close` |

The adapter is `plugins/infrastructure/tools/mcp-session-adapter.py`.

### Full-flow / long EM solves — do NOT use MCP
Large Monte-Carlo sweeps and 3D EM solves run for tens of minutes to hours and write
structured output files. Launch via Bash and read the output files (`.mt*`, `.csv`,
Touchstone `.sNp`) directly.

### Execution Hierarchy (per domain agent)
1. **Tier 2 session MCP** — when iterating over an already-loaded netlist (corner/MC/ECO loops)
2. **Tier 1 batch MCP** — one-shot single-analysis invocations
3. **Wrapper script** — if MCP not configured; wrapper emits compact JSON
4. **Direct execution** — last resort; raw logs consume significant context

---

## Stage: tool_discovery

### Domain Rules
1. Run `which <command>` and `<command> --version` (or `-v`) for every open-source tool above.
2. **Python interpreter detection** — run once at the start, before checking any Python packages.
   - **Step A — module system probe**: if `$MODULESHOME` is set or `modulecmd` exists, run `module avail 2>&1`, match `python`/`python3`, load the latest, resolve `PYTHON_EXEC` with `which python3`, set `python_env.type = "module"` and record `python_env.module_name`. Keep the module loaded for the whole run.
   - **Step B — PATH fallback**: `which python3` → `PYTHON_EXEC`; FAIL if empty (required for all wrappers). Classify `system` (`/usr/bin/python3`) vs `custom`.
   - **Step C — finalize**: set `PYTHON_BIN_DIR = dirname(PYTHON_EXEC)`; record `python_env { exec, type, bin_dir, module_name }`; add a `python3` entry to the `tools` array.
3. **Python packages** (`PySpice`, `cocotb`, `skrf`, `hdl21`, `gdstk`, `uv`): for `custom`/`module` Python use `"$PYTHON_EXEC" -m pip show <pkg>`; for `system` use the PATH tool. Report MISSING if absent.
4. For proprietary tools: check PATH with `which <primary-executable>` only (see executable names above); never install; record `PROPRIETARY_ONLY` if found, `MISSING` otherwise.
5. Record each tool as `FOUND`, `MISSING`, or `PROPRIETARY_ONLY`; capture the exact version for each `FOUND`.
6. Write results to `tool-status.json` before advancing.

### QoR Metrics to Evaluate
- `tools_detected`: count of FOUND tools (target ≥ 8 for a functional open-source analog flow)
- `tools_missing`: count of MISSING open-source tools
- `proprietary_found`: count of PROPRIETARY_ONLY tools detected

### Output Required
- `tool-status.json` with `python_env` object and a `tools` array of `{ tool, command, status, version, path }`

---

## Stage: module_discovery

### Domain Rules
1. Detect classic TCL Environment Modules (`$MODULESHOME` set or `modulecmd` in PATH); else set `module_system: "none"`, WARN, write empty `module-status.json`, advance.
2. Run `module avail 2>&1`; match entries against the tool→module map (case-insensitive substring), e.g. `spectre`→`cadence/spectre`, `hspice`→`synopsys/hspice`, `calibre`→`mentor/calibre`, `virtuoso`→`cadence/virtuoso`, `ngspice`→`ngspice`, `magic`→`magic`, `xschem`→`xschem`, `klayout`→`klayout`, `xyce`→`xyce`.
3. For each `FOUND` tool with a module available: upgrade status to `FOUND_PREFER_MODULE`; for `MISSING` with a module: `MISSING_LOAD_MODULE`. Add `module_names`/`versions_available`.
4. Generate `load-modules.sh` (default to latest version; comment alternatives). Never auto-run it; print: "Review and source `load-modules.sh`, then re-run the flow".

### QoR Metrics to Evaluate
- `module_system_detected`: bool
- `tools_found_via_modules`: count of `FOUND_PREFER_MODULE` + `MISSING_LOAD_MODULE`

### Output Required
- `module-status.json`, updated `tool-status.json`, `load-modules.sh` (when modules found)

---

## Stage: tool_installation

### Domain Rules
1. **Never auto-run installs** — only generate per-tool `install-<toolname>.sh` in `install-missing-tools/`.
2. If `python3` is missing: FAIL immediately and escalate (required for all wrappers).
3. Generate a script for every `MISSING` tool; skip `FOUND`/`FOUND_PREFER_MODULE`/`MISSING_LOAD_MODULE`/`PROPRIETARY_ONLY`.
4. Python-package scripts (`PySpice`, `cocotb`, `skrf`, `hdl21`, `gdstk`, `uv`) read `python_env.exec` and use `"$PYTHON_EXEC" -m pip install <pkg>`; never bare `pip` for custom/module Python.
5. Always generate a TCL classic modulefile per tool (no extension) under `$EDA_MODULEFILES_ROOT/<tool>/<version>` with at least `PATH` and `LD_LIBRARY_PATH`.

### Package Name Mapping (open-source)
| Tool | apt | brew | source / notes |
|---|---|---|---|
| `ngspice` | `ngspice` | `ngspice` | — |
| `Xyce` | build-from-source | — | https://github.com/Xyce/Xyce |
| `xschem` | `xschem` | build-from-source | https://github.com/StefanSchippers/xschem |
| `magic` | `magic` | — | http://opencircuitdesign.com/magic |
| `netgen` | `netgen-lvs` | — | http://opencircuitdesign.com/netgen |
| `klayout` | `klayout` | `klayout` | — |
| `openvaf` | build-from-source | — | https://github.com/pascalkuthe/OpenVAF |
| `openEMS` | `openems` | — | https://github.com/thliebig/openEMS-Project |
| `PySpice`/`cocotb`/`skrf`/`hdl21`/`gdstk` | `<PYTHON_EXEC> -m pip install <pkg>` | same | Python packages |
| `uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `uv` | prefer standalone installer |

### Output Required
- One `install-<toolname>.sh` per MISSING tool in `install-missing-tools/`

---

## Stage: wrapper_deployment

### Domain Rules
1. Deploy the wrapper scripts to `plugins/infrastructure/tools/` and `chmod +x` each; on permission denied, FAIL and escalate with `sudo chmod +x`.
2. Every wrapper must emit JSON conforming to the schema below regardless of exit code, and must handle a missing tool gracefully (`status: "FAIL"`).
3. Never suppress the tool's original exit code.

### Wrapper JSON Output Schema
```json
{
  "tool": "<tool-name>",
  "exit_code": 0,
  "status": "PASS|FAIL|WARN",
  "summary": {},
  "errors": [],
  "warnings": [],
  "raw_log": "/tmp/<tool>-XXXXXX.log"
}
```
`summary` carries tool-specific metrics (e.g. ngspice: measured specs + convergence; magic/klayout: DRC/LVS counts; openvaf: compile status; openEMS: S-param/passivity).

### Output Required
- Executable wrapper scripts in `plugins/infrastructure/tools/`

---

## Stage: mcp_configuration

### Domain Rules
1. Emit MCP config snippets for the batch + session configs listed in the MCP Architecture section.
2. Batch configs use `"command": "python3"` with `mcp-adapter.py` (never point directly at the wrapper); session configs use `mcp-session-adapter.py --tool ngspice`.
3. Resolve absolute adapter/wrapper paths at runtime (`realpath`/`pwd`); never leave `/absolute/path/to/`.
4. Write snippet files to `plugins/infrastructure/mcp/`; do not modify `.claude/settings.json` automatically — instruct the user to paste the `mcpServers` block.

### Output Required
- Batch MCP configs in `plugins/infrastructure/mcp/` (`mcp-ngspice.json`, `mcp-xyce.json`, `mcp-magic.json`, `mcp-klayout.json`, `mcp-netgen.json`, `mcp-openvaf.json`, `mcp-openems.json`)
- Session MCP config (`mcp-ngspice-session.json`)
- Adapter scripts present in `plugins/infrastructure/tools/` (`mcp-adapter.py`, `mcp-session-adapter.py`)
- Printed snippets with resolved absolute paths

---

## Stage: environment_validation

### Domain Rules
1. **Python environment check first**: read `python_env`; if `type == module`, verify the module is still loaded; if `custom`/`system`, verify the path matches `python_env.exec` (WARN on mismatch).
2. Re-run tool checks using the same Python-aware detection as `tool_discovery`.
3. Verify wrapper scripts exist and are executable; verify MCP snippets + adapters are present.
4. FAIL if any critical-path tool (ngspice or Xyce, plus magic/klayout for layout flows) is still `MISSING`.
5. For `MISSING_LOAD_MODULE` critical tools: WARN and instruct to source `load-modules.sh`.
6. Print the final sign-off summary: tools detected, tools via modules, wrappers deployed, MCP servers configured.

### Sign-off Checklist
- [ ] `tool-status.json` written (includes `python_env`)
- [ ] `module-status.json` written (even if `"none"`)
- [ ] `install-<toolname>.sh` generated for all MISSING tools
- [ ] `load-modules.sh` generated if module-available tools found
- [ ] Wrappers deployed and executable
- [ ] `mcp-adapter.py` and `mcp-session-adapter.py` present
- [ ] MCP config snippets written with resolved absolute paths and printed
- [ ] No critical-path tools with status `MISSING`

### Output Required
- Printed environment validation report
- `tool-manifest.json` with the final confirmed state

---

## Memory

Infrastructure memory is **opt-in** (default off) and environment-keyed — see the
infrastructure orchestrator's Infrastructure Memory section and
[`memory/README.md`](../../../../memory/README.md). When enabled
(`design_state.pipeline_config.track_infrastructure == true` or `--track-memory`), upsert a
record into `memory/infrastructure/experiences.jsonl` after `environment_validation` with a
`key_metrics.tool_versions` map. Distillation into `memory/infrastructure/knowledge.md` is
handled by the `memory-keeper` skill.
