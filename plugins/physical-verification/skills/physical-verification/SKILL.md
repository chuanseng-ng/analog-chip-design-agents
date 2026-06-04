---
name: physical-verification
description: >
  Run DRC, LVS, antenna/ERC, and density/DFM checks against the foundry decks and sign off physical correctness of the layout. (Skeleton — full domain rules land in Phase 3.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Physical Verification

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.7.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 3**.

## Purpose
Run DRC, LVS, antenna/ERC, and density/DFM checks against the foundry decks and sign off physical correctness of the layout.

## Supported EDA Tools

### Open-Source
- Magic (DRC / extract) + Netgen (LVS)
- KLayout DRC / LVS decks

### Proprietary (detect-only — never installed)
- Siemens Calibre nmDRC / nmLVS
- Synopsys IC Validator (ICV)
- Cadence Pegasus / Assura
- Silvaco Guardian

## Stage Sequence
`drc → lvs → antenna_erc → density_dfm → pv_signoff`

## Domain Rules
_To be detailed in Phase 3._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- DRC violations = 0
- LVS clean (devices + nets matched)
- Antenna = 0
- Density within window
- ERC clean

## Output Required
- DRC report
- LVS report
- Antenna / density report
