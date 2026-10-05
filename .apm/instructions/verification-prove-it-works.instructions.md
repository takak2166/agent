---
description: Verify changes with real execution and actual output, not proxies or assumptions
applyTo: "**/*"
---

# Verification: Prove It Works

- **Never declare completion based on proxy indicators alone**: Passing builds, clean typechecks, or lint checks do not prove that runtime behavior is correct. When changing executable code, run the feature, command, or test and verify the concrete output before reporting completion.
- **Documentation and static assets**: For changes that have no runtime execution (e.g. documentation, instructions, pure configuration), verify via linter/validator, syntax check, and confirming referenced paths and symbols exist.
- **Test behavior, not implementation**: When adding or updating tests, verify external contracts and behavioral outcomes rather than tautological assertions that simply mirror mock return values.
