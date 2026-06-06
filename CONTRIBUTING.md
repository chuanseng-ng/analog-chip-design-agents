# Contributing to analog-chip-design-agents

All 16 plugins are implemented — the phased build in [`PLAN.md` §12](docs/PLAN.md) is
complete. Contributions now extend existing domains (new stage rules, QoR metrics,
loop-backs) or broaden tool/PDK coverage. Follow the standards below so CI
(`validate.yml`) stays green.

## Skill File Standards

Every `plugins/<domain>/skills/<skill>/SKILL.md` must have YAML frontmatter and the
four required sections (the CI greps for these exact substrings):

```markdown
---                          ← YAML frontmatter (required)
name: skill-name
description: >
  One-sentence description for Claude Code's skill discovery.
version: x.y.z
author: chuanseng-ng
license: MIT
allowed-tools: Read, Write, Bash
---

# Skill: Domain Name

## Purpose
One paragraph — what this skill enables Claude to do.

## Supported EDA Tools         ← Open-Source and Proprietary (detect-only) subsections

## Stage: stage_name           ← repeat per stage once fleshed out

### Domain Rules               ← numbered, specific rules (satisfies '## Domain Rules')
### QoR Metrics to Evaluate    ← measurable pass/fail with units (satisfies '## QoR Metrics')
### Common Issues & Fixes      ← table: Issue | Fix
### Output Required            ← artifacts the stage must produce
```

A template lives at [`docs/templates/SKILL.template.md`](docs/templates/SKILL.template.md).

## Orchestrator Standards

Every `plugins/<domain>/agents/<domain>-orchestrator.md` must have frontmatter with
`name`, `description`, `model`, `effort`, `maxTurns`, `skills`, plus `## Stage Sequence`
and `## Loop-Back Rules` sections. Template:
[`docs/templates/orchestrator.template.md`](docs/templates/orchestrator.template.md).

Skill references in the `skills:` list use the **marketplace** name as prefix:
`analog-chip-design-agents:<skill-folder>`.

## Adding / Implementing a Plugin

1. Create `plugins/<domain>/skills/<skill>/SKILL.md` and
   `plugins/<domain>/agents/<domain>-orchestrator.md` from the templates.
2. Add `plugins/<domain>/.claude-plugin/plugin.json` (template:
   [`docs/templates/plugin.template.json`](docs/templates/plugin.template.json)).
3. Register the plugin in `.claude-plugin/marketplace.json`.
4. Keep counts consistent: **agents == marketplace entries == 16**; skills ≥ 16.
5. Run validation locally (see below) and open a PR — `validate.yml` must pass.

## Shared metadata in plugin.json

Each `plugins/<domain>/.claude-plugin/plugin.json` repeats the same `author`,
`homepage`, `repository`, and `license` — the installer reads each manifest in
isolation. Canonical values:

```json
"author":     { "name": "chuanseng-ng", "url": "https://github.com/chuanseng-ng" },
"homepage":   "https://github.com/chuanseng-ng/analog-chip-design-agents",
"repository": "https://github.com/chuanseng-ng/analog-chip-design-agents",
"license":    "MIT"
```

When updating these, change all 16 `plugin.json` files and `marketplace.json` together.

## Local Validation

```bash
python3 - << 'PY'
import json, glob
skills = glob.glob("plugins/*/skills/*/SKILL.md")
agents = glob.glob("plugins/*/agents/*.md")
mp = json.load(open(".claude-plugin/marketplace.json"))["plugins"]
print("skills", len(skills), "agents", len(agents), "marketplace", len(mp))
assert len(agents) == len(mp) == 16
for p in skills:
    c = open(p).read()
    assert c.startswith("---"), p
    for s in ["## Purpose", "## Domain Rules", "## QoR Metrics", "## Output Required"]:
        assert s in c, f"{p}: missing {s}"
print("OK")
PY
```

## Pull Request Checklist

- [ ] SKILL.md has frontmatter + the four required sections
- [ ] Orchestrator has frontmatter (`model`/`effort`/`maxTurns`/`skills`) + `## Stage Sequence` + `## Loop-Back Rules`
- [ ] `plugin.json` + `marketplace.json` updated together
- [ ] Counts consistent (agents == marketplace == 16; skills ≥ 16)
- [ ] Local validation passes
- [ ] Open-source **and** proprietary tools listed where applicable (proprietary = detect-only)

## Versioning

- `PATCH` (x.x.1) — fixes or clarifications within existing skills
- `MINOR` (x.1.0) — new domain rules / a phase completed for a domain
- `MAJOR` (x.0.0) — breaking change to frontmatter schema or stage interface
