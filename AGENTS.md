# Agent Guidelines

<!-- Lean context: only what shared rules and the codebase cannot supply. Update in-place; do not sprawl. -->

## Project-specific context

Personal APM package: agent skills under `skills/` plus always-on instruction primitives under `.apm/instructions/`, consumed in other repos via `apm install`.

---

## Commands (non-default only)

```bash
# Install this package's rules into a consumer repo
apm install takak2166/agent

# Install one skill (example)
apm install takak2166/agent/skills/draft-pr

# User-wide install
apm install -g takak2166/agent

# Docs: README.md — layout and consumer install; skill list in apm.yml.example
```

---

## Conventions & gotchas

- One skill per directory: `skills/<name>/SKILL.md`. Workflows stay in skills; always-on policy stays in `.apm/instructions/`.
- Install rules from the repo-root package (`takak2166/agent`), not from a `skills/…` path.

---

## Layout notes (optional)

```
skills/                Agent Skills (`SKILL.md`, optional `reference/`)
.apm/instructions/     APM instruction primitives; deploy to consumer rules on `apm install`
```
