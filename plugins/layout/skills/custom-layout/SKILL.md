---
name: custom-layout
description: >
  Floorplan, generate matched devices, and place/route analog blocks with symmetry, shielding, and matching constraints to a clean, DRC-ready layout. (Skeleton — full domain rules land in Phase 3.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Custom Layout

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.6.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 3**.

## Purpose
Floorplan, generate matched devices, and place/route analog blocks with symmetry, shielding, and matching constraints to a clean, DRC-ready layout.

## Supported EDA Tools

### Open-Source
- Magic
- KLayout
- gdsfactory / gdstk
- ALIGN and MAGICAL (analog layout automation)
- BAG layout generators

### Proprietary (detect-only — never installed)
- Cadence Virtuoso Layout (XL/GXL/EAD)
- Synopsys Custom Compiler Layout
- Tanner L-Edit
- Silvaco Expert

## Stage Sequence
`layout_floorplan → device_generation → analog_placement → analog_routing → layout_finishing → layout_check`

## Domain Rules
_To be detailed in Phase 3._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- Matching quality (common-centroid / interdigitation)
- Symmetry
- Density
- Area
- Shielding of sensitive nets
- Antenna readiness

## Output Required
- GDS / layout database
- Device-matching report
- Pre-DRC summary
