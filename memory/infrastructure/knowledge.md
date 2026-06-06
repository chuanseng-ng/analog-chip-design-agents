# Infrastructure — Distilled Knowledge (Tier 2)

Seeded known setup quirks and version-mismatch patterns. Infrastructure memory is
**opt-in and environment-keyed** — prefer entries whose environment fingerprint matches the
current host (versions and quirks do not transfer across machines). Distilled by
`/analog-design-infrastructure:memory-keeper --domain infrastructure`.

## Known Env-Mismatch Failure Patterns

| Pattern | Fix |
|---------|-----|
| `ngspice` < 38 cannot load OSDI Verilog-A models | Build/install ngspice ≥ 38 with `--enable-osdi`; OpenVAF emits OSDI |
| OpenVAF/OSDI ABI mismatch with installed ngspice | Recompile the `.osdi` with the OpenVAF release matching the ngspice OSDI ABI |
| `magic`/`netgen` not finding the PDK tech | Export `PDK_ROOT` and `PDK`; source the open_pdks-generated setup before launch |
| KLayout DRC script API drift across 0.27/0.28 | Pin the KLayout version per project; the DRC deck targets a specific API |
| `python3` resolves to system but PySpice installed under a venv/module | Detect `python_env`; use `"$PYTHON_EXEC" -m pip` — never bare `pip` for custom/module Python |
| Proprietary tool in PATH but license unavailable | Detect-only; do not block the flow — fall back to the open-source tool for that stage |

## Successful Flags / Install Notes

- open_pdks: install `sky130`, `gf180mcu`, `ihp-sg13g2` with `--enable-...-pdk`; sets `PDK_ROOT`.
- freepdk45 / asap7: predictive academic PDKs **not** shipped by open_pdks — fetch from their own
  repos (FreePDK / ASAP7) and point `PDK_ROOT`+`PDK` (and any tech/deck paths) at the unpacked tree
  before launching Magic/KLayout.
- ngspice: `--enable-osdi --enable-xspice` for Verilog-A and mixed-signal code models.
- Xyce: build with MPI for large Monte-Carlo throughput.
- uv: prefer the standalone astral.sh installer; pip fallback only for custom/module Python.

## Tool Quirks

- `Xyce` executable is capitalised (`Xyce`), unlike most tools.
- `openEMS` solves are long — always run via Bash/MCP with `TOOL_TIMEOUT_S` raised, never inline.

## Metric Baselines

_(Populated by `memory-keeper`: `tools_detected`, `tools_missing`, `wrappers_deployed`, `mcp_servers_configured`, plus the per-tool `tool_versions` map.)_
