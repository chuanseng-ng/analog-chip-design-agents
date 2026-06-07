# PDK & tool coverage

This page tracks how far each PDK and EDA tool is exercised by the marketplace, so the
"detect-only vs run-in-loop" boundary is explicit. It complements the per-domain
`## Supported Tools` sections in each `plugins/<domain>/skills/<skill>/SKILL.md`.

## Coverage levels

| Level | Meaning |
|-------|---------|
| **run-in-loop** | The tool is invoked through an infrastructure wrapper and its output is parsed back into `design_state`. |
| **smoke** | Exercised by a real but minimal run in the test suite (skipped when the binary is absent). |
| **detect-only** | The infrastructure domain detects/wraps it and the SKILLs describe its use, but it is not executed in CI. |

## Open PDKs

| PDK | Status | Notes |
|-----|--------|-------|
| `sky130` | validated (detect-only) | SkyWater 130 nm; primary open analog target across the SKILLs. |
| `gf180mcu` | validated (detect-only) | GlobalFoundries 180 nm MCU. |
| `ihp-sg13g2` | validated (detect-only) | IHP SiGe BiCMOS 130 nm; the RF/EM tier's open SiGe target. |

"Validated" here means the PDK name is wired consistently through the SKILL `Supported Tools`
sections and the `constraints.pdk` field. None of the three is exercised by a real tape-out flow
in CI yet (see [`FUTURE_WORK.md`](FUTURE_WORK.md) → *Deeper tool / PDK coverage*).

## Predictive / academic PDKs

These are wired by name exactly like the open PDKs above, but they are **predictive,
educational, and non-manufacturable**: they carry no silicon-proven status, ship little or
no foundry corner/statistical data, and are **not** distributed via `open_pdks` (each comes
from its own academic distribution). Treat them as targets for topology, methodology, and
flow exploration — **not** for tape-out QoR or trustworthy PEX/EM/reliability numbers.

| PDK | Status | Notes |
|-----|--------|-------|
| `freepdk45` | predictive (detect-only) | NCSU 45 nm planar bulk CMOS; academic/non-manufacturable. BSIM4, typical-corner-oriented models; install from the FreePDK distribution, not `open_pdks`. |
| `asap7` | predictive (detect-only) | ASU/ARM 7 nm FinFET; academic/non-manufacturable. BSIM-CMG, quantized fin widths, multi-Vt, multi-patterning DRC; no statistical/MC data. Install from the ASAP7 repo, not `open_pdks`. |

Neither is an RF/EM target (no HBTs, no characterized thick-metal passive stack) — keep
`ihp-sg13g2` for true RF/EM blocks.

## Open-source tools

| Tool | Wrapper | Status |
|------|---------|--------|
| ngspice | `plugins/infrastructure/tools/wrap-ngspice.sh` | **smoke** — `tests/test_tool_smoke.py` runs a PDK-independent divider deck (`examples/designs/ldo_pm/smoke/divider.sp`) when ngspice is installed. |
| Xyce | `wrap-xyce.sh` | detect-only |
| Magic | `wrap-magic.sh` | detect-only |
| KLayout | `wrap-klayout.sh` | detect-only |
| Netgen | `wrap-netgen.sh` | detect-only |
| OpenVAF | `wrap-openvaf.sh` | detect-only |
| openEMS | `wrap-openems.sh` | detect-only |

All wrappers emit a compact JSON summary (status / measures / errors / warnings) rather than raw
logs, so a future in-loop driver can parse them uniformly — the ngspice smoke test demonstrates that
contract end-to-end.

## Adding coverage

To promote a tool from *detect-only* to *smoke*:
1. Add a minimal, PDK-independent input deck under `examples/designs/<design>/smoke/`.
2. Add a `@pytest.mark.skipif(shutil.which("<tool>") is None, ...)` test in
   `tests/test_tool_smoke.py` that runs it through its `wrap-*.sh` and asserts the parsed JSON.
3. Update the table above.

To add a PDK: wire its name into the relevant SKILL `Supported Tools` sections and confirm it is an
acceptable `constraints.pdk` value, then add a row above.
