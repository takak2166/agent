# Storage destination (abstract)

Do **not** commit requirements or ADR body text to the git repo (avoid secrets and unreleased product information). Skill bodies say only **write to the storage destination**; provider-specific product names and APIs live in `reference/storage-*.md`.

## Agent rules

1. **Existence check before write** — if a page or file with the same title or slug already exists, **do not overwrite**. If an update is needed, confirm with the user and switch to append, a different title, or an explicit update procedure.
2. **No secrets in output** — never put authentication tokens, session IDs, or Cookie values in chat, commits, PRs, or screenshots. Reference only the **names** of environment variables.
3. **Swappable providers** — implementation details go in per-provider reference files. Skill bodies fix only the flow: fill the template and write to the storage destination.

## Document types and suggested title patterns

| Type | Suggested page / file title | Body template skill |
|------|----------------------------|---------------------|
| Requirements | `<product-name>/要件定義` (Japanese: “requirements definition”) or user-specified | `product-requirements` |
| ADR | `ADR/<NNN>-<short-slug>` | `write-adr` |

Agree product name and parent page with the user during kickoff.

## Default implementation today

- **Cosense (formerly Scrapbox)**: [`storage-cosense.md`](storage-cosense.md) — verified 2026-10 (**unofficial API**; may change).
- To move to another storage later, add `storage-<provider>.md` and update each skill’s **Additional resources** (do not change skill workflow bodies).
