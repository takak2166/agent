# Agent Guidelines

<!-- Lean context: only what shared rules and the codebase cannot supply. Update in-place; do not sprawl. -->

## Project-specific context

<!-- Omit this section when README title + tree make the purpose obvious. Otherwise 1–3 bullets or one short paragraph. -->
[Why this repo exists or how it differs from a stock app template — not language, deps, or folder inventory]

---

## Commands (non-default only)

<!-- Omit the entire section when install/run/test/lint are standard for the stack and visible in manifest, Makefile, or README. -->

```bash
# Wrappers, custom targets, or workflows the agent would miss without this file
[example: ./scripts/dev.sh]   # not plain npm install / go test ./...
```

---

## Conventions & gotchas

- [Conventions that differ from tool or ecosystem defaults]
- [Pitfalls, ordering constraints, or "never do X" for this repo]
<!-- Do not paste generic clean-code advice (e.g. "prefer explicit over clever") — project-specific only -->

---

## Layout notes (optional)

<!-- Omit when top-level dirs are self-explanatory (e.g. src/, cmd/). List only boundaries the tree does not explain. -->

```
[path/]    [one line — non-obvious role only]
```
