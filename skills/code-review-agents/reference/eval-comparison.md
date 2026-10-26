# Offline PR review design comparison (maintainer)

GitHub is **read-only** for this eval. Never post reviews or comments. Raw artifacts live only under `/tmp/code-review-agents/` (not committed).

## Ground-truth set

Build ~10 merged PRs from `takak2166/*` repos. For each PR:

1. Check out the PR head commit (`gh pr view --json headRefOid`) before `Read`/`Grep` file contents; use `gh pr diff` for the unified diff (read-only).
2. Ground truth = top-level review comments (`gh api …/pulls/{n}/comments`) that recommend a **fix**; exclude threads the author dismissed without a code change.
3. Normalize each ground-truth item to a short finding key (file + topic).

Store manifests as `/tmp/code-review-agents/eval-data/pr-{owner}-{repo}-{n}.json`.

## Designs

| Design | Dispatch pattern |
|--------|------------------|
| **A (current)** | 8 specialist analysis subagents in parallel + 1 integration subagent ([SKILL.md](../SKILL.md)) |
| **B (consolidated)** | 3 sequential generalist passes (security/performance/observability; architecture/DDD/refactoring; language/TDD) + 1 integration subagent — same shared Code Context, perspectives drawn from [agent-prompts.md](../agent-prompts.md) |

Run each PR **twice** per design (`run1`, `run2`) with the **same Task model** recorded in `BENCHMARKS.md`. **Pass** = recall ≥ 60% and precision ≥ 50% for that PR-run. Record **flipped PRs** when pass/fail changes between runs or after skill edits.

## Scoring

- **Recall** = matched ground-truth fix items / total ground-truth fix items.
- **Precision** = matched items / findings reported (ignore style-only nits unless ground truth marked fix).
- **Time/cost proxy** = subagent Task count × nominal wall time (A ≈ 9 cells; B ≈ 4 cells per PR).

**Winner rule:** If mean recall and mean precision are within **10 percentage points**, pick the design with lower time/cost. Otherwise pick higher mean recall.

## Recording

Append matrices to `/tmp/code-review-agents/BENCHMARKS.md`:

```markdown
## Design comparison — {date}

| PR | Design | Run | Recall | Precision | Tasks | Flipped vs prior |
|----|--------|-----|--------|-----------|-------|------------------|
```

Summarize flipped PR ids in the hardening or maintainer report.
