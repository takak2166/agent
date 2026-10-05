---
description: Protect the agent context window by filtering verbose logs and scoping exploration
applyTo: "**/*"
---

# Guard the Context Window

- **Value-to-cost ratio**: Only bring information into the main conversation that directly informs the next decision. Filling context with raw, uncurated data degrades reasoning quality.
- **No verbose log dumps**: Never paste full test outputs, lengthy build logs, or entire documentation chapters into the conversation. Summarize outcomes and cite relevant file paths and line numbers.
- **Filter and scope reads**: Use targeted tools (e.g. filtered `rg`/`grep`, `jq`, line-range reads) or scoped subagents when exploring large files or broad datasets, returning only concise findings.
- **Keep decisions audit-friendly**: Record the essential command, exit code, and key output snippet needed to justify the next action without cluttering the transcript.
