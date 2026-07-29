---
description: Do not embed issue tracker IDs in repository source or docs
applyTo: "**/*"
---

# No issue tracker IDs in code

Do not put Linear / Jira / GitHub issue IDs (e.g. `ABC-123`, `PROJ-456`) in:

- Source code, comments, or string literals
- Package docs and README content under version control
- Config comments (`rules.yaml`, hook JSON comments, etc.)

Link tickets in PR descriptions, commit messages, or Linear comments instead.

Exception: skill / instruction examples that teach how to *handle* ticket IDs (e.g. Linear MCP workflows) may mention sample IDs.
