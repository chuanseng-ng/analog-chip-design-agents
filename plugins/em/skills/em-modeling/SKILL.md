---
name: em-modeling
description: >
  Solve electromagnetics for inductors, transformers, transmission lines, and antennas, extract S-parameters, and fit lumped models for circuit-level RF simulation. (Skeleton — full domain rules land in Phase 5.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: EM Modeling

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §5.13.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 5**.

## Purpose
Solve electromagnetics for inductors, transformers, transmission lines, and antennas, extract S-parameters, and fit lumped models for circuit-level RF simulation.

## Supported EDA Tools

### Open-Source
- openEMS (FDTD)
- FastHenry / FastCap
- gmsh (meshing)
- scikit-rf (fitting)

### Proprietary (detect-only — never installed)
- Ansys HFSS / SIwave / RaptorX
- Keysight Momentum / RFPro / EMPro
- Cadence EMX & AWR AXIEM / Analyst
- Sonnet

## Stage Sequence
`em_setup → geometry_definition → meshing → em_solve → sparameter_extraction → model_fitting → em_signoff`

## Domain Rules
_To be detailed in Phase 5._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- S-parameter accuracy / passivity
- Q-factor
- Self-resonant frequency
- Lumped-model fit error
- Coupling

## Output Required
- Touchstone (.sNp) S-parameters
- Fitted lumped model
- EM convergence / passivity report
