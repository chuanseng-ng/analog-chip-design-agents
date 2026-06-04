---
name: memory-keeper
description: >
  Distil append-only experiences.jsonl run records into per-domain knowledge.md
  summaries for the analog design agents. (Skeleton — Phase 1.)
version: 0.1.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Memory Keeper

> **Status: skeleton (Phase 0).** The distillation logic and `distill.py` are
> implemented in **Phase 1** alongside the memory system. See
> [`PLAN.md`](../../../../PLAN.md) §9.

## Purpose
Read the Tier-1 `memory/<domain>/experiences.jsonl` run records, identify new
issue/fix patterns and tool flags not already captured, and update the Tier-2
`memory/<domain>/knowledge.md` summaries without discarding still-valid content.

## Domain Rules
_To be detailed in Phase 1._ Distillation threshold, per-domain metric fields,
and merge rules mirror the reference repo's memory-keeper.

## QoR Metrics
- New patterns distilled per run
- knowledge.md sections updated without loss of valid content

## Output Required
- Updated `memory/<domain>/knowledge.md`
