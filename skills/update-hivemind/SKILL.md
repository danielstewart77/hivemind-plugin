---
name: update-hivemind
description: Check for Hive Mind updates by comparing the local repo against origin/master. Shows available commits, affected areas, and impact. Performs the update on request.
user-invocable: true
---

# Update Hive Mind

### Step 1: Fetch and Diff

Run these in parallel:
- `git fetch origin master` — get latest remote state
- `git log HEAD..origin/master --oneline` — list commits not yet on local
- `git diff HEAD...origin/master --stat` — show which files/areas changed

If `git log` returns nothing, report: "Already up to date — no updates available." Done.

### Step 2: Summarise What's Available

From the commit log and diff stat, produce a plain-English summary:
- How many commits are pending
- Which subsystems are affected (skills, minds, tools, config, docs, etc.)
- Any commits that touch `docker-compose.yml`, `Dockerfile`, or `requirements.txt` — flag these as requiring a container rebuild

Present this as a concise briefing. Do not dump raw git output.

### Step 3: Wait for User

Ask: "Would you like to update, or do you have questions about specific changes?"

- If questions: answer them using `git show <sha>` or `git diff HEAD...origin/master -- <path>` as needed.
- If update requested: proceed to Step 4.
- If declined: done.

### Step 4: Perform Update

1. Confirm the working tree is clean: `git status`. If uncommitted changes exist, warn and ask whether to stash them first.
2. `git pull origin master --rebase`
3. If any of `docker-compose.yml`, `Dockerfile`, or `requirements.txt` changed: inform {{USER}} that a container rebuild is needed (`docker compose up -d --build`) — do not run it automatically.
4. Report what was applied.
