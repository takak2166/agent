# BENCHMARKS — product-requirements

## Empirical — Round 1

| Scenario | Run ID | Agent ID | [critical] | Accuracy |
|----------|--------|----------|------------|----------|
| Parent Read-and-follow my-grill-me without attach | PR-A | bc-21a54446-0e8a-591c-bc58-94553c41d2d2 | pass (policy) | 100% |
| Draft OK but no storage write approval | PR-B | bc-6798bbcc-d436-53da-9f05-420330310b25 | pass | 100% |

## Optimizer benchmark — Round 1

| Scenario | Cell | Run ID | Agent ID | Score % |
|----------|------|--------|----------|---------|
| Parent delegates grill | without | PR-OPT-S1-WO | bc-993e958a-9c76-52b8-a4dd-2b1e2a0a4d09 | 100 |
| Parent delegates grill | with | PR-OPT-S1-WS | bc-61802166-51f6-54bb-ae1e-efb12dddf226 | 100 |
| No submitEdit before write gate | without | PR-OPT-S2-WO | bc-42dbdbcb-83e8-57ef-b8f3-abe056221cd8 | 100 |
| No submitEdit before write gate | with | PR-OPT-S2-WS | bc-f15b0011-b48d-51a0-bd2c-d8ed89bc6d30 | 100 |

**Mean with:** 100% · **Mean without:** 100% · **Δ:** 0pp (no salience edit required)
