# analog-chip-design-agents — Repository Plan

> Planning document for an **analog / mixed-signal + RF chip-design** Claude Code
> marketplace, modelled on the
> [`digital-chip-design-agents`](https://github.com/chuanseng-ng/digital-chip-design-agents)
> reference repo.
>
> **Scope (agreed):** full analog/mixed-signal flow **with RF/mmWave emphasis** —
> spec/architecture → behavioral & AMS HDL modeling → schematic/circuit design →
> SPICE simulation → mixed-signal verification → custom layout → physical
> verification → parasitic extraction → post-layout sign-off → reliability →
> characterization → RF design → EM → mixed-signal top integration, plus shared
> infrastructure and a meta pipeline orchestrator.
>
> **Status: fully delivered.** All 16 plugins and Phases 0–7 described below are
> implemented — see [`CHANGELOG.md`](CHANGELOG.md). This document is retained as
> the design rationale and roadmap reference; the §13 decisions are resolved and
> the remaining deferred enhancements are tracked in [`FUTURE_WORK.md`](FUTURE_WORK.md).

---

## 1. Design goals & parity with the reference repo

The reference `digital-chip-design-agents` repo is a Claude Code **plugin
marketplace**: 15 plugins (13 design domains + `infrastructure` + `meta`), each an
isolated `plugins/<domain>/` directory containing a **Skill** (domain knowledge
Claude auto-loads) and an **Orchestrator Agent** (a subagent that sequences stages,
enforces QoR gates, applies loop-back rules, and escalates). A root
`.claude-plugin/marketplace.json` registers all plugins; `install.sh`/`install.ps1`
install them in one step; an `ides/` tree exports the same domain knowledge to
Copilot/Gemini/OpenCode/Codex; a two-tier `memory/` store persists learnings; and
CI validates every file.

This repo will replicate **the same architecture, conventions, and file formats**,
re-targeting every domain to analog/mixed-signal + RF. Specifically we keep:

| Reference convention | Kept as-is for analog |
|---|---|
| One isolated `plugins/<domain>/` dir per plugin | ✅ |
| `plugins/<domain>/.claude-plugin/plugin.json` per-plugin manifest | ✅ |
| `plugins/<domain>/skills/<skill>/SKILL.md` (frontmatter + stage rules) | ✅ |
| `plugins/<domain>/agents/<domain>-orchestrator.md` | ✅ |
| Root `.claude-plugin/marketplace.json` registry | ✅ |
| Each SKILL lists **Open-Source** + **Proprietary** tools | ✅ (analog/RF tools) |
| Stage-by-stage rules, QoR metrics, loop-back caps, escalation | ✅ |
| Shared `design_state.json` cross-orchestrator state + `history[]` trace | ✅ |
| Two-tier `memory/<domain>/{knowledge.md, experiences.jsonl}` | ✅ |
| `meta` pipeline orchestrator with fix_request loop + iteration cap | ✅ |
| `infrastructure` plugin: tool detection, JSON wrappers, MCP tiers, memory-keeper | ✅ |
| `ides/` multi-assistant export + `install.sh`/`install.ps1` | ✅ |
| `.github/workflows/validate.yml` + `release.yml`, `tools/qor_trends.py` | ✅ |

**What changes vs. digital:** the design abstraction is continuous-valued, not
RTL. QoR is electrical (gain, bandwidth, phase margin, noise, linearity, power,
matching, yield-sigma, NF, IP3, phase noise) rather than WNS/coverage. The "build"
artifact path is *schematic → netlist → layout → GDS*, signed off by *post-PEX
corner + Monte-Carlo simulation*, *DRC/LVS*, and *reliability (EM/IR/ESD)* — not
synthesis/STA/ATPG.

---

## 2. Naming & branding decisions

- **Marketplace name:** `analog-chip-design-agents` (matches repo name).
- **Plugin prefix:** `analog-design-<domain>` — e.g. `analog-design-circuit`,
  `analog-design-rf`. *(Reference uses `chip-design-<domain>`; `analog-design-`
  keeps parity while disambiguating from the digital marketplace so both can be
  installed side-by-side.)*
- **Invocation example:** `/plugin install analog-design-circuit@analog-chip-design-agents`.
- **Default open PDKs targeted:** `sky130`, `gf180mcu`, `ihp-sg13g2` (SiGe BiCMOS —
  RF-capable). Proprietary foundry PDKs (TSMC/GF/Samsung/UMC) are *detect-only*.

---

## 3. End-to-end pipeline

```
[System / Product Spec]
        │
        ▼
[1. Analog Architecture] ──► signal-chain budget, block spec allocation
        │
        ├──► [2. Behavioral / AMS Modeling] ──► Verilog-A/AMS, RNM, OSDI models
        │            │  (top-down executable spec; later bottom-up calibration)
        │            ▼
        ├──► [3. Circuit (Schematic) Design] ──► sized schematic + netlist
        │            │
        │            ▼
        │     [4. Circuit Simulation (SPICE)] ◄───────────────┐
        │            │  DC/AC/tran/noise/corners/Monte-Carlo   │ fix_request
        │            ▼                                         │   loop
        │     [5. AMS Verification] (analog↔digital co-sim)    │
        │            │                                  [Meta / Pipeline Orch.]
        │            ▼                                         │
        ├──► [6. Custom Layout] ──► matched, shielded layout   │
        │            │                                         │
        │            ▼                                         │
        │     [7. Physical Verification] (DRC / LVS / ERC)     │
        │            │                                         │
        │            ▼                                         │
        │     [8. Parasitic Extraction] (RC/coupling → PEX)    │
        │            │                                         │
        │            ▼                                         │
        │     [9. Post-Layout Sign-off] (post-PEX corners) ────┘
        │            │
        │            ├──► [10. Reliability] (EM / IR / ESD / aging)
        │            └──► [11. Characterization] (.lib / model gen)
        │
        ├──► [12. RF / mmWave Design] ──► S-param / HB / Pnoise / load-pull
        │            └──► [13. EM Modeling] (inductors, lines, antennas → S-params)
        │
        └──► [14. Mixed-Signal Top Integration] ──► AMS chip assembly → tape-out
```

`infrastructure` and `meta` sit beside the flow (tool setup + cross-domain
orchestration), exactly as in the reference repo.

---

## 4. Plugin / domain catalogue

16 plugins total: **14 design domains + `infrastructure` + `meta`** (within the
"~15–17, RF emphasis" target).

| # | Plugin (`analog-design-…`) | Skill folder | Invoke when you want to… |
|---|---|---|---|
| 1 | `…-architecture` | `analog-architecture` | Capture specs, budget noise/linearity/power across a signal chain, allocate block specs, assess feasibility |
| 2 | `…-modeling` | `behavioral-modeling` | Write/compile Verilog-A · Verilog-AMS · VHDL-AMS · SystemVerilog real-number models; build OSDI/connect modules |
| 3 | `…-circuit` | `circuit-design` | Pick a topology, size/bias devices, capture schematic, run pre-layout ERC/design review |
| 4 | `…-simulation` | `circuit-simulation` | Run DC/AC/transient/noise/stability, corners, temperature, Monte-Carlo and sign off electrical specs |
| 5 | `…-ams-verification` | `ams-verification` | Build AMS testbench, set connect rules, run analog↔digital co-sim, close coverage on RNM |
| 6 | `…-layout` | `custom-layout` | Floorplan, generate matched devices, place/route analog with symmetry/shielding |
| 7 | `…-physical-verification` | `physical-verification` | Run DRC, LVS, antenna/ERC, density/DFM and sign off physical correctness |
| 8 | `…-extraction` | `parasitic-extraction` | RC + coupling extraction, build back-annotated post-layout netlist |
| 9 | `…-post-layout` | `post-layout-signoff` | Run post-PEX corner + MC sim, re-verify specs, gate tape-out |
| 10 | `…-reliability` | `reliability` | EM / IR-drop / ESD / latch-up / aging (HCI/NBTI) analysis and sign-off |
| 11 | `…-characterization` | `characterization` | Generate Liberty/.lib + behavioral models, characterize timing/power/noise of analog macros |
| 12 | `…-rf` | `rf-design` | Design LNA/mixer/VCO/PLL/PA; S-param, harmonic balance, Pnoise/PAC, IP3, load-pull |
| 13 | `…-em` | `em-modeling` | Solve EM for inductors/transformers/transmission-lines/antennas; extract/fit S-parameter models |
| 14 | `…-ams-integration` | `ams-integration` | Qualify analog IP, assemble mixed-signal top, boundary/connect rules, chip-level AMS sim |
| 15 | `analog-design-infrastructure` | `infrastructure` + `memory-keeper` | Detect analog/RF tools, deploy JSON wrappers, configure MCP servers, distil memory |
| 16 | `analog-design-meta` | `pipeline-orchestration` | Drive closed-loop spec↔circuit↔layout feedback via `design_state.json` fix_requests with iteration cap |

> **Optional consolidation:** #9 `post-layout-signoff` reuses the
> `circuit-simulation` skill heavily (same simulators, extracted netlist). If we
> want a leaner 15-plugin set, it can fold into #4 as a `post_layout_*` stage
> group. Flagged for confirmation in §13.

---

## 5. Per-domain detail (stages · QoR · loop-backs · tools)

Each domain follows the reference pattern: a strict **stage sequence**, **QoR
metrics** with thresholds drawn from `design_state.constraints` (schema in §8),
and **loop-back rules** with retry caps enforced by the orchestrator. Below is the
intended content for each SKILL/orchestrator pair. Tool lists separate
**Open-Source** from **Proprietary** (the latter *detect-only*, never installed).

### 5.1 `analog-architecture`
- **Stages:** `spec_capture → signal_chain_budgeting → topology_partitioning → behavioral_feasibility → architecture_signoff`
- **QoR:** noise budget (input-referred / SNR / NF allocation), linearity budget (IP3/THD), power budget, area estimate, supply/headroom, per-block spec table.
- **Loop-backs:** feasibility fail → `topology_partitioning` (×2); budget infeasible → `spec_capture` renegotiate → escalate.
- **Tools — OSS:** Python budgeting (NumPy/scikit-rf), Jupyter, ngspice/Xyce for quick behavioral sanity. **Proprietary:** Cadence ADE Assembler / Spectre, Keysight SystemVue, MATLAB/Simulink (system models).

### 5.2 `behavioral-modeling` *(the "analog HDL" core)*
- **Stages:** `model_planning → va_authoring → model_compilation → connect_rule_setup → model_validation → model_signoff`
- **QoR:** model-vs-SPICE error %, convergence robustness, sim speed-up factor, RNM toggle/branch coverage, connect-module completeness.
- **Loop-backs:** compile fail → `va_authoring` (×3); validation error > tol → `va_authoring` (×3) → escalate.
- **Tools — OSS:** **OpenVAF** (Verilog-A → OSDI for ngspice/Xyce), **ADMS** (legacy Verilog-A→C), ngspice/Xyce OSDI loading, SystemVerilog RNM (`nettype`/`wreal`) via Verilator/Icarus, **Hdl21 + VLSIR** (Python analog HDL), VHDL-AMS (GHDL-AMS — limited). **Proprietary:** Cadence AMS Designer / Xcelium AMS, Spectre Verilog-A, Synopsys VCS-AMS / CustomSim, Siemens Symphony / Symphony Pro.

### 5.3 `circuit-design` *(schematic)*
- **Stages:** `topology_selection → device_sizing → biasing → schematic_capture → pre_layout_erc → design_review`
- **QoR:** DC gain, GBW, phase margin, slew, offset, PSRR/CMRR, power, device matching/headroom, gm/Id operating region.
- **Loop-backs:** ERC fail → `device_sizing` (×2); review fail → `topology_selection` (×1) → escalate.
- **Tools — OSS:** **xschem** (schematic/netlist), Qucs-S, KLayout, ngspice in the loop, **BAG/BAG3** & **Hdl21** generators, gm/Id toolkits. **Proprietary:** Virtuoso Schematic Editor, Synopsys Custom Compiler, Tanner S-Edit, **MunEDA WiCkeD** & Siemens **Solido** (sizing/optimization/yield).

### 5.4 `circuit-simulation` *(SPICE)*
- **Stages:** `testbench_setup → dc_op → ac_analysis → transient → noise_analysis → corner_analysis → monte_carlo → sim_signoff`
- **QoR:** all electrical specs vs target across PVT corners; MC yield (σ / Cpk); convergence; sim runtime.
- **Loop-backs:** corner/MC fail → `fix_request` to `circuit-design`; non-convergence → `testbench_setup` (×2).
- **Tools — OSS:** **ngspice**, **Xyce** (parallel), gnucap, Qucs-S, **PySpice** (control/MC). **Proprietary:** Spectre / Spectre X / APS, HSPICE, **PrimeSim** (HSPICE/XA/Pro), FineSim, **AFS** (Analog FastSPICE), Eldo, SmartSpice (Silvaco), ALPS/NanoSpice (Empyrean).

### 5.5 `ams-verification`
- **Stages:** `ams_testbench → connect_module_setup → analog_digital_cosim → rnm_regression → coverage_closure → ams_signoff`
- **QoR:** functional coverage, RNM-vs-SPICE agreement, connect-module correctness, regression pass-rate, assertion failures.
- **Loop-backs:** cosim mismatch → `fix_request` to `behavioral-modeling` or `circuit-design`; coverage gap → `ams_testbench` (×2).
- **Tools — OSS:** **cocotb** + ngspice/Xyce co-sim, Verilator/Icarus (digital + RNM), Xyce mixed-signal. **Proprietary:** Cadence Xcelium AMS / AMS Designer, Spectre AMS, Synopsys VCS-AMS / CustomSim, Siemens Symphony + QuestaSim, AFS-driven co-sim.

### 5.6 `custom-layout`
- **Stages:** `layout_floorplan → device_generation → analog_placement → analog_routing → layout_finishing → layout_check`
- **QoR:** matching quality (common-centroid/interdigitation), symmetry, density, area, shielding of sensitive nets, antenna-readiness.
- **Loop-backs:** layout_check fail → `analog_routing`/`analog_placement` (×3).
- **Tools — OSS:** **Magic**, **KLayout**, **gdsfactory/gdstk**, **ALIGN** & **MAGICAL** (analog layout automation), BAG layout generators. **Proprietary:** Virtuoso Layout (XL/GXL/EAD), Synopsys Custom Compiler Layout, Tanner L-Edit, Silvaco Expert.

### 5.7 `physical-verification`
- **Stages:** `drc → lvs → antenna_erc → density_dfm → pv_signoff`
- **QoR:** DRC = 0, LVS clean (devices+nets matched), antenna = 0, density within window, ERC clean.
- **Loop-backs:** DRC/LVS fail → `fix_request` to `custom-layout` (×3).
- **Tools — OSS:** **Magic** (DRC/ext) + **Netgen** (LVS), **KLayout** DRC/LVS decks. **Proprietary:** Siemens **Calibre** nmDRC/nmLVS, Synopsys **IC Validator (ICV)**, Cadence **Pegasus** / Assura, Silvaco Guardian.

### 5.8 `parasitic-extraction`
- **Stages:** `extraction_setup → rc_extraction → coupling_extraction → netlist_back_annotation → pex_signoff`
- **QoR:** extraction coverage, R/C accuracy vs golden, coupling completeness, netlist size/runtime.
- **Loop-backs:** extraction error → `extraction_setup` (×2); huge degradation flagged to `custom-layout`.
- **Tools — OSS:** Magic `ext`/`ext2spice`, KLayout PEX (R + limited C), **FastCap/FastHenry** (field solvers). **Proprietary:** Synopsys **StarRC**, Cadence **Quantus QRC**, Siemens **Calibre xRC/xACT**, Silvaco Clever.

### 5.9 `post-layout-signoff`
- **Stages:** `pex_netlist_assembly → post_layout_corner_sim → spec_reverification → margin_analysis → tapeout_signoff`
- **QoR:** post-layout spec margin vs pre-layout, degradation %, corner/MC pass at sign-off, parasitic-induced stability/CMRR loss.
- **Loop-backs:** spec fail → `fix_request` to `custom-layout` (parasitic reduction) or `circuit-design` (×2) → escalate at tape-out gate.
- **Tools:** same simulators as §5.4 driven on the extracted netlist; **checkpoint gate** `tapeout_signoff` (human approval, like the reference `pd_signoff`).

### 5.10 `reliability`
- **Stages:** `em_analysis → ir_drop → esd_check → latchup_check → aging_analysis → reliability_signoff`
- **QoR:** EM current-density margin, IR-drop %, ESD/latch-up rule pass, HCI/NBTI/aging degradation over lifetime.
- **Loop-backs:** EM/IR fail → `fix_request` to `custom-layout` (widen/strap) (×2); ESD fail → `circuit-design`.
- **Tools — OSS:** limited — manual ngspice EM/IR estimates, KLayout density scripts. **Proprietary:** Cadence **Voltus** / Legato Reliability, Ansys **RedHawk/Totem** & PathFinder (ESD), Siemens **Calibre PERC**, Magwel.

### 5.11 `characterization`
- **Stages:** `char_setup → timing_char → power_char → noise_char → liberty_generation → model_validation → char_signoff`
- **QoR:** .lib completeness, characterization accuracy vs SPICE, corner/voltage/temperature coverage, model monotonicity.
- **Loop-backs:** validation fail → `char_setup` (×2).
- **Tools — OSS:** custom ngspice/Xyce sweep harnesses, Python `.lib` writers. **Proprietary:** Cadence **Liberate**, Synopsys **SiliconSmart**, Siemens **Solido ML Characterization**, Altos (legacy).

### 5.12 `rf-design` *(RF/mmWave emphasis)*
- **Stages:** `rf_spec → topology_matching → sparameter_analysis → harmonic_balance → noise_linearity → loadpull_optimization → rf_signoff`
- **QoR:** NF, gain (S21), return loss (S11/S22), IIP3/P1dB, phase noise (VCO/PLL), PAE/Pout (PA), EVM, stability (K-factor).
- **Loop-backs:** spec fail → `topology_matching` (×2); convergence → `harmonic_balance` settings (×2).
- **Tools — OSS:** Qucs-S (HB), **Xyce HB**, ngspice (limited RF), **scikit-rf** (S-param math), openEMS for passives. **Proprietary:** Cadence **Spectre RF**, Keysight **ADS** / GoldenGate, Cadence **AWR Microwave Office**, Synopsys HSPICE-RF, AFS-RF.

### 5.13 `em-modeling`
- **Stages:** `em_setup → geometry_definition → meshing → em_solve → sparameter_extraction → model_fitting → em_signoff`
- **QoR:** S-parameter accuracy/passivity, Q-factor, self-resonant frequency, lumped-model fit error, coupling.
- **Loop-backs:** passivity/fit fail → `meshing`/`geometry_definition` (×2).
- **Tools — OSS:** **openEMS** (FDTD), **FastHenry/FastCap**, **gmsh** (mesh), scikit-rf (fitting). **Proprietary:** Ansys **HFSS** / SIwave / RaptorX, Keysight **Momentum/RFPro/EMPro**, Cadence **EMX** & AWR AXIEM/Analyst, **Sonnet**.

### 5.14 `ams-integration`
- **Stages:** `ip_qualification → top_assembly → boundary_connect_rules → chip_level_ams_sim → power_intent_check → integration_signoff`
- **QoR:** connectivity (LVS at top), AMS top-sim pass, power-intent (UPF) consistency, IO/ESD ring completeness, analog-island isolation.
- **Loop-backs:** sim/connectivity fail → `fix_request` to the offending domain; power-intent fail → `ams_top` rework (×2).
- **Tools — OSS:** cocotb co-sim, KLayout/Magic+Netgen top-level LVS. **Proprietary:** Virtuoso (top assembly), Xcelium AMS / Spectre AMS, VCS-AMS, Siemens Symphony; UPF flows via Synopsys/Cadence.

---

## 6. `infrastructure` plugin (tool detection · wrappers · MCP · memory)

Mirrors `chip-design-infrastructure`, re-targeted to analog/RF. Stages:
`tool_discovery → module_discovery → tool_installation → wrapper_deployment →
mcp_configuration → environment_validation`.

**Open-source tools detected/installable:** ngspice, Xyce, gnucap, Qucs-S, xschem,
Magic, Netgen, KLayout, OpenVAF, ADMS, openEMS, FastHenry, FastCap, gmsh,
scikit-rf, PySpice, cocotb, Hdl21/VLSIR, gdstk/gdsfactory, ALIGN, MAGICAL, BAG3,
GHDL, Verilator, Icarus, GTKWave, ngspice's `ngnutmeg`, open_pdks (sky130 /
gf180mcu / ihp-sg13g2), uv (Python env). *(Mirror the reference's Python-interpreter
detection + Environment-Modules logic verbatim — it is tool-agnostic.)*

**Proprietary tools detected (never installed):** Cadence Virtuoso/Spectre/Spectre
RF/Spectre X/APS/Xcelium AMS/AMS Designer/Quantus/Pegasus/Voltus/Liberate/EMX;
Synopsys Custom Compiler/HSPICE/PrimeSim/FineSim/StarRC/IC Validator/SiliconSmart;
Siemens Calibre/Symphony/AFS/Eldo/Solido; Keysight ADS/Momentum; Ansys
HFSS/RedHawk; Sonnet; Silvaco; Empyrean — via `which` on primary executables
(`virtuoso`, `spectre`, `hspice`, `finesim`, `calibre`, `icv`, `xrun`, `ads`,
`hfss`, `starrc`, `quantus`, …) and Environment-Modules listings.

**Wrappers (compact JSON, not raw logs):** SPICE wrappers parse `.lis`/`.measure`/
`.mt0` outputs into `{specs, corners, mc_yield, convergence}`; DRC/LVS wrappers
summarise violation counts; EM wrappers emit Touchstone-summary JSON. Same
`{tool, exit_code, status, summary, errors, warnings, raw_log}` schema as the
reference.

**MCP tiers:** *Tier-1 batch* (ngspice/Xyce single analysis, Magic DRC, KLayout
DRC/LVS, OpenVAF compile, openEMS short solve); *Tier-2 session* (interactive
ngspice/Xyce session for measurement sweeps, Magic/Netgen session for iterative
LVS). *Full-flow / long EM solves* run via Bash and read output files. Reuse the
reference's `mcp-adapter.py` / `mcp-session-adapter.py` adapter pattern.

**`memory-keeper`** sub-skill: distils `experiences.jsonl` → `knowledge.md` per
domain (known convergence fixes, PDK device quirks, matching recipes, EM mesh
settings) — copied from the reference with analog examples.

---

## 7. `meta` pipeline orchestrator

Mirrors `chip-design-meta`: owns `design_state.json`, drives the closed-loop
**spec ↔ circuit ↔ layout** feedback via `fix_request` records, enforces an
iteration cap (default 3) with user escalation, and manages **checkpoints**
(suggested: `architecture_signoff`, `schematic_signoff`, `pex_signoff`,
`tapeout_signoff` — each requiring human approval before proceeding).

Key fix_request flows: simulation/MC fail → circuit-design; post-layout spec loss →
custom-layout; EM/IR fail → custom-layout; AMS cosim mismatch → behavioral-modeling.
Failure-classification + retry-strategy mapping and the 10-field `history[]` schema
are carried over unchanged (`functional → regenerate`, `convergence → refine`,
`spec_gap → escalate`, etc.; analog adds `convergence` and `yield`/`matching`
failure classes).

---

## 8. `design_state.json` constraints schema (analog)

Replaces the digital timing/area/power schema with electrical specs. Sketch:

```jsonc
"constraints": {
  "supply":   { "vdd_v": 1.8, "vss_v": 0.0 },
  "specs": {                         // per top-level block; domain QoR gated on these
    "dc_gain_db": 60, "gbw_hz": 1e7, "phase_margin_deg": 60,
    "input_noise_nv_rthz": 10, "psrr_db": 70, "cmrr_db": 80,
    "offset_mv_max": 5, "power_mw": 2.0, "settling_ns": 100,
    "thd_db": -60, "iip3_dbm": 0
  },
  "rf_specs": {                      // populated for rf-design / em-modeling
    "nf_db": 3, "gain_db": 20, "s11_db_max": -10, "iip3_dbm": -5,
    "p1db_dbm": 0, "phase_noise_dbc_hz": -100, "pae_pct": 30, "evm_pct": 3
  },
  "corners": {                       // PVT + analog statistical
    "process": ["tt","ss","ff","sf","fs"], "mismatch": true,
    "temp_c": [-40, 27, 125], "voltage_pct": [-10, 0, 10]
  },
  "yield":  { "target_sigma": 3, "mc_samples": 1000 },
  "area_um2": 50000,
  "pdk": "sky130"   // or gf180mcu | ihp-sg13g2 | <proprietary detect-only>
}
```

Each SKILL references defaults the same way the reference does
(`design_state.constraints.specs.phase_margin_deg` with a documented default).
Domain fields merged on completion mirror the reference (`circuit`, `sim`,
`layout`, `pex`, `reliability`, `char`, `rf` blocks with their key metrics +
`signoff` booleans).

---

## 9. Memory system

`memory/<domain>/knowledge.md` (Tier-2 distilled) + `memory/<domain>/experiences.jsonl`
(Tier-1 append/upsert by `run_id`) for every domain in §4. `run_state.md` per
domain for resume-after-interruption, identical to the reference. Distillation via
`analog-design-infrastructure:memory-keeper`.

---

## 10. `tools/qor_trends.py`

Re-targeted to analog metrics: trend `dc_gain_db`, `phase_margin_deg`,
`input_noise`, `power_mw`, `nf_db`, `iip3_dbm`, `mc_yield_sigma`, `area_um2`,
`em_margin`, `ir_drop_pct` across runs for a named design, with regression alerts
(e.g. phase margin drops, NF rises, yield-sigma falls). Group-by `pdk`
(sky130/gf180mcu/ihp-sg13g2) or `tool` (ngspice vs Spectre) — same CLI surface as
the reference.

---

## 11. Repository structure (target)

```
analog-chip-design-agents/
├── .claude-plugin/
│   └── marketplace.json                 ← registers all 16 plugins
├── plugins/
│   ├── architecture/      {.claude-plugin/plugin.json, agents/…-orchestrator.md, skills/analog-architecture/SKILL.md}
│   ├── modeling/          {…, skills/behavioral-modeling/SKILL.md}
│   ├── circuit/           {…, skills/circuit-design/SKILL.md}
│   ├── simulation/        {…, skills/circuit-simulation/SKILL.md}
│   ├── ams-verification/  {…, skills/ams-verification/SKILL.md}
│   ├── layout/            {…, skills/custom-layout/SKILL.md}
│   ├── physical-verification/ {…, skills/physical-verification/SKILL.md}
│   ├── extraction/        {…, skills/parasitic-extraction/SKILL.md}
│   ├── post-layout/       {…, skills/post-layout-signoff/SKILL.md}
│   ├── reliability/       {…, skills/reliability/SKILL.md}
│   ├── characterization/  {…, skills/characterization/SKILL.md}
│   ├── rf/                {…, skills/rf-design/SKILL.md}
│   ├── em/                {…, skills/em-modeling/SKILL.md}
│   ├── ams-integration/   {…, skills/ams-integration/SKILL.md}
│   ├── infrastructure/    {…, skills/infrastructure/SKILL.md, skills/memory-keeper/{SKILL.md,distill.py}, tools/, mcp/}
│   └── meta/              {…, skills/pipeline-orchestration/SKILL.md}
├── ides/                  {copilot/, gemini/, opencode/, codex/}   ← multi-assistant export
├── memory/                {<domain>/knowledge.md, <domain>/experiences.jsonl}
├── tools/qor_trends.py
├── install.sh / install.ps1
├── .github/workflows/     {validate.yml, release.yml}
├── docs/                   {installation.md, architecture.md, design_state_schema.md, pdk_support.md, templates/,
│                            PLAN.md (this file), CHANGELOG.md, FUTURE_WORK.md}
└── README.md  CONTRIBUTING.md  LICENSE
```

---

## 12. Phased implementation roadmap

**All phases below are delivered** (see [`CHANGELOG.md`](CHANGELOG.md)); this is
the build order that was followed — each phase was independently shippable and
CI-validated.

- **Phase 0 — Skeleton & conventions:** `marketplace.json`, root README/CONTRIBUTING/
  LICENSE (MIT, matching reference), `.github/workflows/validate.yml`, plugin.json
  template, SKILL/orchestrator templates, `design_state.json` schema doc.
- **Phase 1 — Core analog spine (highest value):** `circuit-design`,
  `circuit-simulation`, `infrastructure`, `meta`. Gets a working
  schematic→SPICE→sign-off loop on open PDKs.
- **Phase 2 — HDL/AMS:** `behavioral-modeling`, `ams-verification`,
  `analog-architecture`. Delivers the "analog HDL" headline capability.
- **Phase 3 — Physical:** `custom-layout`, `physical-verification`, `extraction`,
  `post-layout-signoff`. Completes RTL-to-GDS-equivalent silicon path.
- **Phase 4 — Sign-off depth:** `reliability`, `characterization`.
- **Phase 5 — RF emphasis:** `rf-design`, `em-modeling`.
- **Phase 6 — Integration & polish:** `ams-integration`, `ides/` exports,
  `install.sh`/`install.ps1`, `tools/qor_trends.py`, `release.yml`, FUTURE_WORK.
- **Phase 7 — RF/EM cross-domain integration:** wire `rf-design` into the meta
  `fix_request` loop as a producer (`route_to: circuit-design` for a device-level
  spec miss, `route_to: em-modeling` for a passive shortfall) with `em-modeling` as
  the servicer and `rf-design` as the re-validation target. Closes the sole
  deferred RF/EM enhancement from Phase 5.

---

## 13. Decisions (resolved)

The questions raised before scaffolding have all been resolved and reflected in
the shipped repo:

1. **Plugin prefix** — `analog-design-<domain>` (disambiguates from the digital
   `chip-design-` marketplace so both install side-by-side).
2. **Post-layout plugin** — kept as a standalone plugin; the catalogue is 16
   plugins (14 domains + infrastructure + meta).
3. **Default open PDKs** — `sky130` primary, `gf180mcu` + `ihp-sg13g2` (RF/SiGe)
   secondary; proprietary PDKs are detect-only.
4. **RF granularity** — one `rf-design` + one `em-modeling` plugin; RF is not
   split further.
5. **Behavioral-modeling languages** — Verilog-A/AMS (OpenVAF/OSDI) first, with
   SystemVerilog RNM and VHDL-AMS also covered in the `behavioral-modeling` skill.
6. **License & metadata** — MIT, with the `chuanseng-ng`
   `author`/`homepage`/`repository` convention across every `plugin.json`.
7. **IDE export targets** — all four kept (Copilot / Gemini / OpenCode / Codex),
   generated under `ides/` by `tools/export_ides.py`.

---

## Appendix A — Tool master list (open-source vs proprietary)

| Flow stage | Open-source | Proprietary (detect-only) |
|---|---|---|
| Schematic capture | xschem, Qucs-S, KLayout, Hdl21/BAG | Virtuoso, Custom Compiler, Tanner S-Edit, Silvaco |
| SPICE simulation | ngspice, Xyce, gnucap, Qucs-S, PySpice | Spectre/X/APS, HSPICE, PrimeSim, FineSim, AFS, Eldo, SmartSpice, ALPS |
| Verilog-A/AMS | OpenVAF, ADMS, ngspice/Xyce OSDI | AMS Designer, Xcelium AMS, Spectre Verilog-A, VCS-AMS, Symphony |
| RNM / co-sim | cocotb, Verilator, Icarus | Xcelium AMS, VCS-AMS/CustomSim, Symphony |
| Layout | Magic, KLayout, gdstk/gdsfactory, ALIGN, MAGICAL, BAG | Virtuoso Layout, Custom Compiler, Tanner L-Edit |
| DRC / LVS | Magic + Netgen, KLayout | Calibre, IC Validator, Pegasus, Assura, Guardian |
| Extraction (PEX) | Magic ext, KLayout, FastCap, FastHenry | StarRC, Quantus QRC, Calibre xRC/xACT, Clever |
| Reliability (EM/IR/ESD) | (limited; ngspice/KLayout scripts) | Voltus, RedHawk/Totem, Calibre PERC, PathFinder, Legato, Magwel |
| Characterization (.lib) | custom ngspice harnesses + Python | Liberate, SiliconSmart, Solido ML Char, Altos |
| RF circuit | Qucs-S, Xyce HB, scikit-rf, ngspice | Spectre RF, ADS, AWR Microwave Office, GoldenGate, HSPICE-RF |
| EM solving | openEMS, FastHenry/FastCap, gmsh, scikit-rf | HFSS, Momentum/RFPro, EMX, Sonnet, AXIEM/Analyst, SIwave, RaptorX |
| PDKs | sky130, gf180mcu, ihp-sg13g2 (open_pdks) | TSMC, GF, Samsung, UMC (NDA, detect-only) |

---

*Mirrors the structure, conventions, and file formats of
`digital-chip-design-agents`, re-targeting every domain to the analog/mixed-signal
+ RF design flow. All 16 plugins and Phases 0–7 are implemented — see
[`CHANGELOG.md`](CHANGELOG.md) for delivery history and
[`FUTURE_WORK.md`](FUTURE_WORK.md) for deferred enhancements.*
