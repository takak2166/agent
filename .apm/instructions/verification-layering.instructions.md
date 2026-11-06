---
description: Layer formal, empirical, and structural verification; humans own spec correctness
applyTo: "**/*"
---

# Verification: Layering and Intent

- **Sibling role split**: This file covers verification layering and the gap between formal specifications and human intent or operational reality; `verification-prove-it-works.instructions.md` requires proving changes with real execution and concrete outputs, not proxy signals alone.
- **Formal methods bound code to a spec, not intent to reality**: Proofs and model checking show that an implementation satisfies a formal specification under stated assumptions. They do not establish that the spec matches what people actually need. Only humans judge whether requirements, UX, and tradeoffs are right.
- **Prefer layered verification**: Combine structural constraints (types, lint, API design, refactors that narrow invalid states) with empirical checks (tests, evals, real runs against production-like conditions) and formal verification where rigor or safety margins justify the cost. No single layer catches every class of failure.
- **Shrink the human review surface**: When designing or reviewing verification, make behavior, invariants, and assumptions explicit in code, tests, and docs so reviewers focus on intent and gaps—not on reconstructing implicit behavior. A passing formal or static check is not a substitute for intent review or empirical confirmation that the change does what stakeholders expect.
- **Pair formal and empirical when both apply**: When using formal artifacts (specs, proofs, verified models), also run empirical checks that exercise the same behavior at runtime so drift between the model and deployed code is caught before merge.
