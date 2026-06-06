# Mixed-Signal Top Integration — Distilled Knowledge (Tier 2)

Seeded known patterns. The `memory-keeper` skill merges new entries from
`experiences.jsonl` as runs accumulate (`/analog-design-infrastructure:memory-keeper --domain ams-integration`).

## Known Failure Patterns & Fixes

| Pattern | Fix |
|---------|-----|
| Block integrated before upstream sign-off | Block qualification; route the block back to its domain — never waive a real `signoff: false` |
| Supply-domain crossing without level-shifter/isolation | fix is local: add the cell at `boundary_connect_rules`; if physical, fix_request → custom-layout (`connectivity`) |
| Implicit connect-module insertion at a boundary | Add an explicit connect rule; thresholds parameterised vs the crossing `supply.vdd_v` |
| Pad missing ESD clamp / incomplete IO ring | Loop back → `top_assembly`; re-check at `power_intent_check` |
| Analog island merged into a noisy supply | Loop back → `top_assembly` to re-isolate; physical coupling → fix_request → custom-layout |
| Top-LVS net mismatch | Reconcile net/instance names; re-extract preserving top net names; fix_request → custom-layout if structural |
| Analog/digital time drift in chip-level AMS sim | Align analog max-timestep to the digital tick; enable rollback/lockstep sync |
| UPF isolation/level-shifter inconsistency | Loop back → `top_assembly` (×2); never relax the power intent to pass |

## Integration Recipes

- Qualify first: confirm every block's producing-domain `signoff` is `true` and collect its
  integration views (netlist/GDS, pins, supplies, connect modules) before assembling anything.
- Reuse modeling/ams-verification connect modules (`design_state.modeling.connect_modules`,
  `design_state.ams`) — do not re-author boundary rules the AMS-verification domain already closed.
- Drive every checked spec from a cocotb assertion/scoreboard; root-cause each top-level failure to
  a domain (layout/circuit/model) and open the fix_request with the matching `route_to`.
- Run top-level LVS on the assembled netlist before the chip-level AMS sim — a connectivity fault
  invalidates the sim. Read the LVS/`.measure` summary, not raw logs (top-level logs are very large).
- `integration_signoff` is the chip tape-out gate: hold for the configured checkpoint approval
  before setting `signoff=true`.

## Tool Quirks

- **Magic + Netgen** top-level LVS: flatten only what is needed; preserve top net names so probe
  nets survive into the AMS sim.
- **cocotb + ngspice/Xyce** at the top: Xyce (parallel) favours the large flat top netlist; load
  once via the session MCP and sweep scenarios.
- **UPF/power-intent** in the open flow is partial — track domains/isolation/level-shifters
  explicitly in the assembly plan; proprietary UPF tools are detect-only.

## Metric Baselines

_(Populated by `memory-keeper` from `experiences.jsonl`: `top_lvs_errors`, `ams_sim_pass`, `connect_rule_errors`.)_
