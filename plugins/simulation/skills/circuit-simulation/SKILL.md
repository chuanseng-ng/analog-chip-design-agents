---
name: circuit-simulation
description: >
  Run the full SPICE analysis suite — DC, AC, transient, noise, stability — across PVT corners with Monte-Carlo, and sign off the design's electrical specifications. (Skeleton — full domain rules land in Phase 1.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Circuit Simulation

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.4.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 1**.

## Purpose
Run the full SPICE analysis suite — DC, AC, transient, noise, stability — across PVT corners with Monte-Carlo, and sign off the design's electrical specifications.

## Supported EDA Tools

### Open-Source
- ngspice
- Xyce (parallel SPICE)
- gnucap
- Qucs-S
- PySpice (control / Monte-Carlo)

### Proprietary (detect-only — never installed)
- Cadence Spectre / Spectre X / APS
- Synopsys HSPICE / PrimeSim (HSPICE/XA/Pro) / FineSim
- Siemens AFS (Analog FastSPICE) / Eldo
- Silvaco SmartSpice
- Empyrean ALPS / NanoSpice

## Stage Sequence
`testbench_setup → dc_op → ac_analysis → transient → noise_analysis → corner_analysis → monte_carlo → sim_signoff`

## Domain Rules
_To be detailed in Phase 1._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- All electrical specs vs target across PVT corners
- Monte-Carlo yield (sigma / Cpk)
- Convergence
- Simulation runtime

## Output Required
- Per-analysis result reports
- Corner / Monte-Carlo summary
- Spec compliance table
