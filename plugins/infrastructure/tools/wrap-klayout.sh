#!/usr/bin/env bash
# wrap-klayout.sh — run KLayout (DRC/LVS, batch) and emit a compact JSON summary
set -euo pipefail
TOOL="klayout"

if ! command -v "$TOOL" &>/dev/null; then
  python3 - <<'PYEOF'
import json
print(json.dumps({"tool":"klayout","exit_code":1,"status":"FAIL","summary":{},"errors":["tool not found: klayout"],"warnings":[],"raw_log":""}))
PYEOF
  exit 1
fi

LOG=$(mktemp /tmp/klayout-XXXXXX.log)
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
viol_m = re.search(r'(\d+)\s+(?:DRC\s+)?violations?', text, re.I)
viol = int(viol_m.group(1)) if viol_m else None
lvs_ok = bool(re.search(r'\bLVS\b.*\b(match|clean|equivalent)\b', text, re.I))
summary = {"violations": viol, "lvs_match": lvs_ok if "LVS" in text.upper() else None,
           "error_count": len(errors), "warning_count": len(warnings)}
status = "FAIL" if exit_code != 0 or errors or (viol and viol > 0) else ("WARN" if warnings else "PASS")
print(json.dumps({"tool":"klayout","exit_code":exit_code,"status":status,"summary":summary,
                  "errors":errors[:10],"warnings":warnings[:10],"raw_log":log_path}, indent=2))
PYEOF
exit $EXIT_CODE
