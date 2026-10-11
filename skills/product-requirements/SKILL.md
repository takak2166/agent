---
name: product-requirements
description: Interviews product requirements using my-grill-me, then writes a requirements document (purpose, users, functional/non-functional requirements, out of scope, acceptance criteria, open questions) to the configured storage destination. Use during product kickoff or when the user runs /product-requirements. Does not implement the product or create Linear Issues.
disable-model-invocation: true
---

# Product requirements

Produce a **requirements document** at the **storage destination** (not in the git repo). Interview via **`my-grill-me`**; do not implement the product in this skill.

## Prerequisites

- **`my-grill-me`** — read and follow that skill for the interview. Subject = this product’s requirements.
- **Storage** — read [`../product-kickoff/reference/storage-destination.md`](../product-kickoff/reference/storage-destination.md) and the active provider doc (default: [`../product-kickoff/reference/storage-cosense.md`](../product-kickoff/reference/storage-cosense.md)).
- **Template** — [`reference/requirements-template.md`](reference/requirements-template.md).

## Non-negotiables

1. **Grill before write** — run **`my-grill-me`** until shared understanding is confirmed (per that skill’s session end). Do not draft the final doc during the grill.
2. **No implementation** — no product code, infra, or Linear Issue create in this skill.
3. **No overwrite** — follow storage rules: existence check before create; never silently replace an existing page.
4. **Secrets** — never print `COSENSE_SID` or other credentials.

## Workflow

### 1. Scope the product

Confirm **product name**, **one-line goal**, and **storage page title** (or accept user-provided title). If missing, ask once.

### 2. Requirements interview

- Invoke **`my-grill-me`** with subject: requirements for `<product name>`.
- Cover at least: users, core workflows, non-goals, acceptance definition, constraints, open empirical items (parked per grill rules).
- Stop when **`my-grill-me`** completes with user confirmation of shared understanding.

### 3. Compose the document

- Fill [`reference/requirements-template.md`](reference/requirements-template.md) from settled decisions.
- Keep **未決事項** for parked empirical items and unresolved product calls.

### 4. User review (required before write)

Show the **full draft** in chat (or attached artifact). Ask explicit approval to write to the storage destination with the agreed **title**.

### 5. Write to storage

- Follow **storage-destination** + **storage-cosense** (or future provider file).
- Cosense: `persistent == false` on GET before import; new pages via **import API** + `Origin` header; convert template lines to Cosense format (no `#` headings).
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
