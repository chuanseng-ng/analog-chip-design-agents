---
name: rf-design
description: >
  Design RF/mmWave blocks (LNA, mixer, VCO, PLL, PA): topology and matching, S-parameter, harmonic-balance, Pnoise/PAC, IP3, and load-pull analyses. (Skeleton — full domain rules land in Phase 5.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: RF / mmWave Design

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.12.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 5**.

## Purpose
Design RF/mmWave blocks (LNA, mixer, VCO, PLL, PA): topology and matching, S-parameter, harmonic-balance, Pnoise/PAC, IP3, and load-pull analyses.

## Supported EDA Tools

### Open-Source
- Qucs-S (harmonic balance)
- Xyce HB
- ngspice (limited RF)
- scikit-rf (S-parameter math)
- openEMS for passives

### Proprietary (detect-only — never installed)
- Cadence Spectre RF
- Keysight ADS / GoldenGate
- Cadence AWR Microwave Office
- Synopsys HSPICE-RF
- AFS-RF

## Stage Sequence
`rf_spec → topology_matching → sparameter_analysis → harmonic_balance → noise_linearity → loadpull_optimization → rf_signoff`

## Domain Rules
_To be detailed in Phase 5._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- NF, gain (S21), return loss (S11/S22)
- IIP3 / P1dB
- Phase noise (VCO/PLL)
- PAE / Pout (PA)
- EVM
- Stability (K-factor)

## Output Required
- S-parameter / Touchstone results
- HB / Pnoise / IP3 reports
- RF spec compliance table
