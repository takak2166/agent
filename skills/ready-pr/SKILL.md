---
name: ready-pr
description: Converts a draft pull request to ready for review after CI checks pass. On CI failure, classifies stale base, flake or infrastructure, or in-diff failures before any retrigger (one fresh run max).
disable-model-invocation: true
---

# Ready PR

Convert a Draft PR to Ready for Review.

## Usage

```
/ready-pr [PR number]
```

Use when the user asks to mark a PR ready for review, convert a draft PR to ready, or invokes `/ready-pr`.

If the PR number is omitted, resolve it from the current branch via `gh pr list`.

## Non-negotiables

1. **Classify before any retrigger** — do not rerun CI until the failure is classified (see **Classification**).
2. **At most one fresh run** — flake or infrastructure earns one full `gh run rerun` (the whole run, never `--failed` / single-job retry). An identical second failure is not flake.
3. **Do not rebase, commit, or merge** — report a stale base or in-diff failure and exit. Mark ready only when checks pass.
4. Use only commands listed under **Restrictions**.

## Integrated example (median path)

**User:** `/ready-pr` on branch `feature/TAK-123-fix` with an open draft PR.

1. `gh pr list --head "$(git branch --show-current)" --json number,url,isDraft,headRefName,baseRefName,mergeStateStatus` → draft PR `#42`, base `main`
2. `gh pr checks --watch` → one check fails
3. **Classification:** `mergeStateStatus` is `CLEAN`; `gh pr diff --name-only` includes the failed job's path → **in-diff** → report failed check + paths, exit (no rerun)
4. Do not run `gh pr ready`

**User:** same branch, CI fails on checkout timeout (infra).

1. Steps 1–2 as above
2. **Classification:** not stale, logs do not implicate the diff → **flake/infra** → `gh run rerun [run-id]` once, then `gh pr checks --watch` again
3. Checks pass → `gh pr ready 42` → report URL and that a rerun was used

## Steps

Resolve **`[PR number]`** once in Step 1 and reuse that `number` in every later command.

1. **Resolve the target PR**
   - If a PR number was given, run `gh pr view [PR number] --json number,url,isDraft,state,headRefName,baseRefName,mergeStateStatus`
   - Otherwise run `gh pr list --head "$(git branch --show-current)" --json number,url,isDraft,headRefName,baseRefName,mergeStateStatus`
   - Continue only when a PR exists and `isDraft` is true. If none exists or it is not a draft, report that and exit
   - When a number was given, run `git branch --show-current`. If it does not match `headRefName`, say so, skip local `git fetch` / `git merge-base`, and classify stale base from `mergeStateStatus` only
2. Execute `gh pr checks --watch` and wait for CI to complete
3. If CI failed, classify per **Classification** (first failure). Report and exit unless **Flake or infrastructure** applies — then rerun once per Classification step 4, watch again with `gh pr checks --watch`, and if checks still fail classify per **After one rerun**; do not rerun again
4. Only if all CI checks pass, execute `gh pr ready [PR number]` to mark it as Ready for Review

## Classification

Run **first failure** checks in order. Stop at the first matching class.

### First failure

1. **Collect failures** — `gh pr checks --json name,bucket,link,workflow --jq '.[] | select(.bucket == "fail")'`
2. **Stale base** — treat as stale when either holds:
   - `mergeStateStatus` is `BEHIND` or `DIRTY` (from Step 1; if missing, `gh pr view [PR number] --json mergeStateStatus`)
   - Local branch matches `headRefName` **and** `git fetch origin [baseRefName]` then `git merge-base --is-ancestor origin/[baseRefName] HEAD` is **false** (exit code 1). If fetch fails, skip the ancestor check and use `mergeStateStatus` only
   - `DIRTY` → class **conflicts**: report that the owner must rebase and stop. Do not fall through to a rerun
   - `BEHIND` or a failed ancestor check → class **stale-base**: report which branch needs the rebase and stop. Do not burn the retry
3. **In-diff** — `gh pr diff --name-only`. If failed-check names or `gh run view [run-id] --log-failed` point at those paths (or at code this PR introduced), class **in-diff**. Report the failed checks and the implicated paths, then exit. Do not rerun
4. **Flake or infrastructure** — timeouts, lost runner, Actions 5xx, checkout/setup/cache failures, or a failure whose logs do not implicate the PR diff. Rerun the **entire** failed run once: take `databaseId` from the check `link` (`/actions/runs/<id>`) or `gh run list --branch [headRefName] --json databaseId,name,conclusion,url`, then `gh run rerun [run-id]` (no `--failed`). Return to **Steps** step 2

When class is unclear on first failure, do **not** assume flake. Class **unclear**. Report the failed checks, the stale-base and in-diff evidence you have, and exit without rerunning.

### After one rerun

If checks still fail after the single allowed rerun:

1. **Identical second failure** — the same check `name` set is still `fail`. Class **not-flake**. Report `gh run view [run-id] --log-failed` (or the failed-check `link`s) and exit
2. Otherwise re-run **First failure** steps 2–3 (stale base, in-diff) before classifying again as flake — a second flake rerun is never allowed

## Expected output

**Ready:** the PR URL and that it is no longer a draft.

**Stopped on failure:** class (`stale-base` / `conflicts` / `in-diff` / `flake-retried` / `not-flake` / `unclear`), failed check names with `link`, and the action for the human (rebase, fix the diff, or read logs). After a flake rerun that then passed, continue to `gh pr ready` and report that a rerun was used.

## Restrictions

- Do not execute any commands other than `gh pr list`, `gh pr view`, `gh pr checks`, `gh pr diff`, `gh pr ready`, `gh run list`, `gh run view`, `gh run rerun`, `git branch --show-current`, `git fetch`, and `git merge-base`
- Do not pass `--failed` to `gh run rerun`
- Do not rebase, commit, push, or merge
- `jq` is allowed only to slice JSON from `gh` (as in the failed-check filter above)
