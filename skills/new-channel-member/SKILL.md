---
name: new-channel-member
description: Parses announcements that someone joined a channel (Slack, Cursor, Discord, etc.), fixes common typos like a missing space before "was", and suggests consistent follow-ups (welcome, access, docs, optional Linear issue). Use when the user pastes system copy, says who added whom, or runs /new-channel-member.
---

# New channel member

Use this skill when the user reports **who joined a channel** and **who invited or added them**—often as short system-style text or chat paste.

## Parse and normalize

1. **Extract three roles:** **invitee** (new member), **inviter** (who added them), **channel** (name or link if stated). If the channel is unnamed, ask one clarifying question or infer only from explicit URLs.
2. **Fix concatenation typos** in English pastes: a name immediately followed by **`as`** often means **` was`** (e.g. `kashiwaas added` → **Kashiwa was** added). Apply only when it yields grammatical "X was added … by Y"; do not rewrite intentional usernames.
3. Preserve **casing** the user prefers for display names; default to **sentence case** for prose summaries.

## After parsing

- Echo a **one-line confirmation** in clear English (or Japanese if the user is writing in Japanese), e.g. "Kashiwa was added to the channel by Takayuki."
- Offer **optional next steps** (user picks): onboarding checklist (repos, roles, calendar), a short welcome blurb, or filing work via **`linear-create-issue`** when Linear MCP is available and the user wants a tracked task.

## Restrictions

- **Do not** post to external services (Slack, Linear, GitHub) unless the user explicitly asks and the environment has the right tools and auth.
- **Do not** invent people or channels—if the sentence is still ambiguous after normalization, ask briefly.
