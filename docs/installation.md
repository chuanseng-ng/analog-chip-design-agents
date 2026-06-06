# Installation

All 16 plugins are fully implemented. Pick the path that matches your setup —
most users want **Option A** (npm) or **Option B** (install script).

## Option A — npm (recommended, no clone)

If you have Node.js (≥18), run a single command — no `git clone` and no Python
required. With no flags the installer **detects which AI coding agents you have
installed** (Claude Code, OpenAI Codex, OpenCode, Gemini, GitHub Copilot), shows
what it found and where each would write, and installs to them after a
confirmation:

```bash
npx analog-chip-design-agents            # detect installed agents + confirm
npx analog-chip-design-agents --yes      # detect + install, no prompt (CI-friendly)
```

Detection treats an agent as installed if its CLI is on `PATH` **or** its config
directory exists (e.g. `~/.claude`, `~/.codex`, `~/.config/opencode`,
`~/.gemini`). For Claude Code it copies every plugin into your plugin cache and
enables them in `settings.json`; for the others it generates the matching context
files (see Option D). All five targets are handled natively in Node — no Python.

To target a specific agent (or all of them) explicitly and skip detection:

```bash
npx analog-chip-design-agents --ide claude     # or codex | opencode | gemini | copilot | all
npx analog-chip-design-agents --ide gemini --global
```

Re-run any of these to pick up future updates. Works identically on macOS, Linux,
and Windows (a single Node process copies plugins sequentially, so there is no
concurrent-write contention on the cache directory).

## Option B — Install script

Clone the repo and run one script. Like the npm installer, running it with no
flags **auto-detects your installed agents** and installs to them after a
confirmation (add `--yes` / `-y` on `install.sh`, or `-Yes` on `install.ps1`, to
skip the prompt). The shell scripts require `python3`; for a Python-free install
use the npm path (Option A).

```bash
bash install.sh          # macOS / Linux / Git Bash
```

```powershell
.\install.ps1            # Windows / PowerShell
```

## Option C — Marketplace (selective install)

If you only need specific domains, install them from inside Claude Code:

```text
/plugin marketplace add github:chuanseng-ng/analog-chip-design-agents
/plugin install analog-design-circuit@analog-chip-design-agents
/plugin install analog-design-simulation@analog-chip-design-agents
```

## Option D — Other AI assistants (Copilot / Gemini / OpenCode / Codex CLI)

These targets are auto-detected by Options A and B, but you can also install one
explicitly. The npm installer and the shell scripts both support every target
natively; run from your analog design project directory with `--ide`:

```bash
npx analog-chip-design-agents --ide copilot    # .github/instructions/ in your project
npx analog-chip-design-agents --ide gemini     # GEMINI.md (or ~/GEMINI.md with --global)
npx analog-chip-design-agents --ide opencode   # opencode.json; use /mode analog-<domain>
npx analog-chip-design-agents --ide codex      # AGENTS.md (or ~/.codex/instructions.md with --global)
```

Domain knowledge is loaded from the plugin SKILLs at install time — `plugins/`
stays the single source of truth, and the `ides/` templates supply each
assistant's header/glob configuration. Re-run to pick up updates.

## QoR trends

Track analog/RF QoR across runs from the per-domain memory logs:

```bash
python3 tools/qor_trends.py --design my_ldo            # trend + regression alerts
python3 tools/qor_trends.py --design my_lna --group-by pdk --format csv
```
