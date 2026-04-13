---
name: prune-config-memory
description: Audits all technical-config memories in the vector store against the live codebase. Verifies each entry's codebase_ref still exists and the stored fact is still accurate. Deletes obsolete entries, updates stale ones, and leaves accurate ones untouched.
user-invocable: true
---

# Prune Config Memory

Audits technical-config memories in the Neo4j vector store against the live codebase. For each stored entry: verify the referenced code still exists, compare the stored fact to current reality, then delete, update, or keep accordingly.

---

## Step 1 — Retrieve All technical-config Entries

Call memory_list with data_class: technical-config and agent_id: ada to get all stored entries. If the result is paginated, fetch all pages before proceeding.

Build a working list. Each entry has at minimum:
- id — the memory ID (needed for delete/update)
- content — the stored fact
- codebase_ref — file paths or symbols this fact references (may be null)
- as_of — when it was stored

Report: "Found {N} technical-config entries. Beginning audit."

---

## Step 2 — Audit Each Entry

Process entries one at a time. For each entry:

### 2a — Entries without codebase_ref

If codebase_ref is null or empty, the fact is a high-level architectural claim with no specific code anchor.

- Read the content carefully. Is it still plausible given current system architecture?
- If clearly obsolete (references removed systems, old names, superseded designs): flag for deletion — confirm with user before deleting.
- If still plausible: keep — no action needed.

### 2b — Entries with codebase_ref

Parse codebase_ref as a comma-separated list of file paths or symbols.

For each referenced path:

1. Check existence — use Glob to verify the file exists at the given path.
   - If the file does not exist: check if it was renamed (Glob for the filename pattern). If found at a new path, note the new path. If not found anywhere: mark the reference as broken.

2. Check content — if the file exists, use Grep or Read to find the specific fact the memory claims.
   - Search for key terms from the memory content in the file.
   - Read surrounding context to understand current state.

3. Classify the entry based on what you find:

| Finding | Action |
|---|---|
| File missing, no rename found | Delete — entry is obsolete |
| File exists, fact is accurate | Keep — no action |
| File exists, fact is slightly stale (path changed, value differs) | Update — rewrite content to reflect current state |
| File exists but the code has been removed/refactored away | Delete — entry is obsolete |
| Multiple refs: some valid, some broken | Update — fix the codebase_ref and content |

---

## Step 3 — Execute Changes

Process all classified entries:

Deletions:
- Call memory_delete with the entry id.
- Log: "Deleted: {short content summary}"

Updates:
- Call memory_update with the entry id, updated content, and corrected codebase_ref.
- Log: "Updated: {short content summary} -> {what changed}"

Kept:
- Log: "OK: {short content summary}"

Do not ask for confirmation on individual entries unless:
- The entry has no codebase_ref and deletion is being considered
- The content is ambiguous and you genuinely cannot determine if the fact is still true

For clear-cut cases (file missing, fact verifiably wrong, or fact verifiably correct), proceed without prompting.

---

## Step 4 — Report

Output a summary table:

  technical-config audit complete.

    Kept:    {N}
    Updated: {N}
    Deleted: {N}
    Skipped (needs review): {N}

  Details:
  [list each action taken, one line per entry]

If entries were skipped for manual review, list them with the reason.
