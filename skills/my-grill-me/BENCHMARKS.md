# BENCHMARKS — my-grill-me

## Empirical — Round 1

| Scenario | Run ID | Agent ID | [critical] | Accuracy |
|----------|--------|----------|------------|----------|
| product-requirements delegates grill | MG-A | bc-3f5c1872-b5f0-52db-ba8d-f321b68f4278 | pass | 100% |
| Ambient “use Redis?” no attach | MG-B | bc-fba46991-cf8d-5807-95a6-4db41fd113e3 | pass | 100% |

## Optimizer benchmark — Round 1

| Scenario | Cell | Run ID | Agent ID | Score % |
|----------|------|--------|----------|---------|
| Ambient Redis question | without | MG-OPT-WO | bc-9d803bed-ccc5-5c68-9a03-c5363765a521 | 100 |
| Ambient Redis question | with | MG-OPT-WS | bc-75e7a752-7b50-5dc0-816f-3c61b6ff982b | 100 |

**Mean with:** 100% · **Mean without:** 100% · **Δ:** 0pp

## Empirical — Round 2

| Scenario | Run ID | Agent ID | [critical] |
|----------|--------|----------|------------|
| Parent delegation + question-delivery ref | MG-R2-A | bc-dd22a71d-8a0e-5ed1-98f1-10989d6e997e | pass |
