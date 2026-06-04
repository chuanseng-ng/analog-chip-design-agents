---
name: infrastructure
description: >
  Detect open-source and proprietary analog/RF EDA tools, deploy output-filtering JSON wrappers, configure MCP servers, and validate the environment before any domain flow runs. Also hosts the memory-keeper distillation skill. (Skeleton — full domain rules land in Phase 1.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Infrastructure Setup

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §6.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 1**.

## Purpose
Detect open-source and proprietary analog/RF EDA tools, deploy output-filtering JSON wrappers, configure MCP servers, and validate the environment before any domain flow runs. Also hosts the memory-keeper distillation skill.

## Supported EDA Tools

### Open-Source
- ngspice, Xyce, gnucap, Qucs-S
- xschem, Magic, Netgen, KLayout
- OpenVAF, ADMS
- openEMS, FastHenry, FastCap, gmsh
- scikit-rf, PySpice, cocotb, Hdl21
- gdstk / gdsfactory, ALIGN, MAGICAL, BAG3
- open_pdks (sky130 / gf180mcu / ihp-sg13g2)
- uv (Python env)

### Proprietary (detect-only — never installed)
- Cadence Virtuoso / Spectre / Spectre RF / Xcelium AMS / Quantus / Pegasus / Voltus / Liberate / EMX (detect-only)
- Synopsys Custom Compiler / HSPICE / PrimeSim / StarRC / IC Validator / SiliconSmart (detect-only)
- Siemens Calibre / Symphony / AFS / Solido (detect-only)
- Keysight ADS / Ansys HFSS / Sonnet / Silvaco / Empyrean (detect-only)

## Stage Sequence
`tool_discovery → module_discovery → tool_installation → wrapper_deployment → mcp_configuration → environment_validation`

## Domain Rules
_To be detailed in Phase 1._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- tools_detected (open-source FOUND count)
- tools_missing
- proprietary_found (detect-only)
- wrappers_deployed
- mcp_servers_configured

## Output Required
- tool-status.json / module-status.json
- JSON wrapper scripts
- MCP config snippets
