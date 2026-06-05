---
name: pipeline-orchestration
description: >
  Cross-domain loop orchestration for the analog/mixed-signal + RF design pipeline.
  Provides the fix_request protocol, iteration-cap logic, the authoritative
  design_state.json constraints schema, failure classification, and approval
  checkpoints. Use when driving the closed-loop spec↔circuit↔layout feedback cycle.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Pipeline Orchestration

## Invocation

- **If invoked by a user** presenting a pipeline loop task: immediately spawn the
  `analog-chip-design-agents:pipeline-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked inside another orchestrator**: read `design_state.json`, summarise open
  `fix_requests[]`, and return — do not spawn subagents (anti-recursion rule).

## Purpose

This skill provides the closed-loop feedback protocol for analog design. When a spec
violation, non-convergence, or yield miss is found during simulation, post-layout
sign-off, or AMS verification, it must be communicated to the selected servicer (via the
fix_request `route_to` hint — `circuit-design` by default, or `behavioral-modeling`) in a
machine-actionable way, and the pipeline must iterate until the spec is met or the
iteration cap is reached.

The protocol has three participants:

| Participant | Role |
|---|---|
| **circuit-simulation-orchestrator** / **post-layout-signoff-orchestrator** / **ams-verification-orchestrator** | Detects the failure; writes a `fix_request` entry to `design_state.fix_requests[]` with `status=open`; terminates with `decision=escalate`. |
| **circuit-design-orchestrator** / **behavioral-modeling-orchestrator** | Reads the open `fix_request`; sets `status=claimed`; the circuit servicer re-sizes/re-tops the circuit, the modeling servicer re-authors/re-validates the behavioral model; sets `status=fixed` with `circuit_response`; terminates. The servicer is chosen by the entry's `route_to` hint (default `circuit-design`). |
| **pipeline-orchestrator** | Detects open entries; assigns a `pipeline_session_id`; dispatches the chosen servicer (circuit-design or behavioral-modeling) then re-validation in sequence; enforces a configurable cap (default 3, via `pipeline_config.max_cross_domain_iterations`); archives resolved entries on signoff; escalates via `pending_approval` if cap exceeded. |

## Domain Rules

### fix_request Schema (authoritative)

All entries in `design_state.fix_requests[]` must conform to this schema:

```json
{
  "id": "fr_<pipeline_session_id>_<YYYYMMDD>_<HHMMSS>_<seq>",
  "created_at": "<ISO-8601>",
  "updated_at": "<ISO-8601>",
  "created_by": "circuit-simulation-orchestrator | post-layout-signoff-orchestrator | ams-verification-orchestrator",
  "failure_class": "spec_violation | convergence | functional | yield",
  "retry_strategy": "refine",
  "route_to": "circuit-design | behavioral-modeling   (optional; omit for default circuit-design)",
  "analysis_name": "<analysis or testbench name, e.g. ac_stability, tran_settling>",
  "spec_or_metric": "<violated spec key, e.g. phase_margin_deg, nf_db, or null>",
  "corner": "<failing corner, e.g. ss_125C_vmin, or null>",
  "waveform_path": "<path or null>",
  "log_path": "<path or null>",
  "suspected_circuit": {
    "block": "<block/cell name>",
    "device": "<device or net, or null>",
    "netlist": "<netlist path or null>",
    "schematic_ref": "<schematic ref or null>"
  },
  "summary": "<one-line failure description>",
  "expected_behavior": "<spec excerpt or target value>",
  "observed_behavior": "<measured value / observed behaviour>",
  "session_id": "<pipeline_session_id or null>",
  "status": "open | claimed | fixed | abandoned",
  "circuit_response": null,
  "history": []
}
```

`route_to` is **optional** (default `circuit-design` when absent) — it names the servicer the
pipeline-orchestrator dispatches: `behavioral-modeling` for a model fault (RNM/cosim
divergence indicting the model) or `circuit-design` for a circuit fault. Producers set it; the
pipeline-orchestrator reads it. Omitting it preserves the legacy circuit-design routing.

`circuit_response` (populated by the servicer — circuit-design or behavioral-modeling — on close):
```json
{
  "fixed_at": "<ISO-8601>",
  "diff_summary": "<one-paragraph description of the circuit change>",
  "files_changed": ["sch/ldo_ota.sch", "netlist/ldo_ota.spice"],
  "commit_ref": null
}
```

`fix_request.history[]` — one entry per state transition:
```json
{
  "timestamp": "<ISO-8601>",
  "agent": "<agent name>",
  "from_status": "<previous status>",
  "to_status": "<new status>",
  "note": "<optional one-liner>"
}
```

### Ownership rules

- The chosen servicer (`circuit-design-orchestrator` or, when `route_to: behavioral-modeling`, `behavioral-modeling-orchestrator`) owns the `open→claimed` and `claimed→fixed|abandoned` transitions.
- Only the `pipeline-orchestrator` sets `cross_domain_iteration_count`, `pipeline_session_id`, `pipeline_config`, and moves resolved entries to `archive_fix_requests[]`.
- Domain orchestrators **may** set `pending_approval` exclusively with `type: "checkpoint"` at their own sign-off stage; `type: "escalation"` remains the sole responsibility of the `pipeline-orchestrator`.
- `approved_checkpoints[]` is written by the user (or by an orchestrator executing an explicit approval instruction) and read by all orchestrators.
- All agents may append to `fix_request.history[]` but must not overwrite each other's entries.

### Iteration cap

`cross_domain_iteration_count` tracks the total number of circuit↔simulation dispatch
cycles for the current pipeline session. The cap is `pipeline_config.max_cross_domain_iterations`
(default: 3 if absent). The orchestrator treats the cap as "reaches or exceeds"
(use `>= max_cross_domain_iterations`), writing a `pending_approval` entry and exiting as
soon as the count is equal to or greater than the cap:

```json
{
  "pending_approval": {
    "type": "escalation",
    "stage": null,
    "agent": "pipeline-orchestrator",
    "reason": "resource_limit: fix_request loop reached 3 cross-domain iterations — relax the spec, raise the cap, or accept current QoR",
    "fix_request_id": "<id>",
    "last_summary": "<last circuit_response.diff_summary>",
    "requires_user": true
  }
}
```

The user reviews the escalation, manually adjusts the circuit/spec, then clears
`pending_approval` (set to `null`) and resets `cross_domain_iteration_count` to 0 before
re-invoking the pipeline-orchestrator. Optionally raise `max_cross_domain_iterations`.

### Pipeline session fields

- **`pipeline_session_id`** (`"ps_<YYYYMMDD>_<HHMMSS>"` or `null`): identifies the active run. Set on entry, cleared on successful signoff. Scopes divergence checks and archival to the current session.
- **`pipeline_config`** (object): user-tunable settings, written with defaults on first run, never overwritten if present.
  - `max_cross_domain_iterations` (integer, default 3).
  - `checkpoints` (array of strings, default `[]`): stage names requiring human approval before sign-off. Example: `["arch_signoff", "schematic_signoff", "pex_signoff", "tapeout_signoff"]`.
  - `track_infrastructure` (bool, default false): opt-in infrastructure memory.
- **`approved_checkpoints[]`**: `{ "stage": "<name>", "approved_at": "<ISO-8601>", "approved_by": "user" }`.
- **`archive_fix_requests[]`**: resolved entries moved here on successful signoff.

### Constraints Schema (authoritative)

`design_state.constraints` is the single source of truth for design-intent parameters
across all domain orchestrators. Defined once here; domain SKILL.md files reference these
keys and document their default fallbacks. See also
[`docs/design_state_schema.md`](../../../../docs/design_state_schema.md).

```json
"constraints": {
  "supply": { "vdd_v": null, "vss_v": 0.0 },
  "specs": {
    "dc_gain_db": null,
    "gbw_hz": null,
    "phase_margin_deg": 60,
    "input_noise_nv_rthz": null,
    "psrr_db": null,
    "cmrr_db": null,
    "offset_mv_max": null,
    "power_mw": null,
    "settling_ns": null,
    "thd_db": null,
    "iip3_dbm": null
  },
  "rf_specs": {
    "nf_db": null,
    "gain_db": null,
    "s11_db_max": -10,
    "iip3_dbm": null,
    "p1db_dbm": null,
    "phase_noise_dbc_hz": null,
    "pae_pct": null,
    "evm_pct": null
  },
  "corners": {
    "process": ["tt"],
    "mismatch": true,
    "temp_c": [27],
    "voltage_pct": [0]
  },
  "yield": { "target_sigma": 3, "mc_samples": 1000 },
  "area_um2": null,
  "pdk": null
}
```

Non-null values are **documented defaults**. `null` values must be supplied by the user
for constraint-bearing domains.

#### Required vs. optional constraints

| Constraint key | Required by (hard-fail if missing/null) |
|---|---|
| `supply.vdd_v` | circuit-design, circuit-simulation, all downstream |
| at least one non-null entry in `specs` (or `rf_specs` for RF blocks) | circuit-design, circuit-simulation, rf-design |
| `corners.process` (≥ 1 entry) | circuit-simulation, post-layout-signoff |
| `pdk` | circuit-design, custom-layout, physical-verification, extraction |

All other keys are **optional** — absent keys fall back to the schema default with a WARN.

#### Stage-entry constraint validation rule

Every constraint-bearing domain orchestrator applies this rule at the **first stage** that
consumes design constraints. Skip entirely when invoked in fix-request-servicing mode (a
`fix_request.id` was passed in the prompt):

1. Read `design_state.constraints`. Treat missing key as `{}`.
2. For each key in this domain's **required** set: if missing or `null`, perform atomic
   RMW — set `pending_approval`:
   ```json
   {
     "type": "constraint_gap",
     "stage": "<entry stage name>",
     "agent": "<this-orchestrator>",
     "reason": "required constraint <key> missing from design_state.constraints",
     "fix_request_id": null,
     "last_summary": "<comma-separated list of missing keys>",
     "requires_user": true
   }
   ```
   Append a `history[]` entry: `decision: "escalate"`, `confidence: "high"`,
   `failure_class: "spec_gap"`, `retry_strategy: "escalate"`, `suggested_next_step: "escalate"`,
   `constraint_ref: "<missing key>"`. Print the gate message and **halt**.
3. For **optional** absent constraints: use the schema default, continue, and include a
   fallback note in the stage's history `reason` field.

#### Decision tagging via `constraint_ref`

In every `history[]` entry emitted after a stage that evaluates QoR against a constraint,
set `constraint_ref` to the primary constraint key compared in dot-path notation
(e.g. `"specs.phase_margin_deg"`, `"rf_specs.nf_db"`, `"yield.target_sigma"`). All other
history entries retain `constraint_ref: null`.

### Failure Classification & Retry Strategy

Every failure is categorised so recovery is determined programmatically. Two fields work
together on each `history[]` entry:

- `failure_class` — *what* went wrong.
- `retry_strategy` — *how* to recover, derived deterministically from `failure_class`.

`retry_strategy` ∈ `none | regenerate | refine | escalate`:

- **regenerate** — discard the faulty artifact and re-run the *generating* stage from a
  clean slate (tool crash, DRC/LVS, non-convergence needing a fresh testbench/options).
- **refine** — keep the artifact and re-run targeting a *specific* identified defect with
  detailed feedback (spec miss on a path, matching error, coverage hole). Usually carries
  a `fix_request`.
- **escalate** — halt and request human input (ambiguous spec, or a budget/cap hit).
- **none** — no failure (PASS or `await_approval`).

#### Mapping (authoritative — `failure_class` → default `retry_strategy`)

| `failure_class` | `retry_strategy` | rationale |
|---|---|---|
| `none` | `none` | no failure |
| `functional` | `refine` | re-run circuit design with the failing testbench |
| `spec_violation` | `refine` | re-size/re-top targeting the violated spec + corner |
| `matching` | `refine` | re-do device matching/layout targeting the mismatch |
| `yield` | `refine` | re-center design / widen margins targeting the MC tail |
| `convergence` | `regenerate` | re-run sim with a clean testbench / solver options |
| `drc_lvs` | `regenerate` | re-run layout/extraction from a clean state |
| `connectivity` | `refine` | re-run targeting the violated connection/connect rule |
| `reliability` | `refine` | re-run targeting the EM/IR/ESD violation |
| `tool_error` | `regenerate` | re-run the same stage from scratch |
| `spec_gap` | `escalate` | ambiguous/missing spec — needs user clarification |
| `resource_limit` | `escalate` | iteration cap / runtime exceeded — human decision |

Producers that emit a `fix_request` (simulation, post-layout, ams-verification) set its
`retry_strategy` to `refine` (their classes map to refine).

#### Actionable escalation guidance

Whenever `retry_strategy` resolves to `escalate` **or** a cap is hit, `pending_approval.reason`
must state both the `failure_class` and a plain-language description of what the user must
supply to unblock, e.g.:

- `spec_gap` → "spec_gap: clarify <ambiguous requirement> — provide the intended <value>."
- `resource_limit` → "resource_limit: loop cap (N) reached on <stage> — relax the spec, raise the cap, or accept current QoR."

### format_version

`design_state.json` for this marketplace uses a single working baseline:

- **`"1.0"`**: full schema — `constraints` (analog/RF), `fix_requests[]`,
  `cross_domain_iteration_count`, per-stage `history[]` (one entry per completed stage,
  each carrying `confidence`, `failure_class`, `retry_strategy`, `suggested_next_step`,
  `reason`, `constraint_ref`), `pipeline_config.checkpoints`, `approved_checkpoints[]`,
  and `pending_approval.type` (`checkpoint | escalation | constraint_gap`).

All orchestrators must set `format_version` to `"1.0"` if absent; never downgrade. Treat
missing `fix_requests`/`cross_domain_iteration_count` as `[]`/`0`; missing
`pipeline_config.checkpoints`/`approved_checkpoints` as `[]`; missing `pending_approval.type`
as `"escalation"`; missing `constraints` as `{}` (apply schema defaults; halt on first
missing required key).

### Approval Checkpoints

Proactive human-in-the-loop gates at configurable stage boundaries. Orthogonal to the
failure-driven `pending_approval` (type `escalation`).

#### Gate logic (applied by every domain orchestrator at its sign-off stage)

1. **Skip the gate in fix-request-servicing mode** (a `fix_request.id` was passed).
2. Read `pipeline_config.checkpoints`. If the orchestrator's sign-off stage name appears in
   the list **and** not in `approved_checkpoints[].stage`: atomic RMW — set `pending_approval`
   with `type: "checkpoint"`, append a `history[]` entry with `decision: "await_approval"`,
   `failure_class: "none"`, `retry_strategy: "none"`, `suggested_next_step: "escalate"`; do
   **not** set `signoff=true`; print the gate message and halt.
3. On re-invocation: if the stage now appears in `approved_checkpoints[]`, clear
   `pending_approval` (set null) and proceed to set `signoff=true`.

### Programmatic branching on standardized history[] fields

After a domain orchestrator completes, the pipeline-orchestrator reads the terminal
`history[]` entry to decide retry/escalate without string-parsing prose. Decision table
(evaluated in order):

| `confidence` | `failure_class` | `suggested_next_step` | Pipeline action |
|---|---|---|---|
| any | `resource_limit` | any | Escalate via `pending_approval` — cap exceeded |
| `low` | any | any | Escalate — result unreliable |
| any | `tool_error` \| `convergence` | `retry_stage` | Re-dispatch the same orchestrator once; if still failing, escalate |
| any | `drc_lvs` | `loop_back_to:<stage>` | Re-dispatch the layout/extraction orchestrator from a clean slate |
| any | `spec_violation` \| `functional` \| `yield` | `escalate` | Append a new `fix_request` and loop back via circuit-design |
| any | `matching` \| `connectivity` \| `reliability` | `loop_back_to:<stage>` | Re-dispatch targeting the violation with QoR feedback |
| any | `spec_gap` | `escalate` | Escalate — ambiguous spec |
| `high` \| `medium` | `none` | `proceed` | Advance to next stage / signoff |
| any | any | `abandon` | Escalate — child reports unrecoverable |

Programmatic branches must read structured fields — do not re-derive intent from `reason`.

### Dispatch pattern (pipeline-orchestrator)

Sequential dispatch — never parallel:
1. **Servicer** (fix the fault) — block until complete. Choose by the entry's `route_to` hint:
   `behavioral-modeling` → the modeling orchestrator; otherwise (default) circuit-design.
2. **Re-validation** — circuit-simulation (or post-layout / ams-verification) orchestrator
   validates the fix — block until complete. A model fix routed from ams-verification is
   re-validated by ams-verification.

Spawn form:
- Circuit: `subagent_type: analog-design-circuit:circuit-design-orchestrator`
- Modeling: `subagent_type: analog-design-modeling:behavioral-modeling-orchestrator`
- Simulation: `subagent_type: analog-design-simulation:circuit-simulation-orchestrator`
- AMS re-validation: `subagent_type: analog-design-ams-verification:ams-verification-orchestrator`

Always pass the `fix_request.id` in the subagent prompt.

## QoR Metrics

- `cross_domain_iteration_count` — circuit↔simulation dispatch cycles (target: ≤ 2 for clean designs)
- `time_to_signoff` — wall-clock from first open `fix_request` to sign-off
- `escalation_rate` — fraction of sessions that hit the cap (target: < 10%)
- `fix_request_abandonment_rate` — fraction of `fix_requests` reaching `status=abandoned` (target: 0%)

## Output Required

- `design_state.json` with all `fix_requests[]` at terminal status (`fixed` or `abandoned`)
- `design_state.json` with `cross_domain_iteration_count` updated
- `memory/meta/experiences.jsonl` entry for this run
- A console summary: which fix_requests were processed, how many iterations, and the outcome (converged / escalated / no open requests)
