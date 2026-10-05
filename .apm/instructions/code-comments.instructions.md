---
description: Keep Linear references out of comments and prefer self-documenting code over narration
applyTo: "**/*"
---

# Code Comments

Do not leave Linear references in source code comments.

- Do not include Linear URLs (for example `https://linear.app/...`)
- Do not include Linear issue IDs (for example `TAK-123`)

This includes `TODO`, `FIXME`, and other annotation comments. Track work in Linear, pull requests, or commit messages instead of embedding those identifiers in the code.

## Self-documenting code over narration

- **No narration (WHAT)**: Do not write comments that merely restate what the code visibly does. If internal behavior is confusing, prefer renaming or refactoring symbols so the code expresses its own structure.
- **Preserve rationale and invariants (WHY)**: Comments are appropriate when explaining non-obvious context that code cannot easily express:
  - Complex domain or business rules and rationale
  - Concurrency, ordering, or security invariants
  - Workarounds or constraints forced by external dependencies or platforms
  - Public API contract documentation
  - Compiler and tooling directives (e.g. `// prettier-ignore`, `@ts-expect-error` with rationale)
  - Legal and license headers
