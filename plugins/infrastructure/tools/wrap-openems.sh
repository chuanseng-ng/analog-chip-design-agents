#!/usr/bin/env bash
# wrap-openems.sh — run an openEMS FDTD solve and emit a compact JSON summary
# openEMS solves can be long; the MCP adapter applies TOOL_TIMEOUT_S.
set -euo pipefail
TOOL="openEMS"

if ! command -v "$TOOL" &>/dev/null; then
  python3 - <<'PYEOF'
import json
print(json.dumps({"tool":"openems","exit_code":1,"status":"FAIL","summary":{},"errors":["tool not found: openEMS"],"warnings":[],"raw_log":""}))
PYEOF
  exit 1
fi

LOG=$(mktemp /tmp/openems-XXXXXX.log)
set +e
"$TOOL" "$@" >"$LOG" 2>&1
EXIT_CODE=$?
set -e

python3 - "$LOG" "$EXIT_CODE" <<'PYEOF'
import json, re, sys
log_path, exit_code = sys.argv[1], int(sys.argv[2])
with open(log_path, encoding='utf-8', errors='replace') as f:
    text = f.read()
errors   = [l.strip() for l in text.splitlines() if re.search(r'\berror\b', l, re.I)]
warnings = [l.strip() for l in text.splitlines() if re.search(r'\bwarning\b', l, re.I)]
energy_m = re.search(r'energy.*?([-+]?[\d.eE]+)\s*%', text, re.I)
ts_m = re.search(r'(\d+)\s+timesteps?', text, re.I)
summary = {"final_energy_pct": float(energy_m.group(1)) if energy_m else None,
           "timesteps": int(ts_m.group(1)) if ts_m else None,
           "error_count": len(errors), "warning_count": len(warnings)}
status = "FAIL" if exit_code != 0 or errors else ("WARN" if warnings else "PASS")
print(json.dumps({"tool":"openems","exit_code":exit_code,"status":status,"summary":summary,
                  "errors":errors[:10],"warnings":warnings[:10],"raw_log":log_path}, indent=2))
PYEOF
exit $EXIT_CODE
