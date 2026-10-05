---
description: Fix underlying root causes rather than masking symptoms with defensive patches
applyTo: "**/*"
---

# Fix Root Causes

- **Never mask internal symptoms**: Do not patch an unexpected missing value, type error, or unexpected state by silently swallowing errors (e.g. empty `catch` blocks, arbitrary fallback defaults, blind retries, or unexamined null-coalescing) without understanding why the invalid state occurred.
- **Trace to the source**: Identify where the invalid state or invariant violation originated and fix it at that origin within the codebase.
- **Validate at trust boundaries**: External inputs, third-party API responses, and process boundaries must be validated explicitly at the boundary. When the root cause is outside codebase control (e.g. third-party bug or upstream contract), handle it at the boundary with typed validation or documented rationale.
- **Eliminate unnecessary defenses**: Avoid stacking redundant protective checks inside internal trusted code. Prefer fixing or removing broken assumptions over accumulating defensive clutter.
