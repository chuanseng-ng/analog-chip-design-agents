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
