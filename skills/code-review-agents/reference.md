# Code review agents — reference

Read this file when Step 1 of [SKILL.md](SKILL.md) hits an edge case, or when Step 2/4 needs round splitting. Requirements in `SKILL.md` win if anything conflicts.

- [Target resolution](#target-resolution)
- [Context budget and rounds](#context-budget-and-rounds)

## Target resolution

### PR number vs branch name

Treat a bare integer as a PR number by default; treat anything else as a base branch name for `git diff`. When the argument is a bare integer, run `git branch --list <arg>` first:

- Matching branch exists → ask the user: 「`<arg>` は PR 番号ですか？それともブランチ名ですか？」
- No match → proceed as a PR number

### Unavailable `gh` (PR flow only)

When `gh` is missing, unauthenticated, or cannot fetch the PR, stop and tell the user to install or authenticate `gh` and re-run.

### Untracked files (no-argument flow)

`git diff HEAD` covers unstaged changes to tracked files only; untracked files are excluded. In the no-argument flow, always run `git status --porcelain` after computing the diff and treat untracked paths as added files:

- Include their full contents in Steps 2 and 4, with `hunks:0, +0/-0` as the change summary (no hunks exist).
- Expand directory-like entries (e.g. `?? dot_kube/`) into concrete paths with `Glob` scoped to that directory (e.g. `dot_kube/**`), then `Read` each match.
- When `Glob` returns nothing but the directory exists, report it as an untracked directory with unknown contents (coverage gap) instead of guessing.

### Empty diff

When the selected diff has no changed files, do not launch subagents. Run `git status --porcelain` before stopping and report paths as-is, one line per path; say the working tree is clean when it returns nothing.

- No-argument flow: if only untracked files exist, review them as added files per the section above.
- Base-branch flow (`git diff <branch>...HEAD`): this scope is committed-diff-only. Lead with "nothing to review in the committed diff", then, when the porcelain output shows uncommitted or untracked changes, list those paths and recommend either `/code-review-agents` with no argument for a working-tree review or committing first and re-running.

### Changed files and change summary

Extract paths from `diff --git a/<path> b/<path>` lines, preferring the `b/<path>` side. Treat `/dev/null` as an add or delete, and use the `rename to` path when rename info exists.

Summarize each file mechanically as `hunks:<N>, +<A>/-<D>`:

- `N`: lines starting with `@@` in that file's diff block
- `A`: lines starting with `+`, excluding the `+++ b/<path>` header
- `D`: lines starting with `-`, excluding the `--- a/<path>` header
- Binary and submodule diffs with no hunks: `hunks:0, +0/-0`

## Context budget and rounds

Estimate the budget by treating the assembled Code Context block (Changed Files + Diff + File Contents) as a single string and using its character length; approximate from file sizes when an exact count is unavailable. Split into multiple review rounds when one round would exceed ~50 000 characters.

- **Grouping heuristic**, in order: directory or module → language → size, keeping each group under the limit.
- **Diff per round**: include only the `diff --git ...` blocks for that round's files.
- **File contents per round**: include only that round's files.
- **Merging**: concatenate specialist outputs across rounds and let the integration subagent deduplicate. When a specialist is missing for any round, note it as a coverage gap.
