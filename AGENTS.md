# Agent Guidelines

<!-- Do not restructure or delete sections. Update individual values in-place when they change. -->

## Project Overview

**Project type:** Personal APM package of agent skills and always-on instruction primitives.
**Primary language:** Markdown and YAML (no application runtime).
**Key dependencies:** [APM](https://microsoft.github.io/apm/) via root `apm.yml`. Skills are separate dependency paths (`takak2166/agent/skills/<name>`).

---

## Commands

```bash
# Install this package's rules into a consumer repo
apm install takak2166/agent

# Install one skill (example)
apm install takak2166/agent/skills/draft-pr

# User-wide install
apm install -g takak2166/agent

# Docs
# README.md — layout and consumer install; skill list in apm.yml.example
```

---

## Code Conventions

- Follow the existing patterns in the codebase
- Prefer explicit over clever
- Delete dead code immediately
- One skill per directory: `skills/<name>/SKILL.md`. Workflows stay in skills; always-on policy stays in `.apm/instructions/`.
- Install rules from the repo-root package (`takak2166/agent`), not from a `skills/…` path.

---

## Architecture

```
skills/                Agent Skills (`SKILL.md`, optional `reference/`)
.apm/instructions/     APM instruction primitives; deploy to consumer rules on `apm install`
```
