---
name: product-kickoff
description: Orchestrates new-product planning in order — Linear Project (linear-create-project), milestones (linear-plan-milestones), requirements interview (product-requirements), ADR (write-adr), Issue decomposition (linear-decompose-project). Stops for user confirmation between phases; does not implement product code. Use when starting a new product or /product-kickoff.
disable-model-invocation: true
---

# Product kickoff

Run **planning only** for a new product in a fixed order. Delegate to child skills; do not duplicate their workflows inline.

## Child skills (use by reference)

| Step | Skill | Purpose |
|------|--------|---------|
| 1 | **`linear-create-project`** | Linear Project |
| 2 | **`linear-plan-milestones`** | Milestones on that Project |
| 3 | **`product-requirements`** | Grill + requirements doc at storage |
| 4 | **`write-adr`** | ADR(s) at storage |
| 5 | **`linear-decompose-project`** | Devin-reviewed Issue breakdown → **`linear-create-issue`** |

## Non-negotiables

1. **Order** — complete step *n* before step *n+1* unless the user explicitly skips (record what was skipped).
2. **No product implementation** — no app code, deploy, or “build MVP” in this skill.
3. **User gates** — see **Confirmation gates**; do not advance without explicit OK at each gate.
4. **Storage** — requirements and ADRs go to the storage destination ([`reference/storage-destination.md`](reference/storage-destination.md), Cosense: [`reference/storage-cosense.md`](reference/storage-cosense.md)). Do not commit product docs to the agent repo.
5. **Secrets** — never log `COSENSE_SID` or paste into PRs.

## Confirmation gates

| After step | Gate — user must confirm before next step |
|------------|---------------------------------------------|
| 1 | Project name/summary and **Linear Project URL** |
| 2 | Milestone names, order, target dates, completion criteria |
| 3 | Requirements draft, then **written page title** at storage |
| 4 | Each ADR draft (or batch) and **written ADR id/title** |
| 5 | Issue breakdown table **after Devin review**; then creation |

If the user rejects at a gate, revise within the same step’s skill and re-gate.

## Phase completion criteria

| Step | Done when |
|------|-----------|
| 1 | **`linear-create-project`** returned Project HTTPS URL (new or existing duplicate acknowledged) |
| 2 | **`linear-plan-milestones`** created milestones user approved (or explicit “no milestones”) |
| 3 | **`product-requirements`** grill complete + doc written with `persistent` check passed |
| 4 | **`write-adr`** at least one **Accepted** or **Proposed** ADR written per user scope |
| 5 | **`linear-decompose-project`** Issues created only after final OK; URLs reported |

## Workflow

### 0. Kickoff brief

Collect if missing: **product name**, **goal**, **Linear team** (or me-time/TAK defaults per child skills), **`COSENSE_PROJECT`** / **`COSENSE_SID`** availability for storage steps.

### 1 → 5

Run each child skill in order. Pass forward: Project URL, milestone names, requirements title, ADR ids.

Between steps, output a short **status block**: completed step, artifact links/titles, next step preview.

### Out of scope

- Implementation, hiring, infra provisioning
- Creating Issues before step 5 approval
- Overwriting existing Cosense pages (child storage rules)

## Usage

```text
/product-kickoff
```

Optional: backlog notes, Cosense brainstorm link, target ship themes.

## Additional resources

- Storage (abstract): [`reference/storage-destination.md`](reference/storage-destination.md)
- Storage (Cosense, verified 2026-10): [`reference/storage-cosense.md`](reference/storage-cosense.md)
