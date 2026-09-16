# Check PR Comment — reference

`SKILL.md` **Decision rubric**, **Non-negotiables**, and **Steps** win if anything conflicts.

Use this file when classifying a comment as **fix**, **dismiss**, or **ask**. The goal is not to ignore bots. The goal is to stop treating every comment as a required code change.

## Ask by default

Do not auto-dismiss these, even if a similar comment was dismissed on this PR or an earlier one:

- Security, privacy, auth, billing, data retention, training-data, and permission-boundary findings
- High-severity findings
- Migration, schema, idempotency, concurrency, and cross-system behavior
- A small suggested fix that clearly reduces risk without changing product intent

When unsure, **ask**. Skipping a noisy style comment is cheap. Skipping a real data or security bug is not.

## Dismiss only with a disproof

A **dismiss** summary must name the fact that makes the comment unnecessary, in one sentence. Examples:

- The cited guard is already on the PR tip before the side effect
- The symbol is used at `<path>` (or in a later commit on this branch)
- The visual change is explicit in the PR body / nearby code, and the comment only restates it
- Project rules already forbid or require the opposite of the suggestion
- A human reply on the thread already answers the claim with verifiable evidence or a named defer-until-condition plan (see **Author or maintainer reply resolves thread** below)

"Looks noisy" or "it's a bot" is not a disproof.

## Recurring skip candidates

Apply a pattern only when **Skip when** holds **and** you can state a disproof. **Do not skip when** always wins.

### Intentional visual or design-system change

- Skip when: The PR body, screenshots, or nearby code make the visual change explicit, and the comment only restates that a shared default changed
- Do not skip when: The comment points to accessibility, focus, keyboard, contrast, or a component API the PR did not intend to change
- Example signal: Focus outlines, button size, spacing, or shared visual defaults, with an "intentional" explanation already in the PR

### Unused export the current branch still uses

- Skip when: The comment says an export, helper, or file is unused, and `Grep` or a later hunk on this PR shows a caller
- Do not skip when: The symbol is public API, or the supposed use is not in this workspace / PR
- Example signal: "Exported component is never used"

### Temporary duplication during a parallel path

- Skip when: The PR keeps a short duplicate beside an old path that the same change is deleting, replacing, or proving out
- Do not skip when: The duplicate changes security, billing, data access, API behavior, or a long-lived shared abstraction would clearly reduce risk
- Example signal: "Significant duplication" on a local old/new split

### Existing invariant already covers the warning

- Skip when: A shared component, type, or single source of truth in the current file (or a file you `Read`) already enforces the concern
- Do not skip when: The invariant is assumed but not enforced, depends on timing, or crosses async / state boundaries
- Example signal: "Missing max-height" when the shared popover already clamps to the viewport

### Already fixed later on this PR

- Skip when: The comment cites a missing check or rename, and the file on disk (or a later `diff_hunk` in the same PR) already has that exact change
- Do not skip when: The helper is a no-op for the principal under discussion, the check runs after the side effect, or tests for that principal are missing
- Example signal: "Missing authorization check" while the guard is already called before the write

### Self-withdrawn or explicit false-positive

- Skip when: The comment body or a later bot reply says the finding is withdrawn, compliant, or a false positive, and you can verify the cited rule locally
- Do not skip when: The only evidence is a human "false positive" on an ask-by-default issue with no explanation

### Repeat bot pass on the same finding

- Skip when: The same bot already posted the same finding earlier in the thread (2+ prior comments), the pattern above applies, and the current code still disproves it
- Do not skip when: The finding is ask-by-default, or the code no longer disproves it

### Author or maintainer reply resolves thread

- Skip when (classify thread **dismiss**): A human reply on the thread (typically PR author or reviewer) addresses the top-level claim and at least one of:
  - cites **verification** (e.g. local runn/CI pass, code already contains the suggested check) that your code read does not contradict
  - states **intentional non-change** with a repo-consistent reason (matches an existing pattern, out of scope, preference)
  - states **defer-until-condition** with a named trigger (e.g. “CI e2e で落ちたら `/download/storage/v1` に寄せる”) — triage now is **dismiss**; record the trigger in the summary
- Do not skip when: The reply is vague, thanks-only, or off-topic; the claim is ask-by-default and the reply provides no verification; or your code read **contradicts** the reply’s verification claim
- Example signal: Copilot suggests a different GCS emulator URL path; author replies that local runn passes with the current path and they will align with the existing pattern only if CI fails — thread **dismiss**, not **ask**
- **Anti-pattern:** listing the reply `id` in coverage or under “返信” but recommending **ask** as if the thread were still undecided

## Widen-narrow error conditions

Do not **fix** a suggestion that broadens a narrow error (a specific `errno`, status, or code) into a catch-all when that narrowness distinguishes "not installed" from "ran and failed", or would hide the original error behind a fallback.

**Ask** if the narrow condition misses another case in the **same** category (e.g. `EACCES` as well as `ENOENT`) or drops data.

## Contract-test or doc-pin claims

When a comment says a test no longer matches a doc (or the reverse), and the test command is cheap and already named, you still **do not** run extra shell beyond `SKILL.md` **Restrictions**. Classify **ask** and name the test path, unless `Read` of both files already proves or disproves the claim. A proven mismatch against files you read is **fix**. A proven match is **dismiss** with that fact.
