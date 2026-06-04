---
name: parasitic-extraction
description: >
  Run RC and coupling extraction on the verified layout and build a back-annotated post-layout netlist for sign-off simulation. (Skeleton — full domain rules land in Phase 3.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Parasitic Extraction

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.8.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 3**.

## Purpose
Run RC and coupling extraction on the verified layout and build a back-annotated post-layout netlist for sign-off simulation.

## Supported EDA Tools

### Open-Source
- Magic ext / ext2spice
- KLayout PEX (R + limited C)
- FastCap / FastHenry (field solvers)

### Proprietary (detect-only — never installed)
- Synopsys StarRC
- Cadence Quantus QRC
- Siemens Calibre xRC / xACT
- Silvaco Clever

## Stage Sequence
`extraction_setup → rc_extraction → coupling_extraction → netlist_back_annotation → pex_signoff`

## Domain Rules
_To be detailed in Phase 3._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- Extraction coverage
- R/C accuracy vs golden
- Coupling completeness
- Netlist size / runtime

## Output Required
- Extracted (PEX) netlist
- Parasitic / coupling report
- Back-annotation map
