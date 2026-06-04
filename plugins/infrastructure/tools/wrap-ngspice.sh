#!/usr/bin/env bash
# wrap-ngspice.sh — run ngspice in batch mode and emit a compact JSON summary
set -euo pipefail
TOOL="ngspice"

if ! command -v "$TOOL" &>/dev/null; then
  python3 - <<'PYEOF'
import json
print(json.dumps({"tool":"ngspice","exit_code":1,"status":"FAIL","summary":{},"errors":["tool not found: ngspice"],"warnings":[],"raw_log":""}))
PYEOF
  exit 1
fi

LOG=$(mktemp /tmp/ngspice-XXXXXX.log)
set +e
"$TOOL" "$@" >"$LOG" 2>&1
EXIT_CODE=$?
set -e

python3 - "$LOG" "$EXIT_CODE" <<'PYEOF'
import json, re, sys
log_path, exit_code = sys.argv[1], int(sys.argv[2])
with open(log_path, encoding='utf-8', errors='replace') as f:
    text = f.read()

errors   = [l.strip() for l in text.splitlines() if re.search(r'\b(error|fatal|aborted)\b', l, re.I)]
warnings = [l.strip() for l in text.splitlines() if re.search(r'\bwarning\b', l, re.I)]
nonconv  = bool(re.search(r'(no convergence|singular matrix|iteration limit)', text, re.I))

# Capture ngspice .measure results:  "<name> = <value>"
measures = {}
for m in re.finditer(r'^\s*([a-zA-Z_]\w*)\s*=\s*([-+]?[\d.eE]+)', text, re.M):
    measures[m.group(1)] = float(m.group(2))

summary = {"measures": measures, "convergence": (not nonconv),
           "error_count": len(errors), "warning_count": len(warnings)}
status = "FAIL" if exit_code != 0 or errors or nonconv else ("WARN" if warnings else "PASS")
print(json.dumps({"tool":"ngspice","exit_code":exit_code,"status":status,"summary":summary,
                  "errors":errors[:10],"warnings":warnings[:10],"raw_log":log_path}, indent=2))
PYEOF
exit $EXIT_CODE
