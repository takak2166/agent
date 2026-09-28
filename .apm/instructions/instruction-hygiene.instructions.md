---
description: When editing agent instructions, keep only what the session cannot derive from code
applyTo: "**/CLAUDE.md,**/AGENTS.md,**/SKILL.md,**/.apm/instructions/**,**/.claude/rules/**,**/.cursor/rules/**"
---

# Agent instruction hygiene

When writing or editing agent instructions:

- Remove what a session can derive from the code: directory layout, dependency lists, standard install/test/lint commands, generic advice, and rules a linter already enforces.
- Keep pitfalls, design rationale, conventions that differ from tool defaults, safety prohibitions, commands that cannot be inferred, and external references. If unsure, keep it.
- Always-on instructions hold cross-cutting invariants only. Put workflows and long procedures in a skill. Keep "never do X" prohibitions always-on.
- State each fact in one place. Skip history narrative, incident IDs, and pinned model names.
- Do not turn one session's stumble into a permanent rule.
