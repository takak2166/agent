---
description: Prefer documented repo rules; use existing code patterns as reference, not automatic adoption
applyTo: "**/*"
---

# Code Pattern Analysis

- Documented project rules take precedence over observed code patterns (style guides, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING`, linter/formatter configs, and other repo guidelines)
- Before implementing new code, search for similar patterns in the existing codebase
- Treat existing patterns as reference for comparison—not automatic adoption
- Follow an existing pattern only when it does not conflict with documented rules and is a good fit (consistency, testability, alignment with existing abstractions)
- When documented rules and existing code conflict, follow the documented rules; prefer not extending the outdated pattern (fix it when in scope), and briefly note the conflict
- Explain existing approaches and their trade-offs, then choose based on those trade-offs—not status quo by default
- If creating a new pattern, explain why it's necessary and how it fits with the overall architecture
