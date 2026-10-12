---
name: linear-decompose-project
description: Decomposes requirements and ADRs into milestone-linked Linear Issues (one PR per Issue), runs Devin review on ubuntu24, and creates Issues only after user approval via linear-create-issue. Use when the user runs `/linear-decompose-project`, product-kickoff step 6, or asks for an issue breakdown from requirements and ADRs. Never creates Issues before user OK.
disable-model-invocation: true
---

# Decompose project into Linear Issues

Turn **requirements** + **ADRs** into a **draft Issue breakdown** mapped to **Linear milestones**, run **Devin** review on **ubuntu24**, revise, get **user approval**, then create Issues with **`linear-create-issue`** only.

## Standalone invocation

Works without **`product-kickoff`**. If inputs are missing, **ask in one batch**:

- Linear **Project** (URL or id)
- **Milestone** names (from user or `list_milestones`)
- **Requirements** doc title or pasted 7-section summary
- **ADR** ids/titles (and one-line decision each)
- Optional: team, default priority/state

Do not create Issues until the user approves the final table (step 4 below).

## Installed skill resolution

Resolve **`linear-create-issue`**, **`product-storage`**, and **`cosense`** (when reading storage) using the path order in **`product-requirements`** (**Installed skill resolution**). If **`linear-create-issue`** is missing, **stop** before step 5 (see [`apm.yml`](apm.yml)).

## Prerequisites

- **Linear MCP** — `get_project`, `list_milestones`, `list_issues` (duplicate detection before create).
- **`linear-create-issue`** — read and follow for **each** Issue after approval (no bulk `save_issue` bypass).
- **Inputs** — as above.

## Dry-run and sandbox

When the user or harness says **SANDBOX**, **dry-run**, or **mandatory sandbox**: **do not** call `save_issue`, **`linear-create-issue`**, or other Linear writes — even if the user approved a table or said “create now”. Describe mock issue titles/count only.

## Restrictions

1. **No Issue create before user OK** — no `save_issue` create, no **`linear-create-issue`**, until explicit approval of the final breakdown table **after** Devin review (step 3) unless the user explicitly documents a Devin skip with caveat.
2. **Granularity** — **one Issue = one PR’s worth of work** (mergeable in a single draft PR; completable in one review cycle). Split epics; do not bundle unrelated FRs. Spikes get their own Issue when they are separate PRs.
3. **Milestone link** — every row maps to a **milestone name** from the Project (or user-approved `Unassigned` exception).
4. **No Devin on cloud VM** — Devin CLI only on a self-hosted worker with **`machineDisplayName` `ubuntu24`**. If unavailable, ask the user to run Devin on ubuntu24 and paste output.
5. **No secrets** in Devin prompts.
6. **Do not embed** Linear issue identifiers in committed repo files.

## Integrated example

**User:** `/linear-decompose-project` — Project URL, 3 milestones, pasted requirements summary, ADR-001/002 titles.

1. Draft table: each row = **one PR** (e.g. “Add auth API routes”, not “Build auth”).
2. Devin on **ubuntu24** reviews granularity → revise table.
3. User OK → **`linear-create-issue`** per row with milestone name.

## Workflow

**Checklist:**

```
- [ ] Project + milestones (name→id map) + requirements + ADRs loaded
- [ ] Draft table: one Issue = one PR; every row has milestone
- [ ] Devin review on ubuntu24 (or documented skip)
- [ ] User approved final table
- [ ] linear-create-issue per row only after OK
```

### 1. Load context

Resolve **Project** once; **`list_milestones`** and keep a **`{milestone name → milestone id}`** map for step 5.

If **`list_milestones` fails**, stop before drafting creates — retry or ask the user for milestone names/ids.

Load requirements + ADR content from user paste or storage (read **`product-storage`** + **`cosense`** when credentialed and asked).

### 2. Draft breakdown

| # | Issue title | Milestone | Team (if not default) | Priority | Notes / AC summary |
|---|-------------|-----------|------------------------|----------|-------------------|

Rules:

- **One row = one PR** — title must name a single shippable increment mergeable as **one draft PR** (e.g. “Add login API endpoint”, not “Build entire auth”). Split until each row is one review cycle. **Epic-sized titles** in the user input must be **split in the draft table** before Devin/user review — do not leave a single “build everything” row unless the user explicitly limits scope to one PR.
- Every row has a **milestone** (name from step 1).
- Actionable titles; 1–2 line acceptance hint (full body via **`linear-create-issue`**).

### 3. Devin review (ubuntu24)

Read and follow [`reference/devin-ubuntu24.md`](reference/devin-ubuntu24.md). Apply reasonable edits to the table from Devin output.

### 4. User confirmation (required)

Present revised table + Devin summary. Explicit approval to create **N** Issues.

### 5. Create Issues

Resolve **team** and **project** once per batch; reuse for every row.

For each approved row:

1. **`list_issues`** with `query`/filters on title keywords + **project** (and **team** when known) — moderate `limit` per **`linear-create-issue`**. If duplicate detection is incomplete or **`list_issues` errors**, **do not create** that row until resolved.
2. Run **`linear-create-issue`** (read installed `SKILL.md`) with title, team, project, description from [`linear-create-issue/reference/issue-description.md`](../linear-create-issue/reference/issue-description.md).
3. **Milestone:** read **`save_issue` descriptor** — if a milestone/project-milestone field exists, pass the **milestone id** from the step 1 map; if unsupported, add **`Milestone:`** line in the description and tell the user to link in the UI.

**Resume:** If creation stops mid-batch, report created URLs and continue from the next approved row — do not recreate rows already reported.

### 6. Report

Created count, Issue URLs, milestone mapping, manual follow-ups.

## Usage

```text
/linear-decompose-project
```

Provide Project, milestones, requirements + ADR references.

## Additional resources

- Devin on ubuntu24: [`reference/devin-ubuntu24.md`](reference/devin-ubuntu24.md)
- Issue creation: **`linear-create-issue`**
- Storage reads (optional): **`product-storage`**
- Transitive deps: [`apm.yml`](apm.yml)
- Parent: **`product-kickoff`**
