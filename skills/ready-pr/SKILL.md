---
name: ready-pr
description: Convert a draft pull request to ready for review after CI checks pass. Use when the user asks to mark a PR ready for review, convert a draft PR to ready, or invokes `/ready-pr`.
disable-model-invocation: true
---

# Ready PR
A skill to convert a Draft PR to Ready for Review.

## Usage
```
/ready-pr [PR number]
```

## Steps
1. Execute `gh pr list` command to check if a PR for the current branch already exists, and whether it is in Draft status. If no PR exists or the PR is not in Draft status, exit
1. Execute `gh pr checks --watch` command and wait for CI to complete
1. If CI failed, execute `gh pr checks --json name,bucket,link,workflow --jq '.[] | select(.bucket == "fail")'` command and report a summary to the user, then exit
1. Only if all CI checks pass, execute `gh pr ready [PR number]` command to mark it as Ready for Review

## Restrictions
- Do not execute any commands other than `gh pr list`, `gh pr checks`, and `gh pr ready`
