---
name: circuit-design
description: >
  Select a circuit topology, size and bias devices to meet block specs, capture the schematic, and pass pre-layout ERC and design review before layout. (Skeleton — full domain rules land in Phase 1.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Circuit (Schematic) Design

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.3.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 1**.

## Purpose
Select a circuit topology, size and bias devices to meet block specs, capture the schematic, and pass pre-layout ERC and design review before layout.

## Supported EDA Tools

### Open-Source
- xschem (schematic capture / netlisting)
- Qucs-S
- KLayout
- ngspice in the sizing loop
- BAG / BAG3 and Hdl21 generators
- gm/Id toolkits

### Proprietary (detect-only — never installed)
- Cadence Virtuoso Schematic Editor
- Synopsys Custom Compiler
- Tanner S-Edit
- MunEDA WiCkeD / Siemens Solido (sizing, optimization, yield)

## Stage Sequence
`topology_selection → device_sizing → biasing → schematic_capture → pre_layout_erc → design_review`

## Domain Rules
_To be detailed in Phase 1._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- DC gain, GBW, phase margin, slew
- Offset, PSRR, CMRR
- Power
- Device matching / headroom
- gm/Id operating region

## Output Required
- Sized schematic
- Pre-layout netlist
- Operating-point / design-review report
