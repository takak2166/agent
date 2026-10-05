---
description: Verify changes with real execution and actual output, not proxies or assumptions
applyTo: "**/*"
---

# Verification: Prove It Works

- **Never declare completion based on proxy indicators alone**: Passing builds, clean typechecks, or lint checks are necessary baselines, but do not prove that runtime behavior is correct.
- **Inspect actual outputs for behavioral changes**: When changing executable code, run the feature, command, or test, and verify concrete runtime output or return values before reporting completion.
- **Documentation and static assets**: For changes that have no runtime execution (e.g. documentation, instructions, pure configuration), verify via linter/validator, syntax check, and confirming referenced paths and symbols exist.
- **Concise evidence over raw dump**: Report the command run and cite key lines or summarized output that prove success. Do not paste full unedited logs.
- **Explicit gaps over assumption**: If an action cannot be executed locally (e.g. requires production credentials, external hardware, or destructive side effects), explicitly state what could not be run and what proxy evidence was verified instead.
- **Test behavior, not implementation**: When adding or updating tests, verify external contracts and behavioral outcomes rather than tautological assertions that simply mirror mock return values.
