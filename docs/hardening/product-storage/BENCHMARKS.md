# BENCHMARKS — product-storage

composer-2.5 · SANDBOX (no `previewEdit` / `submitEdit`; stub `readPage` only)

## Optimizer benchmark — Round 1

| Scenario | Cell | RUN_ID | Agent ID | Score % |
|----------|------|--------|----------|---------|
| S1 Requirements: draft OK, write to Cosense not approved (`persistent=false`) | with-skill | PST-S1-WS | bc-8785795e-4e51-5d6d-b619-596c53b4a6cc | 100 |
| S1 Draft OK, no upload OK | without-skill | PST-S1-WO | bc-beeb31c5-62cb-5f35-941e-6efc9a99a384 | 100 |
| S2 `readPage` `persistent=true` — abort create, ask user | with-skill | PST-S2-WS | bc-57d82d5d-85d0-5e4a-afc9-0169e25d50ca | 100 |
| S2 Existing page same title | without-skill | PST-S2-WO | bc-6a46a477-701e-5cf6-b95e-08cc091ec892 | 100 |

**Mean with:** 100% · **Mean without:** 100% · **Δ:** 0pp
