---
name: product-kickoff
description: Orchestrates new-product planning in six ordered phases (Project, milestones, requirements, ADR, milestone review, Issue decomposition) by delegating to child skills with user confirmation gates. No product implementation. Child skills also work standalone.
disable-model-invocation: true
---

# Product kickoff

Run **planning only** for a new product in a fixed order. Delegate to child skills by **reading each child’s installed `SKILL.md`** and following its workflow; do not duplicate their workflows inline.

## Child skills (use by reference)

Kickoff child skills (including **`linear-plan-milestones`**, **`product-requirements`**, **`write-adr`**, **`linear-decompose-project`**) use **`disable-model-invocation: true`** — they are **not** auto-invoked from this parent. At each step, read the installed child `SKILL.md` (the user may attach that skill explicitly) and execute per that document.

| Step | Skill | Purpose |
|------|--------|---------|
| 1 | **`linear-create-project`** | Linear Project — read installed `SKILL.md` and follow it |
| 2 | **`linear-plan-milestones`** | Initial milestones (create mode) |
| 3 | **`product-requirements`** | Grill + requirements doc at storage |
| 4 | **`write-adr`** | ADR(s) at storage (one decision per ADR) |
| 5 | **`linear-plan-milestones`** | **Review mode** — revisit milestones after requirements + ADR |
| 6 | **`linear-decompose-project`** | Devin-reviewed Issue breakdown → **`linear-create-issue`** |

**Auto-discoverable skills:** **`linear-create-project`** (step 1) and **`linear-create-issue`** (step 6, via decomposition) may load without `disable-model-invocation`. Still **Read** their installed `SKILL.md` and obey kickoff **Confirmation gates**. **Step 1:** call `save_project` only **after** the user approves Project **name** and **summary** (and any creation fields the child shows); the returned **Linear Project URL** is confirmed to **advance to step 2**, not as a precondition for `save_project`. **Step 6:** do **not** call `save_issue` until the user approves the **issue breakdown table** after Devin review — even if **`linear-create-issue`** auto-loads.

## Installed child skill resolution

Before each step, resolve and **Read** the child’s `SKILL.md` using the first readable path:

1. `<workspace>/.agents/skills/<skill-name>/SKILL.md`
2. `<workspace>/.claude/skills/<skill-name>/SKILL.md`
3. `<workspace>/skills/<skill-name>/SKILL.md` (source repo)
4. `$HOME/.claude/skills/<skill-name>/SKILL.md`
5. `$HOME/.agents/skills/<skill-name>/SKILL.md`

If none resolve, **stop** and ask the user to install the missing skill (see [`apm.yml`](apm.yml)). Do not substitute workflows from memory.

## Standalone use (child skills)

Each child skill **must work when invoked alone** (not only from this parent).

- If a prior artifact is missing (Project URL, milestone list, requirements title, ADR ids), **ask the user** or accept what they paste in the same turn — do not assume kickoff already ran.
- Do not call **`linear-create-project`** from children unless that child’s skill explicitly allows it; step 1 stays **`linear-create-project`** only.

## Non-negotiables

1. **Order** — in a full kickoff, complete step *n* before step *n+1* unless the user explicitly skips (record what was skipped).
2. **No product implementation** — no app code, deploy, or “build MVP” in this skill.
3. **User gates** — see **Confirmation gates**; do not advance without explicit OK at each gate.
4. **Storage** — requirements and ADRs go to the storage destination via **`product-storage`** ([`../product-storage/reference/storage-destination.md`](../product-storage/reference/storage-destination.md), default Cosense: [`../product-storage/reference/storage-cosense.md`](../product-storage/reference/storage-cosense.md)). Do not commit product docs to the agent repo.
5. **Secrets** — never log `COSENSE_PAT` or paste into PRs.
6. **No Issue creation in this skill** — do not call `save_issue`, **`linear-create-issue`**, or create “planning/meta” Issues when the user asks to skip ahead. Step 6 delegates to **`linear-decompose-project`** only after steps 1–5 gates; Issues appear only after that child’s final OK.

## Confirmation gates

| After step | Gate — user must confirm before next step |
|------------|---------------------------------------------|
| 1 (pre-create) | Project **name** and **summary** (and description draft if shown) — **before** `save_project` |
| 1 (post-create) | Returned **Linear Project URL** (new or acknowledged duplicate) — **before step 2** |
| 2 | Milestone **draft table** (names, dates, completion criteria) then created milestones |
| 3 | Requirements draft, then **written page title** at storage |
| 4 | Each ADR draft (or batch) and **written ADR id/title** |
| 5 | Milestone **review change set** (add/rename/re-date/criteria updates) before any `save_milestone` update |
| 6 | Issue breakdown table **after Devin review**; then creation |

If the user rejects at a gate, revise within the same step’s skill and re-gate.

Informal phrases (“looks good”, “proceed”, “go ahead”, “proceed to requirements”) **do not** close a gate unless they clearly approve the **current gate’s artifact** (step 1 pre-create: name/summary; step 1 post-create: Project URL; milestone draft table; requirements draft; ADR draft; milestone change set; issue breakdown table). Advancing to step *n+1* requires explicit OK on step *n*’s **post-create** gate (or final gate for that step) — not intent to move on. When ambiguous, ask one explicit confirm question before `save_project`, `save_issue`, or advancing.

## Dry-run and sandbox

When the user or harness says **SANDBOX**, **dry-run**, or **mandatory sandbox**: **do not** call Linear MCP (`save_project`, `save_issue`, `save_milestone`, …), Cosense `submitEdit` / `previewEdit` against production, or GitHub writes. Report **mock** URLs/titles only. Step 6 “Issues created” means the user approved the breakdown in chat — still **no** `save_issue` in sandbox.

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

### 0. Preflight and kickoff brief

**Preflight (stop if unresolved):** Resolve installed `SKILL.md` for **`linear-create-project`**, **`linear-plan-milestones`**, **`product-requirements`**, **`write-adr`**, **`linear-decompose-project`**, **`linear-create-issue`**, **`product-storage`**, **`cosense`**, and **`my-grill-me`** per **Installed child skill resolution**. Confirm Linear MCP tool descriptors are readable for the planned steps. For step 6, confirm a **ubuntu24** Devin worker is available or the user accepts a documented Devin skip.

**Environment (names only — never collect token values):** Confirm **`COSENSE_PROJECT`** is known or will be asked. Verify **`COSENSE_PAT`** is **set in the user’s environment** (or the user will run `cosense login`) — do **not** ask the user to paste the PAT. When storage steps will run, confirm **`@helpfeel/cosense-cli`** is available (**Node.js >= 24** per [`../product-storage/reference/storage-cosense.md`](../product-storage/reference/storage-cosense.md)).

Collect if still missing: **product name**, **goal**, **Linear team** (or me-time/TAK defaults per child skills).

### 1 → 6

**Kickoff checklist (full run):**

```
- [ ] Preflight passed
- [ ] Step 1 linear-create-project — Project URL + user gate
- [ ] Step 2 linear-plan-milestones create — milestones + user gate
- [ ] Step 3 product-requirements — 7-section doc + user gate
- [ ] Step 4 write-adr — ADR(s) + user gate
- [ ] Step 5 linear-plan-milestones review — change set + user gate
- [ ] Step 6 linear-decompose-project — Devin + Issues only after OK
```

Run each step in order using the matching child’s installed `SKILL.md`. Pass forward: Project URL, milestone names, requirements title, ADR ids.

- **Step 2:** follow **`linear-plan-milestones`** **create** mode (installed skill).
- **Step 5:** follow **`linear-plan-milestones`** **review** mode (installed skill; see its Review-mode triggers). Inputs: Project, requirements doc title, ADR list, current `list_milestones`.
- **Step 6:** follow **`linear-decompose-project`** (installed skill) with updated milestones.

Between steps, output a short **status block**: completed step, artifact links/titles, next step preview.

### Integrated example (abbreviated)

**User:** `/product-kickoff` for “Acme Widget”, me-time/TAK defaults.

1. **`linear-create-project`** (installed `SKILL.md`) → gate → Project URL.
2. **`linear-plan-milestones`** create (installed `SKILL.md`) → gate.
3. **`product-requirements`** (installed `SKILL.md`) → gate → requirements page title.
4. **`write-adr`** (installed `SKILL.md`; e.g. data store, API style) → gate.
5. **`linear-plan-milestones`** review (installed `SKILL.md`) → gate (maybe shift MVP date).
6. **`linear-decompose-project`** (installed `SKILL.md`) → Devin → gate → Issues.

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

- Storage package: **`product-storage`** — [`../product-storage/reference/storage-destination.md`](../product-storage/reference/storage-destination.md), [`../product-storage/reference/storage-cosense.md`](../product-storage/reference/storage-cosense.md)
- Transitive APM deps: [`apm.yml`](apm.yml)
