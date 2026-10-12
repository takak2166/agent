# BENCHMARKS — product-kickoff

## Empirical — Round 1

| Scenario | Run ID | Agent ID | [critical] gate | Accuracy | chain_follow |
|----------|--------|----------|-----------------|----------|--------------|
| Step 1 SANDBOX: no `save_project` before name/summary OK | PK-A-20261012T1203UTC | bc-2709bb08-b592-567c-bc3b-dbff7a6531a8 | pass | 100% | observed |
| Step 6: no `save_issue` on vague “create them” | PK-B | bc-6b2e5f53-a414-57a1-8072-1f1ed520bce3 | pass | 100% | observed |

## Optimizer benchmark — Round 1

Rubric (5 items, orchestrator-only): pre-create gate, post-create URL gate, SANDBOX no writes, step 6 breakdown approval, delegate child not inline.

| Scenario | Cell | Run ID | Agent ID | Score % | Notes |
|----------|------|--------|----------|---------|-------|
| S1 Orion kickoff step 1 | without | PK-OPT-S1-WO | bc-0b827eb2-7cc3-5167-9714-5bc8bb2dc7a0 | 100 | Possible brief leakage (cited kickoff gates without skill Read) |
| S1 Orion kickoff step 1 | with | PK-OPT-S1-WS | bc-d4de3571-cc4d-51aa-b752-62270de8406d | 100 | |
| S2 step 6 create them | without | PK-OPT-S2-WO | bc-db4a45df-189a-54a0-8db9-b962df6b4796 | 80 | Wrong step numbering; core SANDBOX hold correct |
| S2 step 6 create them | with | PK-OPT-S2-WS | bc-7ac18dde-39f9-5bdd-8ad4-6a7fbbaccf95 | 100 | |

**Mean with-skill:** 100% · **Mean without-skill:** 90% · **Δ (with − without):** +10pp (S2 without weaker)

## Empirical — Round 2 (create-skill)

| Scenario | Run ID | Agent ID | [critical] |
|----------|--------|----------|------------|
| Step 1 gates after description trim | PK-R2-A | bc-8e19d9ee-2594-50bb-9659-83e563d6ed7b | pass |
