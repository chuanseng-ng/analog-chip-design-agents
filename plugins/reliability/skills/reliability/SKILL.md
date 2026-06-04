---
name: reliability
description: >
  Run electromigration, IR-drop, ESD, latch-up, and aging (HCI/NBTI) analyses and sign off long-term reliability of the analog block. (Skeleton — full domain rules land in Phase 4.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Reliability

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.10.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 4**.

## Purpose
Run electromigration, IR-drop, ESD, latch-up, and aging (HCI/NBTI) analyses and sign off long-term reliability of the analog block.

## Supported EDA Tools

### Open-Source
- ngspice EM/IR estimation harnesses
- KLayout density / current-density scripts

### Proprietary (detect-only — never installed)
- Cadence Voltus / Legato Reliability
- Ansys RedHawk / Totem & PathFinder (ESD)
- Siemens Calibre PERC
- Magwel

## Stage Sequence
`em_analysis → ir_drop → esd_check → latchup_check → aging_analysis → reliability_signoff`

## Domain Rules
_To be detailed in Phase 4._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- EM current-density margin
- IR-drop %
- ESD / latch-up rule pass
- HCI / NBTI / aging degradation over lifetime

## Output Required
- EM / IR-drop report
- ESD / latch-up report
- Aging / reliability sign-off
