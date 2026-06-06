---
name: em-modeling
description: >
  Solve the electromagnetics of an on-chip passive or antenna (inductor, transformer, transmission
  line, balun, antenna), extract a converged passive S-parameter model, and fit a lumped equivalent
  for circuit-level RF simulation. Use when building or re-solving the passive model rf-design
  consumes. Loop-backs are stage-local (passivity/fit → meshing/geometry_definition); passivity is
  a hard gate; a fundamental geometry/stackup gap escalates (no cross-domain fix_request).
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: EM Modeling

## Invocation

- **If invoked by a user** presenting an EM-modeling task: immediately spawn the
  `analog-chip-design-agents:em-modeling-orchestrator` agent and pass the full user request and any
  available context. Do not execute stages directly.
- **If invoked by the `em-modeling-orchestrator` mid-flow** (including re-solves): do not spawn a
  new agent. Treat this file as read-only — return the requested stage rules, sign-off criteria, or
  loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation and
must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/em/knowledge.md` — known meshing recipes, passivity/fit fixes, de-embedding patterns,
   solver-selection rules, and PDK/tool quirks. Incorporate its guidance into every stage.
2. `memory/em/run_state.md` — current run identity for resume-after-interruption.

## Purpose

Solve the electromagnetics of an on-chip passive or antenna, extract a converged, passive
S-parameter model, and fit a lumped equivalent for circuit-level RF simulation. Seven stages with
explicit QoR gates. EM modeling is a **terminal/branch producer of a data dependency**: it writes a
Touchstone S-parameter model + fitted lumped model into `design_state.em` that `rf-design` reads as
a fixed passive input. Its loop-backs are stage-local (passivity/fit fail → `meshing` /
`geometry_definition`, max 2×); it does **not** open cross-domain `fix_request`s — a fundamental
geometry/stack-up gap escalates to the user.

> **Cross-domain integration (deferred):** automating an em↔rf re-solve loop via the meta
> `fix_request` protocol is a potential future enhancement tracked in
> [`FUTURE_WORK.md`](../../../../FUTURE_WORK.md). It is intentionally **not** implemented here.

---

## Supported EDA Tools

### Open-Source
- **openEMS** (`openEMS`) — FDTD full-wave solver (distributed passives, antennas, mmWave)
- **FastHenry** (`fasthenry`) / **FastCap** (`fastcap`) — quasi-static RL / C field solvers
- **gmsh** (`gmsh`) — mesh generation
- **scikit-rf** (Python `skrf`) — passivity / causality checks, fitting, de-embedding

### Proprietary (detect-only — never installed)
- **Ansys HFSS / SIwave / RaptorX** (`hfss`) — 3D / planar EM
- **Keysight Momentum / RFPro / EMPro** (`momentum`)
- **Cadence EMX** (`emx`) & **AWR AXIEM / Analyst** (`axiem`)
- **Sonnet** (`sonnet`) — planar EM

---

## Stage: em_setup

### Domain Rules
1. Read the passive intent (device type, target inductance/coupling/impedance, operating band) and
   the **geometry source** — a GDS/layout cell (`design_state.layout.gds`), a parametric-generator
   spec, or explicit dimensions — plus the metal stack-up / substrate from `constraints.pdk`.
2. Select the solver class by problem: full-wave FDTD (openEMS) for distributed / high-frequency
   passives and antennas; quasi-static (FastHenry/FastCap) for lumped RL/C below SRF. Record the
   choice.
3. Define the extraction frequency grid (DC/near-DC through past the expected SRF) and the port
   definitions / de-embedding reference planes.

### QoR Metrics to Evaluate
- Geometry source resolved; metal stack-up bound from `pdk`
- Frequency grid spans the band → past the expected SRF
- Ports / de-embedding reference planes defined

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| No metal stack-up for the PDK | escalate constraint_gap — require `pdk` with a layer stack |
| Frequency grid stops below SRF | extend the grid past the expected self-resonance |

### Output Required
- EM setup (device type, geometry source, stack-up, solver class, port/de-embed plan, frequency grid)

---

## Stage: geometry_definition

### Domain Rules
1. Build the 3D / 2.5D geometry from the source (import GDS layers to the stack-up, or instantiate
   the parametric generator); assign conductors, dielectrics, and ports with correct layer
   thicknesses and conductivity.
2. Validate the geometry is physically closed / manifold and ports are on valid reference planes;
   this is a **loop-back target** for fit/passivity failures traced to geometry.
3. Confirm the modeled region includes enough substrate / ground and air margin for the boundary
   conditions.

### QoR Metrics to Evaluate
- Geometry closed / manifold; layers mapped to the stack-up
- Ports correctly placed on valid reference planes
- Adequate ground / air margin for the boundaries

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Open / non-manifold geometry | repair the geometry; re-map GDS layers to the stack-up |
| Port reference plane misplaced | re-define ports on a valid plane and re-de-embed |

### Output Required
- Solver-ready geometry (conductors / dielectrics / ports mapped to the stack-up)

---

## Stage: meshing

### Domain Rules
1. Generate the mesh (gmsh for FE; openEMS rectilinear grid) with cell size ≤ λ/20 at the top
   frequency and refinement at conductor edges / coupled gaps (skin-depth-aware).
2. This is the primary **loop-back target**: a passivity or fit failure traced to under-resolution
   re-enters here to refine (max 2×).
3. Record the mesh cell count and the limiting feature size; ensure the mesh resolves the smallest
   critical gap.

### QoR Metrics to Evaluate
- Cell size ≤ λ/20 at f_max
- Conductor edges / coupled gaps refined
- Mesh resolves the smallest critical gap

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Coarse mesh → non-passive / poor fit | refine the mesh at edges/gaps (loop-back target, max 2×) |
| Mesh misses a thin coupled gap | add local refinement to resolve the gap |

### Output Required
- Mesh summary (cell count, min cell size, refinement regions)

---

## Stage: em_solve

### Domain Rules
1. Run the solver (openEMS FDTD / FastHenry-FastCap / proprietary if detected) across the frequency
   grid; confirm energy / residual convergence (FDTD: energy decay below threshold; FE: residual
   below tolerance).
2. On non-convergence (energy not decayed) or a runtime/resource limit, treat as
   `convergence`/`resource_limit`: extend timesteps or coarsen sensibly (within λ/20), else
   escalate.
3. Read the convergence summary from the solver summary file — **never** the raw field dump.

### QoR Metrics to Evaluate
- Solver converged at every frequency point
- Energy decay / residual below threshold
- No resource-limit abort

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| FDTD energy not decayed (no convergence) | extend timesteps / check excitation & boundaries; re-solve |
| Resource / runtime limit hit | reduce the domain / coarsen the mesh within λ/20, or escalate resource_limit |

### Output Required
- Solver convergence report (per-frequency energy decay / residual, runtime)

---

## Stage: sparameter_extraction

### Domain Rules
1. Extract the N-port S-matrix to a Touchstone (`.sNp`) file, de-embedding to the defined reference
   planes; compute the **passivity** check (all eigenvalues of I − SᴴS ≥ 0 across frequency) and a
   causality / reciprocity sanity check with scikit-rf.
2. A non-passive S-matrix is a **hard fail** → loop back to `meshing` (then `geometry_definition`)
   — max 2×.
3. Derive the physical figures: `q_factor` vs frequency, `srf_ghz` (first self-resonance), and
   coupling (k) for transformers.

### QoR Metrics to Evaluate
- S-matrix passive across the full band (`passivity_pass`)
- Reciprocal where expected
- `q_factor` / `srf_ghz` / coupling extracted

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Non-passive S-matrix | loop back → meshing (refine), then geometry_definition (max 2×) |
| SRF / Q implausible vs expectation | check ports / de-embedding; re-extract |

### Output Required
- Touchstone (`.sNp`) file + passivity report + `q_factor` / `srf_ghz` / coupling table

---

## Stage: model_fitting

### Domain Rules
1. Fit a lumped equivalent (π/T or broadband pole-residue / vector-fit) to the extracted S-params;
   compute `fit_error_pct` = max |fit − EM| / EM × 100 across the band (S-param or Z/Y error).
2. Enforce that the fitted model is itself **passive** (real-part / eigenvalue check) so
   circuit-level RF sim stays stable; a non-passive fit, or a passive but high-error fit traced to
   the EM data, → loop back to `meshing` / `geometry_definition` (max 2×); otherwise refine the fit
   order locally.
3. Confirm the fitted SRF / Q match the EM extraction within tolerance.

### QoR Metrics to Evaluate
- `fit_error_pct` ≤ budget (default ≤ 5%)
- Fitted model passive
- Fitted SRF / Q match the EM extraction within tolerance

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| `fit_error_pct` over budget | raise fit order / broadband (vector) fit; if EM data is the limiter, loop back → meshing |
| Fitted model non-passive | enforce passivity in the fit; if unachievable, loop back → meshing (max 2×) |

### Output Required
- Fitted lumped model (netlist / params) + `fit_error_pct` + passivity-of-fit report

---

## Stage: em_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| Passivity | extracted S-matrix and fitted model both passive across the band (`passivity_pass`) |
| Convergence | solver converged at every frequency point |
| Fit accuracy | `fit_error_pct` ≤ budget (default 5%) |
| Physical sanity | `q_factor` / `srf_ghz` / coupling extracted and plausible vs intent |

### Domain Rules
1. Confirm passivity, convergence, fit accuracy, and physical sanity all pass.
2. Publish the Touchstone + fitted lumped model into `design_state.em` for `rf-design` to consume.
3. Close any serviced re-solve as PASS.

### Failure Escalation
- Passivity / fit fail after the retry cap → escalate to the user with the failing
  frequency/metric and a recommendation (re-mesh, change the geometry, or relax the band) — do
  **not** open a cross-domain fix_request.

### Output Required
- EM sign-off report (passivity, convergence, fit accuracy, physical sanity)
- Published Touchstone + fitted lumped model

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`em_setup`) — hard-fail if missing:**
- `constraints.pdk` — the metal stack-up / substrate (without it there is no geometry to solve)
- a **geometry source** — `design_state.layout.gds` (preferred) **or** an explicit
  parametric-generator / dimension spec passed in the prompt/constraints

EM modeling does **not** require `supply.vdd_v` or `rf_specs` — passive extraction is
bias-independent (a deliberate divergence from the rf-design required set). Skip constraint
validation entirely when invoked in re-solve / fix-servicing mode.

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/em/run_state.md` as the **first action**:
```markdown
run_id:      em_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/em/experiences.jsonl` keyed by
`run_id`. `key_metrics` fields: `q_factor`, `srf_ghz`, `fit_error_pct`. Set
`signoff_achieved: false` until em_signoff passes; then `true`. Create the file and parent
directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each meshing / passivity / fit fix
as an observation to entity `analog-design-em-fixes` after writing to `experiences.jsonl`. Skip
silently if absent — the JSONL file is the canonical record.
