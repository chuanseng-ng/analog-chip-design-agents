# Architecture

## How It Works

Each plugin installs two things, exactly as in the reference repo:

1. **A Skill** (`plugins/<domain>/skills/<skill>/SKILL.md`) — domain knowledge Claude
   reads before executing: stage-by-stage rules, QoR metrics, supported open-source
   and proprietary tools, and output requirements.

2. **An Orchestrator Agent** (`plugins/<domain>/agents/<domain>-orchestrator.md`) — a
   subagent that sequences stages, enforces pass/fail criteria, applies loop-back
   rules when a stage fails, and escalates when human input is needed.

The 14 design domains map to the end-to-end analog/mixed-signal + RF pipeline
diagrammed in [`PLAN.md` §3](PLAN.md). Cross-domain feedback (e.g. a failed
Monte-Carlo run looping back to circuit design) is driven by the `meta` pipeline
orchestrator through a shared `design_state.json`
([schema](design_state_schema.md)).

## Repo Structure

```
analog-chip-design-agents/
├── .claude-plugin/marketplace.json      ← registry of all 16 plugins
├── plugins/                             ← one isolated dir per plugin
│   └── <domain>/
│       ├── .claude-plugin/plugin.json
│       ├── agents/<domain>-orchestrator.md
│       └── skills/<skill>/SKILL.md
├── bin/                                 ← npm installer (install.mjs) + agent detection (detect.mjs)
├── ides/                                ← install-time templates (Copilot/Gemini/OpenCode/Codex)
├── memory/                              ← per-domain knowledge.md + experiences.jsonl
├── tools/                               ← qor_trends.py
├── docs/
│   ├── installation.md                  ← install paths for every supported agent
│   ├── architecture.md                  ← this file
│   ├── design_state_schema.md           ← shared cross-orchestrator state schema
│   ├── pdk_support.md                   ← PDK / tool coverage matrix
│   ├── templates/                       ← SKILL / orchestrator / plugin.json templates
│   ├── PLAN.md                          ← full roadmap (domains, stages, tools, phases)
│   └── CHANGELOG.md  FUTURE_WORK.md
├── .github/workflows/                   ← validate.yml (CI) + release.yml (tagged release)
├── install.sh / install.ps1            ← one-step plugin installers
├── README.md  CONTRIBUTING.md  LICENSE
```
