---
description: Assign each check to unit, integration, or end-to-end
applyTo: "**/*"
---

# Test placement

Assign each check to the testing layer that owns it.

- **Sibling role split**: This file assigns a check to unit, integration, or end-to-end. `verification-layering.instructions.md` covers formal, empirical, and structural verification. `verification-prove-it-works.instructions.md` requires proving a change with real execution and concrete output.
- **Unit tests own isolated branches and combinations**: Extract the decision logic and cover its branches and input combinations in unit tests.
- **Integration checks own boundaries**: Use an integration check where parts meet and the contract between them is what can fail.
- **End-to-end starts at one representative scenario**: Treat one high-value scenario on a critical flow as the default starting scope. Add another end-to-end scenario when it is an independent critical flow that the first scenario, together with unit and integration checks, would miss.
- **Negative example**: An end-to-end case for every branch, flag, or input combination. Cover those in unit tests. Stopping after one end-to-end scenario when a second, independent critical flow would still go untested by that scenario and by unit and integration checks is also wrong; add that flow and leave the remaining matrix in unit tests.
