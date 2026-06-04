---
name: characterization
description: >
  Characterize timing, power, and noise of analog/mixed macros across corners and generate Liberty (.lib) and behavioral models for downstream integration. (Skeleton — full domain rules land in Phase 4.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Characterization

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.11.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 4**.

## Purpose
Characterize timing, power, and noise of analog/mixed macros across corners and generate Liberty (.lib) and behavioral models for downstream integration.

## Supported EDA Tools

### Open-Source
- Custom ngspice / Xyce sweep harnesses
- Python .lib writers

### Proprietary (detect-only — never installed)
- Cadence Liberate
- Synopsys SiliconSmart
- Siemens Solido ML Characterization
- Altos (legacy)

## Stage Sequence
`char_setup → timing_char → power_char → noise_char → liberty_generation → model_validation → char_signoff`

## Domain Rules
_To be detailed in Phase 4._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- .lib completeness
- Characterization accuracy vs SPICE
- Corner / voltage / temperature coverage
- Model monotonicity

## Output Required
- Liberty (.lib) files
- Behavioral / characterization models
- Characterization validation report
