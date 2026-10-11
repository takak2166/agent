---
name: write-adr
description: Writes Architecture Decision Records (context, decision, options, consequences, status) to the storage destination with numbered ADR-NNN titles and Deprecated/Superseded rules. Use after requirements exist or when the user runs /write-adr. Does not implement code or create Linear Issues.
disable-model-invocation: true
---

# Write ADR

Record **one architecture decision** (or a tightly related set) as an **ADR** at the **storage destination**. Numbering and lifecycle (**Deprecated**, **Superseded**) are defined here.

## Prerequisites

- **Storage** — [`../product-kickoff/reference/storage-destination.md`](../product-kickoff/reference/storage-destination.md), provider: [`../product-kickoff/reference/storage-cosense.md`](../product-kickoff/reference/storage-cosense.md).
- **Template** — [`reference/adr-template.md`](reference/adr-template.md).
- **Inputs** — requirements doc title/URL from user or prior **`product-requirements`** step; optional tech constraints from chat.

## ADR numbering and lifecycle

| Rule | Detail |
|------|--------|
| **Format** | `ADR-<NNN>` — three-digit zero-padded (`ADR-001`, `ADR-012`). |
| **Next number** | List existing pages under prefix `ADR/` (or project convention) at storage; **max(NNN)+1**. If none, start at `001`. |
| **Title** | Page title: `ADR-<NNN>-<kebab-or-short-slug>` (slug ASCII; decision title may be Japanese in body H1). |
| **Status** | Start as **Proposed** unless the user says Accepted. |
| **Deprecated** | Mark old ADR **Deprecated**; set **Superseded by** to the new ADR id. Update the **old** page in storage only when user confirms (no silent overwrite — follow storage rules; prefer adding status block at top with user approval). |
| **Superseded** | New ADR references **Supersedes: ADR-xxx** when replacing a decision. |

Do not renumber published ADRs. New decision → new number.

## Non-negotiables

1. **One ADR per decision thread** — split unrelated decisions into separate ADRs.
2. **No overwrite** — new ADR = new page; deprecating an old ADR is an explicit update step after user confirms.
3. **No secrets** in ADR body or chat logs.
4. **No implementation** — design record only.

## Workflow

### 1. Clarify the decision

Ask briefly if unclear: what choice is being recorded (stack, boundary, data model, integration, etc.).

### 2. Options and recommendation

Draft **at least two** real options in the template table. State a **recommended** option with rationale (user may override before write).

### 3. User confirmation

Show draft ADR (full markdown). Confirm: number, title, status, and storage write.

### 4. Allocate number

Resolve **NNN** per table above (storage search / user-provided index).

### 5. Write to storage

- Create page per **storage-cosense** rules (`persistent` check, import + `Origin`, Cosense line format).
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
