---
description: Regenerate user-scope APM root context after global install or update
applyTo: "**/*"
---

After any manual `apm install -g` or `apm update -g`, run `apm compile -g` so user-scope root context files (for example `~/.codex/AGENTS.md`) stay current.