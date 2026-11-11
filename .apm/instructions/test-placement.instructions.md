---
description: Assign each check to unit, integration, or end-to-end
applyTo: "**/*"
---

# Test placement

Assign each check to the testing layer that owns it.

- **Sibling role split**: This file assigns each check to unit, integration, or end-to-end. For the canonical role map of the three verification instruction files, see `verification-layering.instructions.md` (verification layering and the gap between formal specifications and human intent or operational reality; `verification-prove-it-works.instructions.md` for real execution and concrete outputs). Do not duplicate that map here.
- **Unit tests own observable behavior in isolation**: Cover observable behavior with representative inputs and boundary values, isolated from I/O, network, and clock. Do not mandate extracting production logic.
- **Integration checks own boundaries**: Use an integration check where parts meet and the contract between them is what can fail.
- **End-to-end starts at one representative scenario**: When a change touches a critical flow, treat one high-value end-to-end scenario on that flow as the default scope. Add a second end-to-end scenario only when that second scenario covers an independent critical flow that the first scenario, together with unit and integration checks, would miss; otherwise stop after that first scenario.
- **Negative example**: An end-to-end case for every branch, flag, or input combination. Cover those in unit tests.
