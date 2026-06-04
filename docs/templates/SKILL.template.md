---
name: <skill-folder-name>
description: >
  One-sentence description for Claude Code's skill discovery — what this skill
  enables and when Claude should load it.
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: <Domain Title>

## Invocation

- **If invoked by a user** presenting a <domain> task: immediately spawn the
  `analog-chip-design-agents:<domain>-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `<domain>-orchestrator` mid-flow**: do not spawn a new agent.
  Treat this file as read-only — return the requested stage rules, sign-off criteria,
  or loop-back guidance to the calling orchestrator.

## Pre-run Context

Before executing or advising on any stage, read if present:
1. `memory/<domain>/knowledge.md` — known failure patterns, tool flags, PDK quirks.
2. `memory/<domain>/run_state.md` — current run identity for resume-after-interruption.

## Purpose

One paragraph describing what this skill enables Claude to do across the flow.

## Supported EDA Tools

### Open-Source
- **<tool>** (`<command>`) — what it does, when to use it.

### Proprietary (detect-only — never installed)
- **<tool>** (`<command>`) — what it does.

## Stage: <stage_name>        <!-- repeat this block per stage -->

### Domain Rules
1. Specific, numbered rules. Reference `design_state.constraints.<path>` for thresholds.

### QoR Metrics to Evaluate
- Measurable pass/fail criteria with units; cite the constraint default in parentheses.

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| … | … |

### Output Required
- Files / artifacts this stage must produce.

## Memory

Describe the `run_state.md` and `experiences.jsonl` writes (keyed by `run_id`),
mirroring the reference repo's two-tier memory pattern. See
[`docs/design_state_schema.md`](../design_state_schema.md).
