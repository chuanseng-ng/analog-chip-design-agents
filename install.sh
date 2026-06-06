#!/usr/bin/env bash
# install.sh — one-step installer for the analog-chip-design-agents marketplace.
#
# Registers this marketplace with Claude Code and installs its plugins. Plugin
# names are read from .claude-plugin/marketplace.json so the list stays in sync.
#
# Usage:
#   ./install.sh                 # register the marketplace + install all plugins
#   ./install.sh --list          # list the plugins that would be installed
#   ./install.sh PLUGIN [PLUGIN] # install only the named plugin(s)
#   ./install.sh --help
#
# Requires: the `claude` CLI on PATH, and `python3` (to parse the registry).

set -euo pipefail

REPO_SLUG="chuanseng-ng/analog-chip-design-agents"
MARKETPLACE="analog-chip-design-agents"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY="${SCRIPT_DIR}/.claude-plugin/marketplace.json"

usage() {
  sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

die() { echo "error: $*" >&2; exit 1; }

[[ -f "${REGISTRY}" ]] || die "registry not found: ${REGISTRY}"
command -v python3 >/dev/null 2>&1 || die "python3 is required to parse the registry"

list_plugins() {
  python3 - "${REGISTRY}" <<'PY'
import json, sys
with open(sys.argv[1]) as fh:
    data = json.load(fh)
for plugin in data.get("plugins", []):
    name = plugin.get("name")
    if name:
        print(name)
PY
}

case "${1:-}" in
  -h|--help)
    usage; exit 0 ;;
  --list)
    list_plugins; exit 0 ;;
esac

command -v claude >/dev/null 2>&1 || die "the 'claude' CLI was not found on PATH — install Claude Code first"

# Determine the plugin set: explicit args, or every plugin in the registry.
if [[ $# -gt 0 ]]; then
  PLUGINS=("$@")
else
  mapfile -t PLUGINS < <(list_plugins)
fi
[[ ${#PLUGINS[@]} -gt 0 ]] || die "no plugins to install"

echo "Registering marketplace '${MARKETPLACE}' (github:${REPO_SLUG})..."
claude plugin marketplace add "github:${REPO_SLUG}" || \
  echo "note: marketplace add returned non-zero (it may already be registered) — continuing"

failed=()
for plugin in "${PLUGINS[@]}"; do
  echo "Installing ${plugin}@${MARKETPLACE}..."
  if ! claude plugin install "${plugin}@${MARKETPLACE}"; then
    echo "  ! failed to install ${plugin}" >&2
    failed+=("${plugin}")
  fi
done

echo
if [[ ${#failed[@]} -eq 0 ]]; then
  echo "Done — installed ${#PLUGINS[@]} plugin(s) from ${MARKETPLACE}."
else
  echo "Completed with ${#failed[@]} failure(s): ${failed[*]}" >&2
  exit 1
fi
