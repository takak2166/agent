---
name: product-kickoff
description: Orchestrates new-product planning in six ordered phases (Project, milestones, requirements, ADR, milestone review, Issue decomposition) by delegating to child skills with user confirmation gates. No product implementation. Child skills also work standalone.
disable-model-invocation: true
---

# Product kickoff

Run **planning only** for a new product in a fixed order. Delegate to child skills; do not duplicate their workflows inline.

## Child skills (use by reference)

| Step | Skill | Purpose |
|------|--------|---------|
| 1 | **`linear-create-project`** | Linear Project (unchanged; use as-is) |
| 2 | **`linear-plan-milestones`** | Initial milestones (create mode) |
| 3 | **`product-requirements`** | Grill + requirements doc at storage |
| 4 | **`write-adr`** | ADR(s) at storage (one decision per ADR) |
| 5 | **`linear-plan-milestones`** | **Review mode** — revisit milestones after requirements + ADR |
| 6 | **`linear-decompose-project`** | Devin-reviewed Issue breakdown → **`linear-create-issue`** |

## Standalone use (child skills)

Each child skill **must work when invoked alone** (not only from this parent).

- If a prior artifact is missing (Project URL, milestone list, requirements title, ADR ids), **ask the user** or accept what they paste in the same turn — do not assume kickoff already ran.
- Do not call **`linear-create-project`** from children unless that child’s skill explicitly allows it; step 1 stays **`linear-create-project`** only.

## Non-negotiables

1. **Order** — in a full kickoff, complete step *n* before step *n+1* unless the user explicitly skips (record what was skipped).
2. **No product implementation** — no app code, deploy, or “build MVP” in this skill.
3. **User gates** — see **Confirmation gates**; do not advance without explicit OK at each gate.
4. **Storage** — requirements and ADRs go to the storage destination ([`reference/storage-destination.md`](reference/storage-destination.md), Cosense: [`reference/storage-cosense.md`](reference/storage-cosense.md)). Do not commit product docs to the agent repo.
5. **Secrets** — never log `COSENSE_SID` or paste into PRs.
6. **No Issue creation in this skill** — do not call `save_issue`, **`linear-create-issue`**, or create “planning/meta” Issues when the user asks to skip ahead. Step 6 delegates to **`linear-decompose-project`** only after steps 1–5 gates; Issues appear only after that child’s final OK.

## Confirmation gates

| After step | Gate — user must confirm before next step |
|------------|---------------------------------------------|
| 1 | Project name/summary and **Linear Project URL** |
| 2 | Milestone **draft table** (names, dates, completion criteria) then created milestones |
| 3 | Requirements draft, then **written page title** at storage |
| 4 | Each ADR draft (or batch) and **written ADR id/title** |
| 5 | Milestone **review change set** (add/rename/re-date/criteria updates) before any `save_milestone` update |
| 6 | Issue breakdown table **after Devin review**; then creation |

If the user rejects at a gate, revise within the same step’s skill and re-gate.

## Phase completion criteria

| Step | Done when |
|------|-----------|
| 1 | **`linear-create-project`** returned Project HTTPS URL (new or existing duplicate acknowledged) |
| 2 | **`linear-plan-milestones`** (create mode) milestones user approved and created (or explicit “no milestones yet”) |
| 3 | **`product-requirements`** grill complete + 7-section doc written with storage rules satisfied |
| 4 | **`write-adr`** all in-scope design decisions recorded (≥1 ADR unless user scoped zero) |
| 5 | **`linear-plan-milestones`** (review mode) user approved changes applied or confirmed “no milestone changes” |
| 6 | **`linear-decompose-project`** Issues created only after final OK; URLs reported |

## Workflow

### 0. Kickoff brief

Collect if missing: **product name**, **goal**, **Linear team** (or me-time/TAK defaults per child skills), **`COSENSE_PROJECT`** / **`COSENSE_SID`** availability for storage steps.

### 1 → 6

**Kickoff checklist (full run):**

```
- [ ] Step 1 linear-create-project — Project URL + user gate
- [ ] Step 2 linear-plan-milestones create — milestones + user gate
- [ ] Step 3 product-requirements — 7-section doc + user gate
- [ ] Step 4 write-adr — ADR(s) + user gate
- [ ] Step 5 linear-plan-milestones review — change set + user gate
- [ ] Step 6 linear-decompose-project — Devin + Issues only after OK
```

Run each child skill in order. Pass forward: Project URL, milestone names, requirements title, ADR ids.

- **Step 5:** invoke **`linear-plan-milestones`** in **review mode** (see that skill). Inputs: Project, requirements doc title, ADR list, current `list_milestones`.
- **Step 6:** invoke **`linear-decompose-project`** with updated milestones.

Between steps, output a short **status block**: completed step, artifact links/titles, next step preview.

### Integrated example (abbreviated)

**User:** `/product-kickoff` for “Acme Widget”, me-time/TAK defaults.

1. **`linear-create-project`** → gate → Project URL.
2. **`linear-plan-milestones`** create → gate.
3. **`product-requirements`** → gate → requirements page title.
4. **`write-adr`** (e.g. data store, API style) → gate.
5. **`linear-plan-milestones`** review → gate (maybe shift MVP date).
6. **`linear-decompose-project`** → Devin → gate → Issues.

Stop after any gate if user says no; do not implement product code.

### Out of scope

- Implementation, hiring, infra provisioning
- Creating Issues before step 6 approval
- Overwriting existing Cosense pages (child storage rules)

## Usage

```text
/product-kickoff
```

Optional: backlog notes, storage brainstorm link, target ship themes.

## Additional resources

- Storage (abstract): [`reference/storage-destination.md`](reference/storage-destination.md)
- Storage (Cosense, verified 2026-10): [`reference/storage-cosense.md`](reference/storage-cosense.md)
