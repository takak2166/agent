# Optional sections (only when shared rules are absent)

Insert **after** Layout notes (or after Conventions & gotchas if Layout notes is omitted) when Step 4 finds **no** shared always-on rules. Keep short.

## Core Principles

- **Line budget:** Non-blank, non-HTML-comment lines = instruction body (target **30–50**). Whole file ≤**75** lines. Offload depth to `docs/`.
- Prefer deleting dead instructions over accumulating caveats.
- Do not duplicate language, dependency lists, standard install/test/lint, or directory maps the agent can read from manifests and the tree.

## Maintenance Notes

1. Remove leftover `[bracket]` / TBD placeholders once filled
2. Refresh **Commands (non-default only)** when custom workflows change; trim **Layout notes** when structure is obvious again
3. Delete anything the agent can infer from code, manifests, README, or shared rules
