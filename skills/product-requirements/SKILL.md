---
name: product-requirements
description: Interviews product requirements via my-grill-me, then writes a seven-section requirements document to the configured storage destination. Does not implement the product or create Linear Issues.
disable-model-invocation: true
---

# Product requirements

Produce a **requirements document** at the **storage destination** (not in the git repo). Run the requirements interview using the **`my-grill-me`** workflow (read that skill’s installed `SKILL.md` — it is not auto-invoked); do not implement the product in this skill.

## Standalone invocation

Works without **`product-kickoff`**. If the product name, goal, or storage page title is missing, **ask the user** (or use what they provide in the same message). Do not require a Linear Project for this step.

## Document sections (required seven)

After the grill, the saved document must include these sections (see template). Use the **Japanese headings** below in the stored document; they match [`reference/requirements-template.md`](reference/requirements-template.md):

1. 目的 — purpose  
2. 利用者 — users / stakeholders  
3. 機能要件 — functional requirements  
4. 非機能要件 — non-functional requirements  
5. 範囲外 — out of scope  
6. 受け入れ条件 — acceptance criteria  
7. 未決事項 — open questions  

## Prerequisites

- **`my-grill-me`** — read the installed `SKILL.md` and follow its interview workflow (`disable-model-invocation: true`; the user may attach `/my-grill-me` explicitly). Subject = this product’s requirements.
- **Storage** — read [`../product-kickoff/reference/storage-destination.md`](../product-kickoff/reference/storage-destination.md) and the active provider doc (default: [`../product-kickoff/reference/storage-cosense.md`](../product-kickoff/reference/storage-cosense.md)).
- **Template** — [`reference/requirements-template.md`](reference/requirements-template.md).

## Non-negotiables

1. **Grill before write** — complete the **`my-grill-me`** workflow until shared understanding is confirmed (per that skill’s session end). Do not draft the final doc during the grill.
2. **No implementation** — no product code, infra, or Linear Issue create in this skill.
3. **No overwrite** — follow storage rules: existence check before create; never silently replace an existing page.
4. **Secrets** — never print `COSENSE_PAT` or other credentials.

## Integrated example

**User:** `/product-requirements` for “Acme Widget” — storage title `Acme Widget/要件定義` (Japanese requirements page suffix).

1. Confirm product name + title.
2. Follow installed **`my-grill-me`** `SKILL.md` until shared understanding confirmed.
3. Fill template (7 sections) → show full draft → user approves write.
4. Cosense: `readPage` → `persistent == false` → `previewEdit --new` + `submitEdit` per **storage-cosense** → report page title only.

## Workflow

**Checklist:**

```
- [ ] Product name, goal, storage title confirmed
- [ ] my-grill-me completed with user confirmation
- [ ] Draft has all 7 sections; user approved write
- [ ] Storage existence check passed; no overwrite
- [ ] Write succeeded; handoff summary
```

### 1. Scope the product

Confirm **product name**, **one-line goal**, and **storage page title** (or accept user-provided title). If missing, ask once.

### 2. Requirements interview

- Read the installed **`my-grill-me`** `SKILL.md` and follow its workflow (subject: requirements for `<product name>`). Do not assume nested skill auto-invocation.
- Cover at least: users, core workflows, non-goals, acceptance definition, constraints, open empirical items (parked per grill rules).
- Stop when the grill session completes with user confirmation of shared understanding (per **`my-grill-me`**).

### 3. Compose the document

- Fill [`reference/requirements-template.md`](reference/requirements-template.md) from settled decisions.
- Keep content under **未決事項** (open questions) for parked empirical items and unresolved product calls.

### 4. User review (required before write)

Show the **full draft** in chat (or attached artifact). Ask explicit approval to write to the storage destination with the agreed **title**.

“Publish now” or “upload to Cosense” **does not** replace this gate unless the **full seven-section draft** was just shown and the user explicitly approves **that text** and the **title**. Otherwise ask for approval again; do not call `previewEdit` / `submitEdit`.

### 5. Write to storage

- Follow **storage-destination** + **storage-cosense** (or future provider file).
- Cosense: **`cosense`** skill + CLI — `readPage` (`persistent`), new pages via **`previewEdit --new`** + **`submitEdit`**; convert template lines to Cosense format (no `#` headings).
- Existence check → create only when absent.
- On success: return **page title** and **how to open it** (public URL pattern without secrets), not cookie values.

### 6. Handoff

Summarize: link/title, count of FR/AC/OQ lines. Parent **`product-kickoff`** uses this as input for ADR and Issue decomposition.

## Usage

```text
/product-requirements
```

Optional context: product name, Cosense project (`COSENSE_PROJECT` already set), link to brainstorm notes.

## Additional resources

- Interview: **`my-grill-me`**
- Storage (abstract): [`../product-kickoff/reference/storage-destination.md`](../product-kickoff/reference/storage-destination.md)
- Storage (Cosense): [`../product-kickoff/reference/storage-cosense.md`](../product-kickoff/reference/storage-cosense.md)
- Template: [`reference/requirements-template.md`](reference/requirements-template.md)
