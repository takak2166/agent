---
description: Proceed autonomously on reversible workspace edits; block on destructive or external actions
applyTo: "**/*"
---

# Asynchronous Supervision: Proceed, then Present

- **The user supervises asynchronously**: Agents must stay unblocked. Do not stop to ask "May I do X?" for routine, reversible workspace operations.
- **Proceed, then present**: For reversible actions (editing files, refactoring, adding tests, running local read-only commands or tests), make the best technical decision, execute it, and present the result with rationale.
- **Stop and confirm before destructive or external operations**:
  - Discarding uncommitted or untracked user work (e.g. `git reset --hard`, `git clean -fdx`, deleting non-ephemeral files)
  - Pushing to remote repositories, deleting remote branches/tags, or merging PRs
  - Deploying to shared/production environments or destructive data operations (dropping tables/databases)
  - Modifying secrets, credentials, or billing-sensitive resources
  - Sending messages or updates visible outside the local workspace (e.g. customer-facing communication, external tickets, third-party APIs)
- **Explicit request or skill exception**: An explicit user instruction or an invoked skill step that specifically prescribes the action counts as confirmation (do not re-prompt).
- **Ambiguity vs permission**: Never stop to ask permission for reversible work, but when user requirements or architecture choices are fundamentally ambiguous with significant trade-offs, clarify intent before implementing.
- **Observe, do not ask**: Never ask the user for facts that can be resolved via read-only inspection (reading code, running non-destructive checks, inspecting environment).
