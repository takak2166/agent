---
description: Fix underlying root causes rather than masking symptoms with defensive patches
applyTo: "**/*"
---

# Fix Root Causes

- **Never mask internal symptoms**: Do not patch an unexpected missing value, type error, or unexpected state by silently swallowing errors (e.g. empty `catch` blocks, arbitrary fallback defaults, blind retries, or unexamined null-coalescing) without understanding why the invalid state occurred.
- **Trace to the source**: Identify where the invalid state or invariant violation originated and fix it at that origin. When the origin is outside the codebase's control (e.g. a third-party bug or upstream contract), handle it at that boundary with explicit validation or a documented rationale.
