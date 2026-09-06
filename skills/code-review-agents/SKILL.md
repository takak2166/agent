---
name: code-review-agents
description: Runs a multi-perspective code review by launching 8 specialist analysis subagents in parallel (language spec, refactoring, DDD, clean architecture, security, performance, TDD, observability) plus 1 integration subagent that deduplicates, prioritizes, and reports their findings.
disable-model-invocation: true
---

# Code Review Agents

Orchestrate 8 specialist analysis subagents (parallel), then 1 integration subagent (sequential). Produce review text only.

## Restrictions

These bullets govern the orchestrator (you):

- Do not modify any file — this skill produces review output only.
- Do not post review comments to GitHub (use `reply-pr-comment` for that).
- Limit shell use to `gh pr diff`, `git diff`, `git log`, `git branch`, `git branch --list`, and `git status --porcelain`. Inspect the workspace with `Read`, `Glob`, and `Grep` only (no `ls`, `cat`, `find`, or similar).
- Do not create git commits.

Subagents carry their own constraints: copy **Shared: Restrictions** from [agent-prompts.md](agent-prompts.md) verbatim as the first block of every analysis and integration `Task` prompt. Never substitute the bullets above into a `Task` prompt, and never merge the two blocks.

## Before launching subagents

Confirm all four:

- [ ] Code Context block for the current round is complete — Changed Files + optional Project Notes + Diff + File Contents (Step 4)
- [ ] [agent-prompts.md](agent-prompts.md) read (Step 3)
- [ ] All 8 analysis `Task` calls go out in a single message (Step 5)
- [ ] Every `Task` prompt starts with **Shared: Restrictions**

## Usage

```
/code-review-agents [PR number | base branch]
```

| Argument | Review target |
|----------|---------------|
| Bare integer (e.g. `42`) | PR diff — `gh pr diff 42` |
| Branch name (e.g. `main`) | Committed diff — `git diff main...HEAD` |
| None | Staged changes — `git diff --staged`; only when that output is empty, `git diff HEAD` for unstaged changes to tracked files |

## Steps

1. **Determine the review target** — run the command for the resolved argument per the table above, then collect the changed files with a one-line summary each (`hunks:<N>, +<A>/-<D>`). In the **no-argument flow**, run `git diff --staged` first, run `git diff HEAD` only when staged output is empty, then run `git status --porcelain` — never run porcelain before the staged/HEAD diff sequence. Run only the commands named in the table and in **Restrictions**: use `git status --porcelain` for working-tree state, not bare `git status` or `git diff --stat`. When the resolved diff has no changed files, tell the user there is nothing to review and stop — never launch subagents on an empty diff. For number-vs-branch ambiguity, untracked files, empty-diff reporting, or unavailable `gh`, follow [reference.md](reference.md) **Target resolution**.

2. **Gather full context** — `Read` each changed file in full (not only the diff hunk), detect the primary language(s) from file extensions, and optionally `Glob` relevant directories to understand project structure. When the diff is large, group files into rounds before reading (see [reference.md](reference.md) **Context budget and rounds**).

3. **Read the prompt templates** — read [agent-prompts.md](agent-prompts.md) for the shared blocks and per-agent sections.

4. **Build the shared Code Context block** — assemble this text once per round and embed it in every analysis prompt:

   ```
   ## Changed Files
   <changed files, one line of summary each>

   ## Project Notes
   <optional: structure facts from Step 2 that change how findings should be read, e.g. "no test directory exists">

   ## Diff
   <diff for the files in this round>

   ## File Contents
   <full content of each file in this round, labeled by path>
   ```

   Keep each round's Code Context under ~50 000 characters; the same block is duplicated into 8 prompts, so split at ~35–40k when close to the limit. Grouping, merging, and per-round rules: [reference.md](reference.md) **Context budget and rounds**.

5. **Launch the 8 analysis subagents in parallel** — issue 8 `Task` calls in one assistant message so they run concurrently:

   | Parameter | Value |
   |-----------|-------|
   | `subagent_type` | `"generalPurpose"` |
   | `description` | Short label, e.g. `"Review: Security"` |
   | `prompt` | **Shared: Restrictions** + **Shared: Finding Format** + the agent's section from [agent-prompts.md](agent-prompts.md) + the Code Context block (see **How to construct prompts** there) |

6. **Collect results** — wait for all 8 to return. When a subagent times out or returns empty or unusable output, tell the user and retry that one subagent once with the same prompt; do not retry a second time, and do not retry a subagent that returned a usable report. Then proceed with the available outputs and instruct the integration subagent to record the gap.

7. **Launch the integration subagent** — issue a single `Task` call:

   | Parameter | Value |
   |-----------|-------|
   | `subagent_type` | `"generalPurpose"` |
   | `description` | `"Integrate review findings"` |
   | `prompt` | **Shared: Restrictions** + **Shared: Final Report Format** + the Agent 9 section from [agent-prompts.md](agent-prompts.md) + all available specialist outputs |

8. **Present the final review** — show the integration subagent's report, then offer to drill down into any area.

## Agent roster

| # | Agent | Focus area |
|---|-------|------------|
| 1 | Language Spec | Type safety, idioms, API misuse, deprecation |
| 2 | Refactoring & Patterns | Code smells, SOLID, Martin Fowler's refactoring catalog |
| 3 | DDD | Ubiquitous language, aggregates, value objects, bounded contexts |
| 4 | Clean Architecture | Layer boundaries, dependency rule, use case isolation |
| 5 | Security | OWASP Top 10, injection, auth, secrets, input validation |
| 6 | Performance | Complexity, N+1, memory, I/O, caching |
| 7 | TDD | t-wada's principles, test reliability, coverage, testability |
| 8 | Observability | Logging, metrics, tracing, error handling, operability |
| 9 | Integration | Synthesis, deduplication, prioritization, final report |

## Where formats live

[agent-prompts.md](agent-prompts.md) is the single source of truth for prompt blocks and output templates. Copy each block verbatim; when changing a format, edit that file only.

| Block | Goes into |
|-------|-----------|
| **Shared: Restrictions** | First block of every analysis and integration prompt |
| **Shared: Finding Format** | Each analysis prompt (structure + severity table) |
| **Shared: Final Report Format** | The integration prompt |

## Notes

- **Output language**: match the user's preference (default: 日本語).
- **Codebase exploration**: analysis subagents may `Read` / `Grep` surrounding code for context beyond the diff.
- **Model choice**: omit the `model` parameter so subagents inherit the parent model; if choosing a faster model instead, use `model: "composer-2.5-fast"` on all `Task` calls consistently.
