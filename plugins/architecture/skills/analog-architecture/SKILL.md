---
name: analog-architecture
description: >
  Capture top-level analog/mixed-signal specs, budget noise/linearity/power across a signal chain, allocate per-block specifications, and assess feasibility before circuit design begins. (Skeleton — full domain rules land in Phase 2.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Analog Architecture

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.1.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 2**.

## Purpose
Capture top-level analog/mixed-signal specs, budget noise/linearity/power across a signal chain, allocate per-block specifications, and assess feasibility before circuit design begins.

## Supported EDA Tools

### Open-Source
- Python budgeting (NumPy / scikit-rf)
- ngspice / Xyce (behavioral sanity checks)
- Jupyter

### Proprietary (detect-only — never installed)
- Cadence ADE Assembler / Spectre
- Keysight SystemVue
- MATLAB / Simulink

## Stage Sequence
`spec_capture → signal_chain_budgeting → topology_partitioning → behavioral_feasibility → architecture_signoff`

## Domain Rules
_To be detailed in Phase 2._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- Noise budget (input-referred / SNR / NF allocation)
- Linearity budget (IP3 / THD)
- Power budget
- Area estimate
- Per-block spec allocation table

## Output Required
- Signal-chain budget table
- Per-block specification document
- Feasibility / risk assessment
