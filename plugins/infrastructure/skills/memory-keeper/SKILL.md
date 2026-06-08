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
relevant `<domain>/knowledge.md` under the resolved memory root — it does **not** spawn an
orchestrator. Pass `--init` (runs `memory_root.py --init`) to resolve and seed the central
memory root and migrate any repo-local runtime data, without distilling.

## Memory Root Resolution

Memory does **not** live at a fixed relative `memory/` path. The active root is resolved by
`memory_root.py` (the single source of truth that `distill.py` and `tools/qor_trends.py` import),
in this priority order:

1. an explicit `--memory-root PATH` argument
2. the `$CHIP_DESIGN_MEMORY_ROOT` environment variable
3. the central default `${XDG_DATA_HOME:-$HOME/.local/share}/chip-design-agents/analog/memory`
   (Windows: `%LOCALAPPDATA%\chip-design-agents\analog\memory`)
4. the in-repo `memory/` tree as a seed fallback (used only if the central root is unwritable)

The in-repo `memory/` tree is the version-controlled **seed**: on first resolution each
`<domain>/knowledge.md` is copied into the central root if absent (never overwriting accumulated
data; runtime `experiences.jsonl`/`run_state.md` are never seeded). Orchestrators resolve this same
root at session start and use it as `<MEM>` for every read/write. Print it with
`python3 plugins/infrastructure/skills/memory-keeper/memory_root.py` (add `--init` to seed +
migrate + report). Per-project scoping: `export CHIP_DESIGN_MEMORY_ROOT="$PWD/memory"`.

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
