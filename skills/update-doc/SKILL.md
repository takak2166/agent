---
name: update-doc
description: Scans and updates all markdown documents in the project to match the current source code.
disable-model-invocation: true
---

# Update Document
A skill to update documentation in the current project.

## Usage
```
/update-doc
```

## Non-negotiables

1. **User confirmation before edits** — report each contradiction found; apply markdown fixes only after the user approves (or approves a batch).
2. Use only commands listed under **Restrictions** (`find`, `cat`).

## Expected output

1. **Scan summary** — count of markdown files found.
2. **Contradiction report** — per file: path, summary of mismatch, proposed fix (if any).
3. **Applied changes** — list of files edited (after approval) with brief diff description.
4. **Review request** — ask the user to review all corrections.

## Steps
1. Check all markdown documents in the project using the `find . -type f -name '*.md'` command
  - If none are found, exit
1. For each document found, repeat the following:
  1. Check the document content using the `cat` command and create a summary
  1. Examine whether the document content contradicts the source code state
  1. If contradictions exist, add them to the contradiction report and **wait for user approval** before editing
  1. After approval, correct the approved documents only
1. After all documents have been corrected, request a review from the user

## Restrictions
- Do not execute commands other than find and cat
- Do not edit files other than markdown
