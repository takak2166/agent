---
name: code-review-agents
description: Runs a multi-perspective code review via 3 sequential consolidated analysis passes (security/performance/observability; architecture/DDD/refactoring; language/TDD) plus 1 integration subagent that deduplicates, prioritizes, and reports their findings.
disable-model-invocation: true
---

# Code Review Agents

Orchestrate **3 consolidated analysis passes** (sequential — one `Task` at a time), then 1 integration subagent. Produce review text only.

## Restrictions

These bullets govern the orchestrator (you):

- Do not modify any file — this skill produces review output only.
- Do not post review comments to GitHub (use `/reply-pr-comment` for that).
- Limit shell use to `gh pr diff`, `gh pr view`, `gh issue view`, `git diff`, `git log`, `git branch`, `git branch --list`, and `git status --porcelain`. Inspect the workspace with `Read`, `Glob`, and `Grep` only (no `ls`, `cat`, `find`, or similar).
- Do not create git commits.

Subagents carry their own constraints: copy **Shared: Restrictions** from [agent-prompts.md](agent-prompts.md) verbatim as the first block of every analysis and integration `Task` prompt. Never substitute the bullets above into a `Task` prompt, and never merge the two blocks.

## Before launching analysis passes

Confirm all four before the first analysis `Task` (Step 5; Step 8 integration uses the same **Shared: Restrictions** rule separately):

- [ ] Code Context block for the current round is complete — Changed Files + Stated Intent + Diff + File Contents; add **Project Notes** only when Step 2 surfaced structure facts (Step 4)
- [ ] [agent-prompts.md](agent-prompts.md) read (Step 3)
- [ ] Launch plan ready: three analysis `Task` calls in order (Pass 1 → Pass 2 → Pass 3), each after the prior returns
- [ ] Each analysis `Task` prompt starts with **Shared: Restrictions** from [agent-prompts.md](agent-prompts.md) and includes every agent section listed for that pass in **Consolidated passes**

## Before launching the integration subagent

Confirm all three before the integration `Task` call (Step 8):

- [ ] **Stated Intent** text matches Step 4 (same across rounds)
- [ ] **Change Scope** assembled — review-wide Changed Files + full unified diff (Step 7)
- [ ] Integration `prompt` includes **Shared: Restrictions**, **Shared: Final Report Format**, Agent 9 section, **Stated Intent**, **Change Scope**, and concatenated specialist outputs

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

1. **Determine the review target** — run the command for the resolved argument per the table above, then collect the changed files with a one-line summary each (`hunks:<N>, +<A>/-<D>`). In the **no-argument flow**, run `git diff --staged` first, run `git diff HEAD` only when staged output is empty, then run `git status --porcelain` — never run porcelain before the staged/HEAD diff sequence. Run only the commands named in the table and in **Restrictions**: use `git status --porcelain` for working-tree state, not bare `git status` or `git diff --stat`. Compute each `hunks:<N>, +<A>/-<D>` summary by reading the diff text — never pipe it through `awk`, `grep`, `wc`, or similar. When staged/HEAD diffs are empty **and** porcelain shows no untracked paths to include per [reference.md](reference.md) **Untracked files**, tell the user there is nothing to review and stop — never launch subagents with zero files in scope. When diffs are empty but porcelain lists untracked paths, include those files (not an empty-diff stop). For number-vs-branch ambiguity, empty-diff reporting, or unavailable `gh`, follow [reference.md](reference.md) **Target resolution**.

2. **Gather full context** — `Read` each changed file in full (not only the diff hunk), detect the primary language(s) from file extensions, and optionally `Glob` relevant directories to understand project structure. When the review target is a PR number, also fetch **stated intent** per [reference.md](reference.md) **Stated intent** (`gh pr view`) for Step 4. When the diff is large, group files into rounds before reading (see [reference.md](reference.md) **Context budget and rounds**).

3. **Read the prompt templates** — read [agent-prompts.md](agent-prompts.md) for the shared blocks and per-agent sections.

4. **Build the shared Code Context block** — assemble this text once per round and embed it in every analysis prompt:

   ```
   ## Changed Files
   <changed files, one line of summary each>

   ## Stated Intent
   <PR title and body; linked issue title/body when available — see reference.md **Stated intent**. For non-PR targets, use the non-PR fallback text from **Branch or working-tree targets** in that section.>

   ## Project Notes
   <optional — omit this heading entirely when Step 2 found nothing: structure facts that change how findings should be read, e.g. "no test directory exists">

   ## Diff
   <diff for the files in this round; write "(none — untracked files only)" when the round has no diff blocks>

   ## File Contents
   <full content of each file in this round, labeled by path>
   ```

   Keep each round's Code Context under ~50 000 characters; the same block is duplicated into 3 pass prompts, so split at ~35–40k when close to the limit. **Multi-round:** list only this round's files under Changed Files; repeat Steps 4–6 per round, then run Steps 7–8 once using concatenated pass outputs from all rounds ([reference.md](reference.md) **Context budget and rounds**). Grouping, merging, and per-round rules: same section.

5. **Launch the 3 consolidated analysis passes sequentially** — issue one `Task` at a time; start the next pass only after the previous returns:

   | Pass | `description` | Agent sections from [agent-prompts.md](agent-prompts.md) (in order) |
   |------|---------------|---------------------------------------------------------------------|
   | 1 | `"Review pass: Sec/Perf/Obs"` | Agent 5 (Security), Agent 6 (Performance), Agent 8 (Observability) |
   | 2 | `"Review pass: Arch/DDD/Refactor"` | Agent 3 (DDD), Agent 4 (Clean Architecture), Agent 2 (Refactoring & Patterns) |
   | 3 | `"Review pass: Lang/TDD"` | Agent 1 (Language Spec), Agent 7 (TDD) |

   | Parameter | Value |
   |-----------|-------|
   | `subagent_type` | `"generalPurpose"` |
   | `prompt` | **Shared: Restrictions** + **Shared: Finding Format** + the pass's agent sections (concatenated) + the Code Context block (see **How to construct prompts** there) |

6. **Collect results** — after each pass, retain its report labeled by pass name. When a pass times out or returns empty or unusable output, tell the user and retry **that pass** once with the same prompt; do not retry a second time, and do not retry a pass that returned a usable report. Then proceed with the available outputs and instruct the integration subagent to record any missing pass.

7. **Assemble integration inputs** — once per review (not per round), before the integration `Task`:
   - **Stated Intent** — same text used in Step 4 (identical across rounds).
   - **Change Scope** — block with headings **## Change Scope**, **## Changed Files** (every scoped file with `hunks:<N>, +<A>/-<D>`), and **## Diff** (concatenate all `diff --git` blocks from every round; omit file contents). Required for Agent 9 intent alignment per [agent-prompts.md](agent-prompts.md) **Integration agent (9)**.

8. **Launch the integration subagent** — issue a single `Task` call:

   | Parameter | Value |
   |-----------|-------|
   | `subagent_type` | `"generalPurpose"` |
   | `description` | `"Integrate review findings"` |
   | `prompt` | **Shared: Restrictions** + **Shared: Final Report Format** + the Agent 9 section from [agent-prompts.md](agent-prompts.md) + the same **Stated Intent** block as Step 4 + **Change Scope** (review-wide Changed Files + full unified diff) + all available pass outputs (Pass 1–3) |

9. **Present the final review** — show the integration subagent's report, then offer to drill down into any area.

## Consolidated passes

Each pass is one `Task` that applies multiple specialist lenses (sections in [agent-prompts.md](agent-prompts.md)):

| Pass | Perspectives covered |
|------|----------------------|
| 1 | Security, Performance, Observability |
| 2 | DDD, Clean Architecture, Refactoring & Patterns |
| 3 | Language Spec, TDD |

## Agent roster (prompt source)

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

- **Offline design eval:** Maintainer comparison of multi-agent vs consolidated review lives in [reference/eval-comparison.md](reference/eval-comparison.md). GitHub remains read-only; artifacts under `/tmp/code-review-agents/` only.
- **Output language**: match the user's preference (default: 日本語).
- **Codebase exploration**: analysis subagents may `Read` / `Grep` surrounding code for context beyond the diff.
- **Model choice**: omit the `model` parameter so subagents inherit the parent model; if choosing a faster model instead, use `model: "composer-2.5-fast"` on all `Task` calls consistently.
