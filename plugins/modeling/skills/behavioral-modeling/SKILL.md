---
name: behavioral-modeling
description: >
  Author, compile, and validate analog behavioral models — Verilog-A, Verilog-AMS, VHDL-AMS, and SystemVerilog real-number models — plus the connect modules that bridge analog and digital domains. This is the analog-HDL core of the marketplace. (Skeleton — full domain rules land in Phase 2.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Behavioral / AMS Modeling

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.2.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 2**.

## Purpose
Author, compile, and validate analog behavioral models — Verilog-A, Verilog-AMS, VHDL-AMS, and SystemVerilog real-number models — plus the connect modules that bridge analog and digital domains. This is the analog-HDL core of the marketplace.

## Supported EDA Tools

### Open-Source
- OpenVAF (Verilog-A → OSDI for ngspice / Xyce)
- ADMS (legacy Verilog-A → C)
- SystemVerilog RNM (nettype/wreal) via Verilator / Icarus
- Hdl21 + VLSIR (Python analog HDL)
- GHDL-AMS (limited VHDL-AMS)

### Proprietary (detect-only — never installed)
- Cadence AMS Designer / Xcelium AMS
- Spectre Verilog-A
- Synopsys VCS-AMS / CustomSim
- Siemens Symphony / Symphony Pro

## Stage Sequence
`model_planning → va_authoring → model_compilation → connect_rule_setup → model_validation → model_signoff`

## Domain Rules
_To be detailed in Phase 2._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- Model-vs-SPICE error %
- Convergence robustness
- Simulation speed-up factor
- RNM toggle / branch coverage
- Connect-module completeness

## Output Required
- Verilog-A/AMS or RNM source
- Compiled OSDI / connect modules
- Model-vs-SPICE validation report
