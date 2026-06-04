---
name: memory-keeper
description: >
  Distil append-only experiences.jsonl run records into per-domain knowledge.md summaries
  for the analog design agents. Use after enough runs accumulate to merge new convergence
  fixes, sizing recipes, PDK quirks, and tool flags into the Tier-2 knowledge file.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Memory Keeper

## Invocation

Invoke as `/analog-design-infrastructure:memory-keeper --domain <domain>` (or `--all`).
This skill runs the distillation helper, reviews the candidate patterns, and updates the
relevant `memory/<domain>/knowledge.md` — it does **not** spawn an orchestrator.

## Purpose

Read the Tier-1 `memory/<domain>/experiences.jsonl` run records, identify new issue/fix
patterns and tool flags not already captured, and update the Tier-2
`memory/<domain>/knowledge.md` summaries without discarding still-valid content. This keeps
the knowledge each orchestrator reads at session start current as experience accumulates.

## Domain Rules

1. Run the helper: `python3 distill.py <domain> [--min-records N] [--memory-root PATH]`.
   It emits a JSON summary (issue/fix pairs, tool-flag candidates, metric ranges, signoff
   rate) and exits with code 2 (skip) when fewer than `--min-records` records exist
   (default threshold: 5).
2. Supported domains are listed in `distill.py` `VALID_DOMAINS` (the 14 design domains plus
   `infrastructure` and `meta`). Each has a numeric `key_metrics` field set in `METRIC_FIELDS`.
3. Merge — do not overwrite: add new issue/fix patterns and tool flags to the matching
   section of `knowledge.md`; preserve still-valid existing content. De-duplicate near-identical entries.
4. Record metric ranges (min/median/max/latest) for the domain's numeric metrics so the
   orchestrator has a baseline for regression awareness.
5. Never edit `experiences.jsonl` — it is the append-only source of truth.

## QoR Metrics
- New issue/fix patterns distilled per run
- `knowledge.md` sections updated without loss of still-valid content
- Metric-range baselines refreshed for the domain

## Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Fewer than `--min-records` records | Skip (exit 2); re-run after more runs accumulate |
| Malformed JSONL line | Helper warns and skips the line; fix the producer if recurring |

## Output Required
- Updated `memory/<domain>/knowledge.md` (merged, not overwritten)
- Console summary of what was added
