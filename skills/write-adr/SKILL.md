---
name: write-adr
description: Writes one Architecture Decision Record per design decision to the storage destination with ADR-NNN numbering and Deprecated/Superseded lifecycle rules. Does not implement code or create Linear Issues.
disable-model-invocation: true
---

# Write ADR

Record **exactly one design decision per ADR** at the **storage destination**. If several decisions are unrelated, write **multiple ADRs** (separate invocations or explicit user-approved batch). Numbering and lifecycle (**Deprecated**, **Superseded**) are defined here.

## Standalone invocation

Works without **`product-kickoff`**. If requirements context is missing, ask for a short summary or storage title — do not block on Linear Project.

## Prerequisites

- **Storage** — [`../product-kickoff/reference/storage-destination.md`](../product-kickoff/reference/storage-destination.md), provider: [`../product-kickoff/reference/storage-cosense.md`](../product-kickoff/reference/storage-cosense.md).
- **Template** — [`reference/adr-template.md`](reference/adr-template.md).
- **Inputs** — requirements doc title/URL from user or prior **`product-requirements`** step; optional tech constraints from chat.

## ADR numbering and lifecycle

| Rule | Detail |
|------|--------|
| **Format** | `ADR-<NNN>` — three-digit zero-padded (`ADR-001`, `ADR-012`). |
| **Next number** | List existing pages whose titles match `ADR-<NNN>-…` at storage (`listPages` / search per **storage-cosense**); **max(NNN)+1**. If none, start at `001`. |
| **Title** | Page title: `ADR-<NNN>-<kebab-or-short-slug>` (slug ASCII; decision title may be Japanese in body H1). |
| **Status** | Start as **Proposed** unless the user says Accepted. |
| **Deprecated** | Mark old ADR **Deprecated**; set **Superseded by** to the new ADR id. Update the **old** page in storage only when user confirms (no silent overwrite — follow storage rules; prefer adding status block at top with user approval). |
| **Superseded** | New ADR references **Supersedes: ADR-xxx** when replacing a decision. |

Do not renumber published ADRs. New decision → new number.

## Non-negotiables

1. **One ADR per design decision** — never combine unrelated decisions in one ADR; use sequential numbers in the product (`ADR-001`, `ADR-002`, …). If the user asks for **one ADR covering multiple unrelated choices** (e.g. database **and** UI framework), **decline the merge**, explain the rule, and propose **separate ADRs** (batch approval OK).
2. **No overwrite** — new ADR = new page; deprecating an old ADR is an explicit update step after user confirms.
3. **No secrets** in ADR body or chat logs.
4. **No implementation** — design record only.

## Integrated example

**User:** `/write-adr` — “Use PostgreSQL for primary store” (requirements page already exists).

1. Clarify decision scope → draft options table + recommendation.
2. Allocate **ADR-003** (after storage scan).
3. User approves draft → Cosense `previewEdit --new` + `submitEdit` (new page only) → report `ADR-003-…` title.

## Workflow

**Checklist:**

```
- [ ] Single design decision scoped (split if multiple)
- [ ] ≥2 options + recommendation drafted
- [ ] NNN allocated; user approved write
- [ ] Storage rules (no overwrite); status set
- [ ] Supersedes/Deprecated handled if replacing old ADR
```

### 1. Clarify the decision

Ask briefly if unclear: what choice is being recorded (stack, boundary, data model, integration, etc.).

### 2. Options and recommendation

Draft **at least two** real options in the template table. State a **recommended** option with rationale (user may override before write).

### 3. User confirmation

Show draft ADR (full markdown). Confirm: number, title, status, and storage write.

### 4. Allocate number

Resolve **NNN** per table above (storage search / user-provided index).

### 5. Write to storage

- Create page per **storage-cosense** rules (`readPage` / `persistent`, **`previewEdit --new`** + **`submitEdit`**, Cosense line format).
- If **Supersedes** an older ADR: after create, plan an update to the old page’s status (user-confirmed).

### 6. Report

Return ADR id, title, status, and pointer to open the page. Note any **Deprecated** updates pending user confirmation.

## Usage

```text
/write-adr
```

Pass decision topic, requirements link, or “ADR for &lt;decision&gt;”.

## Additional resources

- Template: [`reference/adr-template.md`](reference/adr-template.md)
- Storage: [`../product-kickoff/reference/storage-destination.md`](../product-kickoff/reference/storage-destination.md), [`../product-kickoff/reference/storage-cosense.md`](../product-kickoff/reference/storage-cosense.md)
- Parent: **`product-kickoff`**
