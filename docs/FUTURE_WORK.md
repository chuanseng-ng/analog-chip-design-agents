# Future Work

Deferred enhancements for `analog-chip-design-agents`. Items here are intentionally
**not** fully implemented yet; each notes the trade-off and the trigger for adopting it.

> **Recently completed** (now part of the shipped repo — see [`CHANGELOG.md`](CHANGELOG.md)
> for details, not re-narrated here): the **Phase 7 RF/EM cross-domain `fix_request`
> loop** (`rf-design` producer → `circuit-design` / `em-modeling` servicer →
> `rf-design` re-validation), the **end-to-end validation harness**
> ([`tests/e2e/run_pipeline.py`](../tests/e2e/run_pipeline.py) + [`tests/test_e2e.py`](../tests/test_e2e.py)
> over the `ldo_pm` / `lna_nf` reference designs), and all of **Phase 6**
> (`ams-integration`, `ides/` export, installers, `qor_trends.py`, release workflow).

---

## Deeper tool / PDK coverage (partially implemented)

**Status:** in progress. The coverage boundary is documented in
[`pdk_support.md`](pdk_support.md), and the **ngspice** path is exercised for
real: a PDK-independent deck (`examples/designs/ldo_pm/smoke/divider.sp`) runs through
`plugins/infrastructure/tools/wrap-ngspice.sh` in `tests/test_tool_smoke.py` (skipped where
the binary is absent, so CI stays green). All other tools remain **detect-only** and the
validated open PDK set is still `sky130` / `gf180mcu` / `ihp-sg13g2`.

### The remaining work
Promote more wrappers from *detect-only* to *smoke* (Xyce, Magic, KLayout, Netgen, OpenVAF,
openEMS), drive at least one full open-source flow in-loop, and add/validate additional open
PDKs beyond the current three. The "Adding coverage" recipe in `pdk_support.md` is the
entry point.

### Trade-offs
- **For:** moves the marketplace from "knows the flow" toward "runs the flow" on open tooling;
  lets a real silicon run close in-loop.
- **Against:** heavy environment/tooling dependencies and PDK-specific quirks; CI cost and
  flakiness risk if real tools are invoked in the pipeline.

### Trigger for adopting it
Pick this up when a real design needs a specific open tool/PDK closed in-loop, or when there
is appetite to maintain tool-execution CI alongside the spec validation.

---

## Real-orchestrator end-to-end (open)

The current end-to-end harness models the meta **dispatch rules**, not the LLM orchestrators
themselves. A heavier future step would stub or invoke the real domain orchestrators end-to-end;
the deeper tool/PDK execution above is the natural place that effort would land.
