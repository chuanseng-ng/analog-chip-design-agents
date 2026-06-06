# ides/ — multi-assistant install templates

These files are **templates** the installer (`bin/install.mjs`, `install.sh`,
`install.ps1`) reads to generate assistant-native context files at install time
from the `plugins/` SKILLs. The **source of truth is each domain's
`plugins/<domain>/skills/<skill>/SKILL.md`** — the installer inlines or references
those at install time, so there is no committed generated copy to keep in sync.

| Assistant | Template(s) | Generated output |
|-----------|-------------|------------------|
| GitHub Copilot | `copilot/.github/copilot-instructions.md` (workspace header) + `copilot/applyto-map.json` (domain → file globs) | `.github/copilot-instructions.md` + `.github/instructions/<domain>.instructions.md` |
| Gemini | `gemini/gemini-header.md` (preamble) | `GEMINI.md` (with `@`-imports to SKILL/agent files) |
| OpenCode | `opencode/opencode-base.json` (base config) | `opencode.json` (one `mode` per domain, `{file:...}` prompts) |
| Codex | `codex/AGENTS.md` (preamble) | `AGENTS.md` (SKILL bodies inlined) |

Install (auto-detect, or target one assistant explicitly):

```bash
npx analog-chip-design-agents                  # detect installed agents + confirm
npx analog-chip-design-agents --ide gemini     # or copilot | opencode | codex | claude | all
```
