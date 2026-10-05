---
name: draft-pr
description: Create a draft pull request for the current branch with a structured PR body.
disable-model-invocation: true
---

# Draft PR

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
4. **Public repositories** (`gh repo view --json visibility` → `PUBLIC`): do not put Linear issue keys, Notion page IDs, or links to Linear, Notion, Scrapbox (including `scrapbox.io`), or other internal-only trackers in the PR **title** or **body**. Branch names may still contain ticket IDs; strip them from outward-facing PR text.

## Integrated example (median path)

**User:** `/draft-pr` on a **private** repo, branch `feature/TAK-123-add-widget`, no open PR, branch not on remote yet.

1. `gh pr list --head "$(git branch --show-current)" --json number,url,isDraft` → `[]`
2. `gh repo view --json visibility` → not `PUBLIC`; read `.github/PULL_REQUEST_TEMPLATE` (before any push)
3. `git push -u origin $(git branch --show-current)`
4. Ticket `TAK-123`; Write tool creates `/tmp/feature-TAK-123-add-widget.md` from the template sections; Reference links the Linear issue URL inferred from repo context
5. `gh pr create --draft --title "Add widget (TAK-123)" --body-file /tmp/feature-TAK-123-add-widget.md --reviewer @copilot` → report PR URL

**User:** same repo, PR `#7` already open for current branch.

1. Step 1 returns non-empty JSON → inform user with `number`, `url`, `isDraft` and **exit** (no duplicate PR)

**User:** `/draft-pr` on a **public** repo, branch `feature/TAK-456-export-api`.

1. Step 1 as usual; step 2 → `gh repo view --json visibility` is `PUBLIC`; read template
2. Push, compose body: title `Export API` (no `(TAK-456)`); Reference uses `- Ticket: N/A` when the template expects a ticket line (no ID, no link), `- ADR: None`; no `linear.app` / `notion.so` / `scrapbox.io` links anywhere in the body
3. Create draft PR as usual

## Before `gh pr create`

Mark each item before Step 7:

```
- [ ] Step 1 — no open PR for current branch
- [ ] Step 2 — visibility: public vs non-public
- [ ] Step 3 — template read (and README / recent PR sample if needed)
- [ ] Step 4 — branch pushed
- [ ] Steps 5–6 — body file written at /tmp/<branch-slug>.md (public: no ticket IDs or internal tracker links)
- [ ] Step 7–8 — draft created; @copilot on PR
```

## Steps

1. Execute `gh pr list --head "$(git branch --show-current)" --json number,url,isDraft` to check if a PR for the current branch already exists. If the result is non-empty, inform the user with `number`, `url`, and `isDraft` from the JSON and exit
2. Execute `gh repo view --json visibility` and treat the repository as **public** when `visibility` is `PUBLIC`; otherwise treat it as non-public (private or internal)
3. Read `.github/PULL_REQUEST_TEMPLATE` to understand the PR body structure. If the file is missing or unreadable, inform the user and exit. Finish this Read, any README Read, and any recent-PR sampling Step 6 needs, **before pushing**. Recent PR bodies are not workspace files — when inferring ticket URL patterns, run `gh pr list --limit 5 --json title,body` and use that output (do not use disallowed git/gh commands)
4. Push the branch with `git push -u origin $(git branch --show-current)`. Always run it — no other git command is allowed to check push state, and the command is safe when the branch is already up to date
5. **Non-public repos only:** identify the ticket ID from the current branch name only — never take an ID from README examples or existing PRs:
   - **Linear issue key** (e.g., `TAK-123`, `TSK-1234`): match pattern `[A-Z]+-\d+` in the branch slug
   - **Notion page ID** (32 hex characters or a UUID in the branch slug) **or slug**: match the pattern used in this repository (infer from existing PRs or the PR template)
   - Example: branch `feature/TAK-123-some-description` → issue key `TAK-123`
   - No ticket ID found: write `- Ticket: [TODO: fill in ticket ID and URL]` in Reference, and drop the `(<ticket-key>)` part of the title
   - **Public repos:** skip this step for PR text — do not copy ticket IDs from the branch into the title or body
6. Compose the PR body with the Write tool (not shell) at `/tmp/<branch-slug>.md` following the template structure, where `<branch-slug>` is the current branch name with `/` replaced by `-` (for example, branch `feature/TAK-123-fix` → `/tmp/feature-TAK-123-fix.md`):
   - Keep the template's headings and checklist items; fill each section with a concise one-line summary and replace HTML comments and empty checklist items with content or `N/A`; when the changes are unknown (see Notes), write the Test plan item as `- [ ] N/A (to be filled in)` rather than inventing checks
   - **Non-public repos only:** write every spot the user must fill in as visible text such as `[TODO: fill in ticket URL]`, never as an HTML comment
   - **Reference — public repo:** omit any ticket / tracking bullet (no issue keys, no Linear / Notion / Scrapbox URLs). If the template expects a ticket line, use `- Ticket: N/A` with no link and no ID. For **ADR**, include `- ADR: <url>` only when `-adr` was passed **and** the URL is not Linear, Notion, or Scrapbox; otherwise `- ADR: None`
   - **Reference — non-public repo:** include a ticket link derived from the ticket ID:
     - **Determine the ticket system** from repository context (PR template, recent PRs, README): look for `linear.app` vs `notion.so` URL patterns
     - **Linear**: link format `https://linear.app/<workspace>/issue/<issue-key>` with no title slug, even when existing URLs have one — read `<workspace>` from the Linear URLs in the README, PR template, or recent PR bodies. When Linear MCP is available, `get_issue` with the issue key may confirm the workspace; the link still uses the slug-free format above. If it fails or is unavailable, use the README-derived workspace
     - **Notion**: link format `https://www.notion.so/<org-name>/<page-id>` — use `<page-id>` exactly as it appears in the branch name (no title slug) and infer `<org-name>` from repo context or existing PR templates (from a README URL take only the org name, never its page ID or slug)
     - If the ticket system cannot be determined, write `- Ticket: <ticket-id> [TODO: fill in URL]` and do not invent a workspace
     - Format **Reference** as bullets: ticket line as `- Ticket: [<ticket-id>](<url>)` when the URL is known; ADR line as `- ADR: <url>` when `-adr` was passed, otherwise `- ADR: None`
   - Leave optional sections (e.g., Debug List, screenshots) with placeholder text or "N/A" for the user to fill in later
7. Create the draft PR and request a Copilot code review using:
   ```bash
   gh pr create --draft --title "<concise title>" --body-file /tmp/<branch-slug>.md --reviewer @copilot
   ```
8. If `gh pr create` created the PR but its output shows `@copilot` was not added (a warning or error naming the reviewer, e.g., older GitHub CLI), add it with the command below. It targets the current branch's PR, so pass no PR argument. Never re-run `gh pr create`:
   ```bash
   gh pr edit --add-reviewer @copilot
   ```

## Expected output

**Created:** draft PR URL, title, and that `@copilot` was requested as reviewer.

**Stopped early:** existing PR (`number`, `url`, `isDraft`), missing/unreadable template, or push/create failure — state what blocked progress and do not create a duplicate PR.

## Notes
- The PR title should be concise and descriptive of the changes; this skill runs no diff command, so unless the conversation already describes the changes, derive `<phrase>` from the branch slug (type prefix and ticket token removed, hyphens → spaces, first word capitalised, no extra verb). **Non-public:** append ` (<ticket-key>)` for Linear keys only (omit for Notion IDs or when no ticket was found), e.g. `Add widget (TAK-123)`. **Public:** use `<phrase>` only — never append issue keys or paste ticket IDs from the branch
- Each section in the PR body should contain brief, clear summaries rather than lengthy explanations; when the changes are unknown, use the PR title as the Summary line (on public repos, that title must not contain ticket IDs)
- On public repos, do not add Linear / Notion / Scrapbox links anywhere in the body (Summary, Reference, checklist notes, etc.), even if the template or recent private PRs show them
- The workspace name (Linear) or organization name (Notion) for constructing the ticket URL should be inferred from the repository context or existing PR templates
- Copilot as reviewer requires GitHub CLI v2.88.0 or later and a plan that includes Copilot code review

## Restrictions
- Do not execute shell commands other than `gh pr list`, `gh repo view`, `git push`, `git branch --show-current`, `gh pr create`, and `gh pr edit` (the `$(git branch --show-current)` inside those commands is covered by this list; no `ls`, `cat`, or `git diff`)
- Use the Read tool for `.github/PULL_REQUEST_TEMPLATE` and README when inferring ticket links or template structure; use `gh pr list --limit 5 --json title,body` (allowed) to sample recent PR bodies — not `git diff`, `gh pr view`, or other disallowed commands
- Linear MCP (`get_issue`) may be used on **non-public** repos when available to confirm the Linear workspace; never paste MCP output (IDs or URLs) into a public PR
