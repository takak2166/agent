# Offline PR review design comparison (maintainer)

GitHub is **read-only** for this eval. Never post reviews or comments. Raw artifacts live only under `/tmp/code-review-agents/` (not committed).

## Ground-truth set

Build ~10 merged PRs from `takak2166/*` repos. For each PR:

1. Check out the PR head commit (`gh pr view --json headRefOid`) before `Read`/`Grep` file contents; use `gh pr diff` for the unified diff (read-only).
2. **Ground truth** = inline review comments that recommend a **fix** (human or bot), collected with:
   - `gh api -X GET /repos/{owner}/{repo}/pulls/{n}/comments --paginate` (REST review comments), **and**
   - GraphQL `reviewThreads` when a Files-tab thread has no REST row (paginate until `hasNextPage` is false).
   Exclude threads the author dismissed without a code change and pure praise/LGTM.
3. Normalize each ground-truth item to a **finding key**: `{path}::{topic}` where `topic` is a short stable label for the underlying defect (same file + same root cause = one key).

Store manifests as `/tmp/code-review-agents/eval-data/{owner}-{repo}-{n}.json` with `gt_fix_count` and normalized keys.

**PR selection:** merged PRs with at least one fix-oriented review comment; spread across repos; avoid empty or docs-only diffs when possible.

## Designs

| Design | Dispatch pattern |
|--------|------------------|
| **A (current)** | 8 specialist analysis subagents in parallel + 1 integration subagent ([SKILL.md](../SKILL.md)) |
| **B (consolidated)** | 3 sequential consolidated passes (security/performance/observability; architecture/DDD/refactoring; language/TDD) + 1 integration subagent — same shared Code Context, agent sections from [agent-prompts.md](../agent-prompts.md) |

Run each PR **twice** per design (`run1`, `run2`) with **`model: composer-2.5`** on every `Task` (record the model slug from each subagent transcript or tool metadata — do not assume).

## Scoring

- **Matched:** A reported finding matches a ground-truth key when the same `{path}::{topic}` is identified (same file and same root cause; wording may differ).
- **Recall** = |matched GT keys| / |GT fix keys|.
- **Precision** = |matched GT keys| / |reported fix findings|. **Style-only nits** are excluded from the precision **denominator** (do not count as reported fix findings). They still do not count as matches unless GT marked them fix.
- **Pass (per PR-run):** recall ≥ 60% **and** precision ≥ 50% (for flip tracking only).
- **Flipped PRs:** PR ids where **pass** differs between `run1` and `run2` for the same design, or where recall changes by ≥ 15 percentage points between runs (record either signal in `BENCHMARKS.md`).

## Time and cost (measured)

Per PR-run, record from logs (not proxies):

- **Wall time (s):** orchestrator start → integration report ready.
- **Token usage:** input/output/cached tokens if the host exposes them per `Task`; otherwise record `tokens: unavailable` and do not infer cost.

Do **not** use “task count × nominal wall time” as a substitute for measured wall time or token totals.

## Winner rule

1. Compare **mean recall** and **mean precision** across all completed PR-runs for each design.
2. If **both** gaps are ≤ **10 percentage points**, pick the design with **lower measured** wall time and token cost (when tokens unavailable, wall time only).
3. If recall gap **>** 10 points, pick higher mean recall.
4. If recall gap ≤ 10 but precision gap **>** 10 points, pick higher mean precision.
5. If still tied within measurement noise, rerun flipped PRs once; if still tied, keep **Design A** (current shipped shape).

**Ship decision:** Update `SKILL.md` only when the winning design is **B**. When **A** wins, update this file and `/tmp/.../BENCHMARKS.md` only.

## Recording

Append to `/tmp/code-review-agents/BENCHMARKS.md`:

```markdown
## Design comparison — {date}

**Runs completed:** {n}/40 (10 PRs × 2 designs × 2 runs). If {n} < 40, do not publish aggregate recall/precision means — list completed cells only.

| PR | Design | Run | Model (verified) | Recall | Precision | Wall s | Tokens in/out | Pass |
|----|--------|-----|------------------|--------|-----------|--------|---------------|------|
```

Summarize flipped PR ids and the ship decision in the maintainer report.

## Execution status

Full-matrix results are valid only when **40/40** cells complete with verified `composer-2.5` runs. Partial matrices must state `completed_count` and omit invented aggregates (see `/tmp/code-review-agents/EXECUTION_STATUS.md`).
