# Analog Chip Design — Copilot Workspace Instructions

This workspace contains analog / mixed-signal + RF chip design work spanning 16
domains: architecture, behavioral modeling, circuit design, circuit simulation,
AMS verification, custom layout, physical verification, parasitic extraction,
post-layout sign-off, reliability, characterization, RF design, EM modeling, AMS
integration, infrastructure, and pipeline orchestration.

## Behaviour for All Domains

- Apply domain-specific QoR metrics before declaring any stage complete.
- Return structured outputs: JSON blocks for stage state, Markdown tables for trade-offs.
- Execute one stage at a time and report **PASS / FAIL / WARN** after each stage.
- Flag ambiguities before proceeding — chip design is safety-critical.
- When a stage loop limit is exceeded, escalate to the user with full state and recommendations.

## Domain-Specific Rules

Per-domain rules, QoR metrics, and stage sequences are loaded from
`.github/instructions/<domain>.instructions.md` based on the files you are working with.
These files are generated from the plugin SKILL.md sources and contain the full
domain knowledge for each analog/mixed-signal + RF design stage.
