---
name: parasitic-extraction
description: >
  Run RC and coupling extraction on the verified layout and build a back-annotated post-layout
  netlist for sign-off simulation. Use when extracting parasitics from a physically-clean GDS,
  building the PEX netlist for post-layout sign-off, or flagging a layout for parasitic
  reduction.
version: 1.0.0
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Parasitic Extraction

## Invocation

- **If invoked by a user** presenting an extraction task: immediately spawn the
  `analog-chip-design-agents:parasitic-extraction-orchestrator` agent and pass the full user
  request and any available context. Do not execute stages directly.
- **If invoked by the `parasitic-extraction-orchestrator` mid-flow**: do not spawn a new agent.
  Treat this file as read-only — return the requested stage rules, sign-off criteria, or
  loop-back guidance.

Spawning the orchestrator from within an active orchestrator run causes recursive delegation
and must never happen.

## Pre-run Context

Before executing or advising on **any** stage, read the following if they exist:

1. `memory/extraction/knowledge.md` — known extraction-deck settings, coupling-net recipes,
   back-annotation pitfalls, PDK extraction quirks. Incorporate its guidance into every run.
2. `memory/extraction/run_state.md` — current run identity for resume-after-interruption.

## Purpose

Extract R, C, and coupling parasitics from a physically-clean layout and build a
back-annotated post-layout netlist for sign-off simulation. Five stages with explicit QoR
gates. Extraction is the bridge between a clean GDS and post-layout sign-off; it gates on the
`pex_signoff` checkpoint and flags layouts for parasitic reduction when degradation is large.

---

## Supported EDA Tools

### Open-Source
- **Magic** (`magic`) — `ext` / `ext2spice` RC extraction
- **KLayout** (`klayout`) — PEX (R + limited C) decks
- **FastCap / FastHenry** (`fastcap`, `fasthenry`) — field-solver capacitance/inductance for critical nets

### Proprietary (detect-only — never installed)
- **Synopsys StarRC** (`starrc`) — sign-off RC extraction
- **Cadence Quantus QRC** (`quantus`)
- **Siemens Calibre xRC / xACT** (`calibre`)
- **Silvaco Clever** — 3-D field-solver extraction

---

## Stage: extraction_setup

### Domain Rules
1. Configure the extraction deck for the target `constraints.pdk` and the required extraction type (R-only, RC, or RC+coupling) based on the block's sensitivity.
2. Define the corner (best/worst-case parasitic) and the nets requiring coupling extraction (high-Z, matched, clock).
3. Confirm the input GDS passed physical-verification (`design_state.physical_verification.signoff`) before extracting.

### QoR Metrics to Evaluate
- Extraction deck matches the PDK + requested type
- Coupling-net list covers sensitive/matched/clock nets

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Deck/PDK mismatch | Re-select the deck for `constraints.pdk` |
| Missing coupling nets | Add high-Z / matched / clock nets to the coupling list |

### Output Required
- Extraction configuration (deck, corner, coupling-net list)

---

## Stage: rc_extraction

### Domain Rules
1. Run RC extraction (Magic `ext2spice` / KLayout PEX); capture per-net R and ground C across the layout.
2. Verify extraction coverage — every routed net is extracted; flag unextracted or shorted nets.
3. Sanity-check `r_count` / `c_count` against layout complexity; an implausibly low count signals an extraction-deck error.

### QoR Metrics to Evaluate
- Extraction coverage = 100% of routed nets
- `r_count` / `c_count` plausible vs layout complexity
- R/C accuracy vs golden (where a reference exists)

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Net not extracted | Fix the extraction deck / layer map; re-run |
| Implausibly low R/C count | extraction_setup (deck error) (×2) |

### Output Required
- RC-extracted data (per-net R, ground C)

---

## Stage: coupling_extraction

### Domain Rules
1. Extract coupling capacitance for the sensitive/matched/clock nets in the coupling list; use FastCap field-solving for critical high-Z nodes where deck C is insufficient.
2. Confirm coupling completeness — every listed net has its dominant aggressors captured.
3. Report the worst coupling pairs for the post-layout sign-off and for layout feedback.

### QoR Metrics to Evaluate
- Coupling completeness for every listed net
- `coupling_caps` captured for dominant aggressor/victim pairs

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Missing coupling on a high-Z net | Field-solve (FastCap) that net; add to the deck |
| Coupling too large to meet specs | Flag → custom-layout (re-route/shield) |

### Output Required
- Coupling report (aggressor/victim pairs, `coupling_caps`)

---

## Stage: netlist_back_annotation

### Domain Rules
1. Build the back-annotated PEX netlist (extracted R/C merged onto the LVS-matched devices) targeting the post-layout simulator.
2. Preserve device/net names so post-layout results map back to the schematic and the `.measure` testbench.
3. Confirm the PEX netlist size/runtime is tractable; reduce/lump non-critical parasitics if the netlist is too large.

### QoR Metrics to Evaluate
- PEX netlist assembles and name-maps to the schematic
- Netlist size/runtime within budget

### Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Names don't map to testbench | Preserve LVS net names; re-annotate |
| Netlist too large to simulate | Lump non-critical R/C; keep coupling on sensitive nets |

### Output Required
- Back-annotated PEX netlist + back-annotation map

---

## Stage: pex_signoff

### Sign-off Pass Criteria (all must pass)
| Check | Criterion |
|-------|-----------|
| Coverage | 100% of routed nets extracted |
| R/C accuracy | within tolerance vs golden (where available) |
| Coupling | complete for every listed sensitive net |
| Netlist | assembles, name-maps, simulatable within budget |

### Domain Rules
1. Confirm coverage, accuracy, coupling completeness, and a tractable PEX netlist.
2. Honour the `pex_signoff` checkpoint when configured (human approval before post-layout sign-off).
3. Hand the PEX netlist + back-annotation map to post-layout-signoff; flag large parasitic degradation to custom-layout.

### Failure Escalation
- Extraction error → extraction_setup (×2)
- Large parasitic degradation → `fix_request` (`failure_class: spec_violation`, `route_to: custom-layout`)

### Output Required
- Extracted (PEX) netlist
- Parasitic / coupling report
- Back-annotation map

---

## Constraint Validation

See [`plugins/meta/skills/pipeline-orchestration/SKILL.md`](../../../meta/skills/pipeline-orchestration/SKILL.md) §Constraints Schema for the authoritative schema and stage-entry validation rule.

**Required at entry (`extraction_setup`) — hard-fail if missing:**
- `design_state.layout.gds` — the layout to extract
- `constraints.pdk` — for the extraction deck
- `design_state.physical_verification.signoff` true — extract only a physically-clean layout

Skip constraint validation entirely when invoked in fix-request-servicing mode.

---

## Memory

### Run state (write before first stage, update after each stage)
Write `memory/extraction/run_state.md` as the **first action**:
```markdown
run_id:      extraction_<YYYYMMDD>_<HHMMSS>
design_name: <design>
pdk:         <pdk or unknown>
tool:        <primary tool>
start_time:  <ISO-8601>
last_stage:  null
```
Update `last_stage` to the completed stage name only after each stage finishes successfully.

### Write on stage completion
After each stage completes, upsert one JSON record in `memory/extraction/experiences.jsonl`
keyed by `run_id`. `key_metrics` fields: `r_count`, `c_count`, `coupling_caps`. Set
`signoff_achieved: false` until pex_signoff passes; then `true`. Create the file and parent
directories if they do not exist.

### Optional: claude-mem index
If `mcp__plugin_ecc_memory__add_observations` is available, emit each extraction-deck fix as an
observation to entity `analog-design-extraction-fixes` after writing to `experiences.jsonl`.
Skip silently if absent — the JSONL file is the canonical record.
