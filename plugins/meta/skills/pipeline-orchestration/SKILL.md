---
name: pipeline-orchestration
description: >
  Drive the cross-domain analog pipeline: own design_state.json, route fix_requests through the spec-circuit-layout feedback loop, enforce an iteration cap with user escalation, and manage human-approval checkpoints up to tape-out. (Skeleton — full domain rules land in Phase 1.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Pipeline Orchestration

> **Status: skeleton (Phase 0).** The stage sequence, tool lists, and QoR metrics
> below are the planned scope from [`PLAN.md`](../../../../PLAN.md) §7.
> Detailed per-stage Domain Rules, Common Issues & Fixes, memory wiring, and
> `design_state.json` integration are implemented in **Phase 1**.

## Purpose
Drive the cross-domain analog pipeline: own design_state.json, route fix_requests through the spec-circuit-layout feedback loop, enforce an iteration cap with user escalation, and manage human-approval checkpoints up to tape-out.

## Supported EDA Tools

### Open-Source
- (orchestration only — invokes domain orchestrators and the infrastructure tooling)

### Proprietary (detect-only — never installed)
- (orchestration only)

## Stage Sequence
`intake → domain_dispatch → fix_request_routing → checkpoint_gate → pipeline_signoff`

## Domain Rules
_To be detailed in Phase 1._ Each stage above gets numbered, specific
rules, with thresholds sourced from `design_state.constraints` (see
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md)).

## QoR Metrics
- Cross-domain iteration count vs cap
- Open vs resolved fix_requests
- Checkpoints approved
- Terminal pipeline status

## Output Required
- Updated design_state.json (with history[] trace)
- Pipeline status summary
- Escalation report when blocked
