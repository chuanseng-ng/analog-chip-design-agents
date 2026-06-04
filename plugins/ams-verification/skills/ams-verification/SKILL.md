---
name: ams-verification
description: >
  Build mixed-signal testbenches, define connect rules, run analog-digital co-simulation and real-number-model regressions, and close functional coverage. (Skeleton — full domain rules land in Phase 2.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: AMS Verification

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.5.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 2**.

## Purpose
Build mixed-signal testbenches, define connect rules, run analog-digital co-simulation and real-number-model regressions, and close functional coverage.

## Supported EDA Tools

### Open-Source
- cocotb + ngspice / Xyce co-sim
- Verilator / Icarus (digital + RNM)
- Xyce mixed-signal

### Proprietary (detect-only — never installed)
- Cadence Xcelium AMS / AMS Designer
- Spectre AMS
- Synopsys VCS-AMS / CustomSim
- Siemens Symphony + QuestaSim
- AFS-driven co-sim

## Stage Sequence
`ams_testbench → connect_module_setup → analog_digital_cosim → rnm_regression → coverage_closure → ams_signoff`

## Domain Rules
_To be detailed in Phase 2._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- Functional coverage
- RNM-vs-SPICE agreement
- Connect-module correctness
- Regression pass-rate
- Assertion failures

## Output Required
- AMS testbench + connect modules
- Regression / coverage report
- Co-sim waveforms
