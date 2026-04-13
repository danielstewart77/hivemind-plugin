---
name: save-memory
description: Step agent that executes memory writes from the routing manifest. Loads save specs once per run, processes each chunk per its destination, handles conflict detection and user interaction, then executes writes via memory_store and graph_upsert.
tools: Read, Write, Bash
model: sonnet
maxTurns: 50
---

# save-memory

Execute memory writes for all chunks in the routing manifest.

## Input

Parse from the prompt:
- `session_path`: temp directory containing routing-manifest.md

## Process

### Step 1 — Read routing manifest

Read `{session_path}/routing-manifest.md`. Extract all chunks with their classes and actions.

### Step 2 — Load save specs once

Scan the manifest for all action types present:
- Any `save-vector` chunks → read `.claude/skills/semantic-memory-save/SKILL.md` once.
- Any `save-graph` chunks → read `.claude/skills/knowledge-graph-save/SKILL.md` once.
- Any `pin-memory` chunks → read `.claude/skills/pin-memory-action/SKILL.md` once.
- Any `notify` chunks → read `.claude/skills/notify-action/SKILL.md` once.

Do not reload specs per chunk — load once, apply to all relevant chunks.

### Step 3 — Process each chunk

For each chunk in the manifest, apply the procedure from the loaded spec for each of its actions.
A chunk may have multiple actions — execute all of them.

Follow the spec exactly: run searches before writing, surface conflicts to {{USER}}, wait for decisions before acting.

### Step 4 — Confirm

After all chunks are processed, report a brief summary:
- How many chunks saved to vector store
- How many saved to knowledge graph
- How many pinned to MEMORY.md
- How many reminders set
- Any skipped or failed

## Exit Protocol

`RESULT: PASS` — all chunks processed (saved, notified, or intentionally skipped with user input).
`RESULT: FAIL | {reason}` — a write failed, a spec could not be loaded, or an unresolvable error occurred.
