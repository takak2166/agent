# Optional sections (only when shared rules are absent)

Insert **after** Architecture when Step 4 finds **no** shared always-on rules. Keep short.

## Core Principles

- **Line budget:** Non-blank, non-HTML-comment lines = instruction body (target **30–50**). Whole file ≤**75** lines. Offload depth to `docs/`.
- Prefer deleting dead instructions over accumulating caveats.

## Maintenance Notes

1. Remove leftover `[bracket]` / TBD placeholders once filled
2. Update Commands when workflows change; rewrite Architecture on major layout changes
3. Delete anything the agent can infer from code
