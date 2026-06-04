# Pipeline Orchestration (meta) — Distilled Knowledge (Tier 2)

Seeded known loop patterns. Distilled by `/analog-design-infrastructure:memory-keeper --domain meta`.

## Known Loop Patterns & Handling

| Pattern | Handling |
|---------|----------|
| spec_violation fix_request from simulation | Dispatch circuit-design (refine), then re-validate the named `spec_or_metric` + `corner` only — not the whole suite |
| Same fix_request reopened 3× (cap hit) | Escalate via `pending_approval` (type escalation) with `resource_limit` guidance — likely a topology limit, not a sizing tweak |
| convergence failure_class | `regenerate` (retry sim with a clean testbench/options) once before escalating — do not route to circuit-design |
| yield miss | Route to circuit-design (centring/area), not to layout, in the pre-layout phase |
| Domain returns `confidence: low` | Escalate regardless of `suggested_next_step` — result is unreliable |

## Escalation Triggers

- `cross_domain_iteration_count >= max_cross_domain_iterations` → escalate (resource_limit).
- Any non-null `pending_approval` at intake → halt with the type-specific message.
- `spec_gap` from a constraint-gap → escalate; the user must populate `design_state.constraints`.

## Practice

- Always pass the `fix_request.id` to the dispatched child so it locates its work item.
- Dispatch is sequential (circuit-design → re-validation), never parallel.
- On clean signoff, archive resolved `fix_requests[]` and clear `pipeline_session_id`.

## Metric Baselines

_(Populated by `memory-keeper`: `cross_domain_iterations`, `fix_requests_processed`, `fix_requests_abandoned`.)_
