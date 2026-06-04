---
name: ams-integration
description: >
  Qualify analog IP, assemble the mixed-signal top, define boundary/connect rules, run chip-level AMS simulation, and check power intent through integration sign-off. (Skeleton — full domain rules land in Phase 6.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Mixed-Signal Top Integration

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.14.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 6**.

## Purpose
Qualify analog IP, assemble the mixed-signal top, define boundary/connect rules, run chip-level AMS simulation, and check power intent through integration sign-off.

## Supported EDA Tools

### Open-Source
- cocotb co-sim
- KLayout / Magic + Netgen top-level LVS

### Proprietary (detect-only — never installed)
- Cadence Virtuoso (top assembly)
- Xcelium AMS / Spectre AMS
- Synopsys VCS-AMS
- Siemens Symphony
- UPF flows (Synopsys / Cadence)

## Stage Sequence
`ip_qualification → top_assembly → boundary_connect_rules → chip_level_ams_sim → power_intent_check → integration_signoff`

## Domain Rules
_To be detailed in Phase 6._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- Connectivity (top-level LVS)
- AMS top-sim pass
- Power-intent (UPF) consistency
- IO / ESD ring completeness
- Analog-island isolation

## Output Required
- Assembled mixed-signal top
- Chip-level AMS sim report
- Power-intent / connectivity report
