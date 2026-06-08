# Agent Memory System

This directory is the **version-controlled seed** for persistent, file-based memory used by the
analog/mixed-signal + RF design orchestrators. Live memory does **not** live here at runtime — it
lives in a central, machine-level root so any working directory shares the same accumulated
knowledge. Agents read memory at session start, write a run-state file before the first stage, and
upsert an experience record after each stage completes — no external infrastructure required.

## Where Memory Lives (Resolution)

The active memory root is resolved by
[`plugins/infrastructure/skills/memory-keeper/memory_root.py`](../plugins/infrastructure/skills/memory-keeper/memory_root.py)
— the single source of truth that orchestrators, `distill.py`, and `tools/qor_trends.py` all use —
in this priority order:

1. an explicit `--memory-root PATH` / `--memory-dir PATH` argument (scripts)
2. the `$CHIP_DESIGN_MEMORY_ROOT` environment variable
3. the central default `${XDG_DATA_HOME:-$HOME/.local/share}/chip-design-agents/analog/memory`
   (Windows: `%LOCALAPPDATA%\chip-design-agents\analog\memory`)
4. this in-repo `memory/` tree as a seed fallback (only if the central root is unwritable)

On first resolution the central root is created and each `<domain>/knowledge.md` here is copied
in **if absent** (accumulated data is never overwritten; runtime `experiences.jsonl`/`run_state.md`
are never seeded). The analog and digital flavors use separate subdirs (`.../analog/` vs
`.../digital/`) so same-named domains never collide.

```bash
# Where does my data actually live?
python3 plugins/infrastructure/skills/memory-keeper/memory_root.py
# Seed the central root + migrate any repo-local runtime data, then report:
python3 plugins/infrastructure/skills/memory-keeper/memory_root.py --init
```

**Per-project scoping (opt-out of the central store):** `export CHIP_DESIGN_MEMORY_ROOT="$PWD/memory"`
or pass `--memory-root ./memory` to the scripts. Throughout this document, `<MEM>` denotes the
resolved root; orchestrators use the resolved absolute path, not the literal `memory/` directory.

## Two-Tier Design

### Tier 1 — `experiences.jsonl`
JSONL with per-stage upsert/overwrite by `run_id`. One record per orchestrator run, updated
as stages complete. Machine-parseable; grows over time; never edited manually.

### Tier 2 — `knowledge.md`
Human- and agent-readable distilled summary: known failure patterns, successful tool flags,
PDK/device quirks. Seeded here and periodically updated by the `memory-keeper` skill
(`/analog-design-infrastructure:memory-keeper --domain <domain>`) as records accumulate.

## Experience Record Schema

```json
{
  "run_id": "<domain>_<YYYYMMDD>_<HHMMSS>",
  "timestamp": "<ISO-8601>",
  "domain": "<domain>",
  "design_name": "<from state>",
  "pdk": "<from state if known, else null>",
  "tool_used": "<primary tool>",
  "stages_completed": ["<stage>", "..."],
  "loop_backs": {"<stage>": "<count>"},
  "key_metrics": { "<domain-specific fields — see distill.py METRIC_FIELDS>" },
  "issues_encountered": ["<description>", "..."],
  "fixes_applied": ["<description>", "..."],
  "signoff_achieved": true,
  "notes": "<free-text observations>"
}
```

## Domain key_metrics Fields (Phase 1 domains; full set in `distill.py`)

| Domain | key_metrics fields |
|--------|--------------------|
| circuit | `dc_gain_db`, `phase_margin_deg`, `gbw_hz`, `power_mw`, `erc_errors` |
| sim | `worst_pm_deg`, `worst_gain_db`, `mc_yield_sigma`, `failing_corners`, `convergence_failures` |
| infrastructure | `tools_detected`, `tools_missing`, `wrappers_deployed`, `mcp_servers_configured`, `module_system`, `tool_versions` |
| meta | `cross_domain_iterations`, `fix_requests_processed`, `fix_requests_abandoned` |

## Directory Layout

```
memory/
├── README.md                 ← this file
├── designs/                  ← per-design metric history (future use)
├── circuit/                  ← knowledge.md seeded; experiences.jsonl on first run
├── sim/
├── infrastructure/           ← opt-in, environment-keyed (see note)
└── meta/
```

Domains implemented in later phases (`architecture`, `modeling`, `ams-verification`,
`layout`, `physical-verification`, `extraction`, `post-layout`, `reliability`,
`characterization`, `rf`, `em`, `ams-integration`) get their `knowledge.md` when their phase
lands; the folder is created by the orchestrator on first run.

### Infrastructure memory (opt-in, environment-keyed)

The `infrastructure` domain is **opt-in**: the infrastructure-orchestrator writes an
`experiences.jsonl` record only when `design_state.pipeline_config.track_infrastructure` is
`true` (or it is invoked with `--track-memory`). Default off — infrastructure state is
environment-specific. When enabled, each record carries an `environment` fingerprint
(`host`, `os`, `os_version`, `arch`) and a `key_metrics.tool_versions` map; records are
environment-keyed.

## Design State

`design_state.json` is the cross-orchestrator shared file in the working directory. Every
orchestrator reads it at session start (after `knowledge.md`) and performs an atomic
read-modify-write at session end. Its authoritative schema (constraints, `fix_requests[]`,
`history[]`, `pipeline_config`, checkpoints, `format_version "1.0"`) is defined in
[`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../plugins/meta/skills/pipeline-orchestration/SKILL.md)
and summarised in [`docs/design_state_schema.md`](../docs/design_state_schema.md).

Atomic write protocol: read `design_state.json` (or `{}`) → modify → write a unique temp
file → rename to `design_state.json`. Apply the same care to `experiences.jsonl` upserts.

## How Orchestrators Use This

- **Session start**: read `<MEM>/<domain>/knowledge.md` and `run_state.md` before stage 1.
- **Before stage 1**: write `<MEM>/<domain>/run_state.md` with `run_id`, `design_name`, `pdk`, `tool`, `start_time`, `last_stage`.
- **Per stage**: upsert one JSON line in `experiences.jsonl` keyed by `run_id` (`signoff_achieved: false` until the final stage). Overwrite, do not append a second line for the same run.
