# Memory System

Every domain orchestrator reads from and writes to a **two-tier, file-based memory store**
under [`memory/`](../memory). No external database or service is required — memory is plain
files committed alongside the repo, so learnings persist across sessions and machines.

This page is the reader's overview. For the exact record schema, per-domain `key_metrics`
fields, and the atomic-write protocol, see [`memory/README.md`](../memory/README.md).

---

## Two Tiers

| Tier | File | Format | Role |
|------|------|--------|------|
| **Tier 1 — Experience log** | `memory/<domain>/experiences.jsonl` | JSONL, one record per run | Machine-parseable run history. Upserted (overwritten by `run_id`) as each stage completes; grows over time; never hand-edited. |
| **Tier 2 — Distilled knowledge** | `memory/<domain>/knowledge.md` | Markdown | Human- and agent-readable summary of failure patterns, successful tool flags, and PDK/device quirks. Seeded per domain and read by every orchestrator at session start. |

Tier 1 is the **append-only evidence**; Tier 2 is the **curated wisdom** distilled from it.
The two are linked by the `memory-keeper` skill, which periodically folds new patterns from
the JSONL log into `knowledge.md`.

A third helper file, `memory/<domain>/run_state.md`, records the active run's identity
(`run_id`, `design_name`, `pdk`, `tool`, `start_time`, `last_stage`) so an interrupted run
can be resumed.

---

## How an Orchestrator Uses Memory

Each of the 16 orchestrators follows the same protocol (see the `## Memory` section in any
`plugins/<domain>/agents/<domain>-orchestrator.md`):

1. **Session start — read.** Load `memory/<domain>/knowledge.md` (Tier 2) for known pitfalls
   and tool flags, then `run_state.md` to resume an interrupted run if present. The shared
   `design_state.json` is read immediately after.
2. **First action — write run state.** Create/update `memory/<domain>/run_state.md` with the
   new `run_id` and metadata; refresh `last_stage` after each stage.
3. **Per stage — upsert experience.** Write one JSON line to
   `memory/<domain>/experiences.jsonl` keyed by `run_id`, with the metrics available so far
   and `signoff_achieved: false`. On final sign-off, set `signoff_achieved: true`. The same
   `run_id` line is overwritten, never duplicated.

```
                read knowledge.md ──► run flow ──► upsert experiences.jsonl
                       ▲                                      │
                       │            memory-keeper skill       │
                       └──────────── distils Tier 1 ◄─────────┘
```

---

## Domains

The store covers all 16 domains (14 design domains plus `infrastructure` and `meta`), each
with its own subdirectory and seeded `knowledge.md`:

`architecture` · `modeling` · `circuit` · `sim` · `ams-verification` · `layout` ·
`physical-verification` · `extraction` · `post-layout` · `reliability` ·
`characterization` · `rf` · `em` · `ams-integration` · `infrastructure` · `meta`

Each domain records domain-appropriate `key_metrics` — e.g. `circuit` tracks `dc_gain_db`,
`phase_margin_deg`, `gbw_hz`, `power_mw`, `erc_errors`; `rf` tracks `nf_db`, `gain_db`,
`iip3_dbm`, `phase_noise_dbc_hz`. The authoritative field list per domain lives in
[`plugins/infrastructure/skills/memory-keeper/distill.py`](../plugins/infrastructure/skills/memory-keeper/distill.py)
(`METRIC_FIELDS`).

### Infrastructure memory is opt-in

The `infrastructure` domain only writes an `experiences.jsonl` record when
`design_state.pipeline_config.track_infrastructure` is `true` (or the orchestrator is invoked
with `--track-memory`). Default is off because tool versions and quirks are environment-
specific. When enabled, records are **environment-keyed** with a `host`/`os`/`arch`
fingerprint and a `tool_versions` map.

---

## Distilling Knowledge (Tier 1 → Tier 2)

As runs accumulate, fold new issue/fix patterns and tool flags back into `knowledge.md` with
the `memory-keeper` skill:

```text
/analog-design-infrastructure:memory-keeper --domain circuit
/analog-design-infrastructure:memory-keeper --all --min-records 10
```

The skill runs
[`distill.py`](../plugins/infrastructure/skills/memory-keeper/distill.py), which reads the
JSONL records, computes metric ranges (min/median/max/latest), surfaces candidate issue/fix
pairs and tool flags, and **merges** them into `knowledge.md` without discarding still-valid
content. It skips domains below the `--min-records` threshold (default 5). `experiences.jsonl`
is never modified — it remains the source of truth.

---

## QoR Trends

Track how key metrics evolve across runs for a named design with
[`tools/qor_trends.py`](../tools/qor_trends.py). It reads the Tier-1 records, tabulates or
plots metric history, and flags regressions when a metric moves the wrong way between runs
(e.g. phase margin drops, DRC violations climb). See
[`docs/installation.md`](installation.md) for usage.

---

## Shared Design State

Separate from per-domain memory, `design_state.json` in the working directory is the
**cross-orchestrator** shared file. Every orchestrator reads it at session start (after
`knowledge.md`) and performs an atomic read-modify-write at session end, carrying
`constraints`, `fix_requests[]`, `history[]`, `pipeline_config`, and checkpoint state across
all domain boundaries. Its schema is documented in
[`docs/design_state_schema.md`](design_state_schema.md).

---

## See Also

- [`memory/README.md`](../memory/README.md) — full experience-record schema, per-domain
  `key_metrics` table, directory layout, and atomic-write protocol
- [`plugins/infrastructure/skills/memory-keeper/SKILL.md`](../plugins/infrastructure/skills/memory-keeper/SKILL.md)
  — distillation skill specification
- [`docs/design_state_schema.md`](design_state_schema.md) — shared cross-orchestrator state
