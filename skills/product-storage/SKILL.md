---
name: product-storage
description: Defines the default Cosense storage destination and write procedures for product requirements and ADRs. Swappable provider details live in reference files. Does not run kickoff or create Linear artifacts.
disable-model-invocation: true
---

# Product storage

Shared **storage destination** rules for product-planning skills (`product-requirements`, `write-adr`, **`product-kickoff`**). **Cosense** (via **`cosense`** skill and **`@helpfeel/cosense-cli`**) is the **default provider** today; other providers can be added as `reference/storage-<provider>.md` without changing workflow skills.

## Non-negotiables

1. **No overwrite without approval** — existence check before create (see references).
2. **No secrets** — reference env var **names** only; never paste `COSENSE_PAT` or tokens.
3. **CLI / skill only** — Cosense reads/writes follow **storage-cosense**; no raw import API or cookie auth in planning skills.

## Additional resources

- Abstract flow: [`reference/storage-destination.md`](reference/storage-destination.md)
- Default provider (Cosense): [`reference/storage-cosense.md`](reference/storage-cosense.md)
- Transitive deps: [`apm.yml`](apm.yml)
