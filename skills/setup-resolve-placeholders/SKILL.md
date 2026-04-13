---
name: setup-resolve-placeholders
description: Collect real values for plugin placeholders ({{USER}}, {{PLANKA_*}}) and substitute them across all installed skill files. Run after setup-body so Planka credentials are available for auto-discovery.
user-invocable: true
tools: Bash, Read, Edit
---

# setup-resolve-placeholders

Scans installed skill files for unresolved placeholders and replaces them with real values. Safe to re-run — skips placeholders that are already resolved.

---

## Step 1 — Find skill files with unresolved placeholders

```bash
# Locate the plugin skills directory
SKILLS_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude-config}/skills"

# Find all SKILL.md files containing any placeholder
grep -rl '{{' "$SKILLS_DIR" --include="*.md" 2>/dev/null
```

If no files contain `{{...}}`: "All placeholders already resolved. Nothing to do." → stop.

Report: "Found N skill files with unresolved placeholders."

---

## Step 2 — Inventory which placeholders are present

```bash
grep -roh '{{[A-Z_]*}}' "$SKILLS_DIR" --include="*.md" | sort -u
```

Build a list of which placeholder tokens still need values. Only collect values for placeholders that are actually present — don't ask about placeholders that don't appear in any skill file.

---

## Step 3 — Collect {{USER}}

If `{{USER}}` is in the inventory:

Ask: "What is your name? (used in skill files where {{USER}} appears — e.g. 'Daniel')"

Store as `RESOLVED_USER`.

---

## Step 4 — Collect Planka IDs

If any `{{PLANKA_*}}` placeholder is in the inventory:

### 4a — Check Planka availability

```bash
python3 /usr/src/app/tools/stateless/planka/planka.py list-projects 2>/dev/null | head -5
```

If Planka is not reachable: "Planka is not running or credentials are not configured. Run `/setup-body` first to set up Planka, then re-run this step. Skipping Planka placeholder resolution."

### 4b — List projects and boards

```bash
python3 /usr/src/app/tools/stateless/planka/planka.py list-projects
```

Present the board list to the user. Ask: "Which board is your development board? (paste the board ID, or 'skip' to resolve Planka placeholders manually)"

If skip → note which Planka placeholders remain unresolved, continue to Step 5.

Store as `BOARD_ID`. Also capture `PROJECT_ID` from the same output.

### 4c — Auto-discover lists from board

```bash
python3 /usr/src/app/tools/stateless/planka/planka.py get-board --board-id "$BOARD_ID"
```

Parse the lists from the output. Present them:

```
Lists found on this board:
  Backlog        → <id>
  In Progress    → <id>
  Done           → <id>
  (others...)
```

Ask the user to confirm which list is Backlog, which is In Progress, which is Done. Pre-select based on name matching (case-insensitive). Allow correction.

Store: `BACKLOG_LIST_ID`, `IN_PROGRESS_LIST_ID`, `DONE_LIST_ID`.

### 4d — Discover labels

```bash
# Get board labels via Planka API directly
TOKEN=$(python3 /usr/src/app/tools/stateless/planka/planka.py list-projects 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('token',''))
except: pass
" 2>/dev/null)

# Fall back to direct auth if token not in list-projects output
if [ -z "$TOKEN" ]; then
  TOKEN=$(curl -sf -X POST http://planka:1337/api/access-tokens \
    -H "Content-Type: application/json" \
    -d "{\"emailOrUsername\":\"$(python3 -c "import sys; sys.path.insert(0,'/usr/src/app'); from core.secrets import get_credential; print(get_credential('PLANKA_EMAIL'))")\",\"password\":\"$(python3 -c "import sys; sys.path.insert(0,'/usr/src/app'); from core.secrets import get_credential; print(get_credential('PLANKA_PASSWORD'))")\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['item'])" 2>/dev/null)
fi

curl -sf "http://planka:1337/api/boards/$BOARD_ID/labels" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; [print(f\"{l['name']}: {l['id']}\") for l in json.load(sys.stdin).get('items',[])]"
```

Present labels. Ask the user to identify which label is Ada's, which is their own (owner), and which is low-priority. Pre-select based on name matching. Allow correction or manual entry if auto-discovery fails.

Store: `ADA_LABEL_ID`, `OWNER_LABEL_ID`, `LOW_PRIORITY_LABEL_ID`.

---

## Step 5 — Confirm before substitution

Present a summary table of all resolved values:

```
Placeholder resolution plan:
  {{USER}}                        → Daniel
  {{PLANKA_PROJECT_ID}}           → abc123
  {{PLANKA_BOARD_ID}}             → def456
  {{PLANKA_BACKLOG_LIST_ID}}      → ghi789
  {{PLANKA_IN_PROGRESS_LIST_ID}}  → jkl012
  {{PLANKA_DONE_LIST_ID}}         → mno345
  {{PLANKA_ADA_LABEL_ID}}         → pqr678
  {{PLANKA_OWNER_LABEL_ID}}       → stu901
  {{PLANKA_LOW_PRIORITY_LABEL_ID}}→ vwx234

  Skipped (manual resolution needed): <any skipped>

Proceed? (y/n)
```

---

## Step 6 — Substitute across all skill files

For each resolved placeholder, run a global find-and-replace across all `*.md` files in the skills directory:

```bash
# Example for {{USER}}
find "$SKILLS_DIR" -name "*.md" -exec \
  sed -i "s/{{USER}}/$RESOLVED_USER/g" {} \;
```

Repeat for each resolved placeholder.

After substitution, verify no `{{PLANKA_*}}` or `{{USER}}` remain:

```bash
grep -rl '{{USER}}\|{{PLANKA_' "$SKILLS_DIR" --include="*.md" 2>/dev/null
```

If any remain: list them — these are files that need manual attention.

---

## Step 7 — Report

```
Placeholder resolution complete.

  Resolved:  N placeholders across M skill files
  Remaining: N (listed above — manual resolution needed)

Your plugin is now live. Skills referencing Planka or your name
will use the real values without further configuration.
```
