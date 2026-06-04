---
name: post-layout-signoff
description: >
  Run post-PEX corner and Monte-Carlo simulation on the extracted netlist, re-verify specs against the pre-layout design, and gate tape-out. (Skeleton — full domain rules land in Phase 3.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Post-Layout Sign-off

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.9.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 3**.

## Purpose
Run post-PEX corner and Monte-Carlo simulation on the extracted netlist, re-verify specs against the pre-layout design, and gate tape-out.

## Supported EDA Tools

### Open-Source
- ngspice / Xyce on the extracted netlist
- PySpice (corner / MC driving)

### Proprietary (detect-only — never installed)
- Cadence Spectre / APS
- Synopsys PrimeSim / FineSim
- Siemens AFS

## Stage Sequence
`pex_netlist_assembly → post_layout_corner_sim → spec_reverification → margin_analysis → tapeout_signoff`

## Domain Rules
_To be detailed in Phase 3._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- Post-layout spec margin vs pre-layout
- Degradation %
- Corner / MC pass at sign-off
- Parasitic-induced stability / CMRR loss

## Output Required
- Post-layout sign-off report
- Margin / degradation analysis
- Tape-out checklist
