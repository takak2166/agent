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
- For skills and instructions, inline short templates or references used on every invocation into the main file rather than forcing extra file reads.

## Encode lessons in structure

When a recurring mistake or correction emerges:
- Prefer structural enforcement over prose instructions whenever an automated mechanism can fail the build or enforce correctness:
  1. **Type system**: make invalid states unrepresentable
  2. **Linter / CI checks**: fail on banned APIs or prohibited patterns
  3. **Canonical helper**: provide a single shared implementation
  4. **Runtime assertion**: validate at system boundaries
- Only keep instructions purely as text when automated evaluation is impossible (e.g. design judgment, subjective quality). In those cases, provide a clear negative example.
