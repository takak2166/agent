---
name: draft-pr
description: Create a draft pull request for the current branch with a structured PR body.
disable-model-invocation: true
---

# Draft PR
A skill to create a Draft PR for the current branch.

## Usage
```
/draft-pr -adr [URL]
```

Use when the user asks to create a draft PR, open a draft pull request, or invokes `/draft-pr`.

### Options
- `-adr [URL]`: Optional. A URL to an ADR (Architecture Decision Record) related to this PR

## Non-negotiables

1. If a PR already exists for the current branch, inform the user and **exit** — do not create a duplicate.
2. Always request Copilot as a code reviewer (`--reviewer @copilot` on create; fall back to `gh pr edit --add-reviewer @copilot` when create did not add Copilot).
3. Compose the PR body from `.github/PULL_REQUEST_TEMPLATE` — do not invent a different structure.

## Steps
1. Execute `gh pr list --head "$(git branch --show-current)" --json number,url,isDraft` to check if a PR for the current branch already exists. If the result is non-empty, inform the user with `number`, `url`, and `isDraft` from the JSON and exit
1. If the current branch has not been pushed to the remote, push it using `git push -u origin $(git branch --show-current)`
1. Read @.github/PULL_REQUEST_TEMPLATE to understand the PR body structure. If the file is missing or unreadable, inform the user and exit
1. Identify the ticket ID from the current branch name:
   - **Linear issue key** (e.g., `TAK-123`, `TSK-1234`): match pattern `[A-Z]+-\d+` in the branch slug
   - **Notion page ID or slug**: match the pattern used in this repository (infer from existing PRs or the PR template)
   - Example: branch `feature/TAK-123-some-description` → issue key `TAK-123`
1. Compose the PR body at `/tmp/<branch-slug>.md` following the template structure, where `<branch-slug>` is the current branch name with `/` replaced by `-` (for example, branch `feature/TAK-123-fix` → `/tmp/feature-TAK-123-fix.md`):
   - Fill each section heading from the template with a concise one-line summary
   - In the Reference section, include a ticket link derived from the ticket ID:
     - **Determine the ticket system** from repository context (PR template, recent PRs, README): look for `linear.app` vs `notion.so` URL patterns
     - **Linear**: link format `https://linear.app/<workspace>/issue/<issue-key>` — infer `<workspace>` from repo context (e.g., existing Linear URLs in the repo). When Linear MCP is available, prefer `get_issue` with the issue key to obtain the canonical URL
     - **Notion**: link format `https://www.notion.so/<org-name>/<page-id>` — infer `<org-name>` from repo context or existing PR templates
     - If the ticket system cannot be determined, include the ticket ID as plain text and leave a placeholder for the user to fill in the URL
     - The ADR link if provided via `-adr` option, otherwise write "None"
   - Leave optional sections (e.g., Debug List, screenshots) with placeholder text or "N/A" for the user to fill in later
1. Create the draft PR and request a Copilot code review using:
   ```bash
   gh pr create --draft --title "<concise title>" --body-file /tmp/<branch-slug>.md --reviewer @copilot
   ```
1. If Copilot was not added during create (e.g., older GitHub CLI), add it on the new PR with:
   ```bash
   gh pr edit --add-reviewer @copilot
   ```

## Notes
- The PR title should be concise and descriptive of the changes; when the diff is unavailable, derive the title from the branch slug and ticket ID
- Each section in the PR body should contain brief, clear summaries rather than lengthy explanations; when the diff is unavailable, derive one-line placeholders from the branch slug and ticket ID
- The workspace name (Linear) or organization name (Notion) for constructing the ticket URL should be inferred from the repository context or existing PR templates
- Copilot as reviewer requires GitHub CLI v2.88.0 or later and a plan that includes Copilot code review

## Restrictions
- Do not execute shell commands other than `gh pr list`, `git push`, `git branch --show-current`, `gh pr create`, and `gh pr edit`
- Use the Read tool for `.github/PULL_REQUEST_TEMPLATE`, README, and recent PR bodies when inferring ticket links or template structure
- Linear MCP (`get_issue`) may be used when available to resolve canonical Linear issue URLs
