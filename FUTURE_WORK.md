# Future Work

Deferred enhancements and planned work for `analog-chip-design-agents`. Items here are
intentionally **not** implemented yet; each notes the trade-off and the trigger for adopting it.

---

## Cross-domain RF/EM integration (deferred from Phase 5)

**Status:** deferred. **Phase 5 chose the terminal/branch approach** for `rf-design` and
`em-modeling`, mirroring the `architecture` and `characterization` precedent.

### What is implemented today (Phase 5)
- `rf-design` and `em-modeling` are **terminal/branch domains**: loop-backs are stage-local
  (rf: spec/stability → `topology_matching`, convergence → `harmonic_balance`; em: passivity/fit →
  `meshing`/`geometry_definition`), and a fundamental gap **escalates to the user**.
- `em-modeling` → `rf-design` is a **data dependency**, not a repair loop: EM publishes the `em`
  block (Touchstone + fitted lumped model) into `design_state.json`; RF reads it as a fixed passive
  input. When RF finds a passive is the limiter, it escalates to the user *recommending* an EM
  re-solve.
- The meta `route_to` / `created_by` / `failure_class` enums are **unchanged** — RF/EM do not open
  cross-domain `fix_request`s.

### The deferred alternative (Option 2)
Wire RF (and the em↔rf coupling) into the meta cross-domain `fix_request` loop:
- Add `rf-design` to the meta `fix_request` enums — `created_by` (RF as a producer), `route_to`
  (e.g. `circuit-design` for an RF spec miss that needs device-level rework, and `em-modeling` so
  an RF-detected passive shortfall opens an **automated** EM re-solve request), and any new
  `failure_class` values needed.
- Extend the pipeline-orchestrator dispatch/participants wiring (and the CI `VALID_FR_FAILURE` /
  fixture checks) so RF spec misses auto-route to the right servicer and em↔rf re-solves run
  closed-loop without a manual user step.

### Trade-offs
- **For:** fully automated RF closure (RF spec miss → circuit-design rework → re-validate) and
  automated em↔rf re-solve loops, with no manual escalation in the common case.
- **Against:** a larger, higher-risk diff touching `plugins/meta/skills/pipeline-orchestration/`,
  the dispatch wiring, and CI enum/fixture checks; it diverges from how every other branch/terminal
  domain (`architecture`, `characterization`) behaves today. RF's natural repair target
  (`topology_matching`) is already an internal stage, so much of the benefit is only realized when
  an RF miss genuinely needs device-level circuit-design rework.

### Trigger for adopting it
Pick this up when real RF runs show frequent RF→circuit-design rework or em↔rf re-solve cycles that
are painful to drive by hand, **or** when a top-level mixed-signal flow needs RF blocks to close
fully unattended inside the meta loop alongside the other domains.

---

## Phase 6 (planned)

- **`analog-design-ams-integration`** — fill in the remaining skeleton domain (mixed-signal top
  assembly, boundary/connect rules, chip-level AMS sim, power intent). Last domain still skeleton.
- **`ides/` multi-assistant export** (Copilot / Gemini / OpenCode / Codex), `install.sh` /
  `install.ps1`, `tools/qor_trends.py`, and `release.yml` — per `PLAN.md` §12 Phase 6.
