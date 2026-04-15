---
name: create-story
description: "Create a Planka story card with proper structure. Use when {{USER}} wants to create a new story/task on the board."
argument-hint: "[title]"
user-invocable: true
tools: Read, Write
---

# Create Story

## Board Reference

- **Project**: Hive Mind (`{{PLANKA_PROJECT_ID}}`)
- **Board**: Development (`{{PLANKA_BOARD_ID}}`)

### List IDs

| Column | ID |
|--------|----|
| Backlog | `{{PLANKA_BACKLOG_LIST_ID}}` |
| In Progress | `{{PLANKA_IN_PROGRESS_LIST_ID}}` |
| Done | `{{PLANKA_DONE_LIST_ID}}` |

### Label IDs

| Label | ID |
|-------|----|
| Ada | `{{PLANKA_ADA_LABEL_ID}}` |
| owner | `{{PLANKA_OWNER_LABEL_ID}}` |
| Low priority | `{{PLANKA_LOW_PRIORITY_LABEL_ID}}` |

## Procedure

1. **Get title.** Use `$ARGUMENTS` if provided, otherwise ask.

2. **Determine column.** Ask: "Should this go to In Progress (ready to work) or Backlog (not yet ready)?" Default: **In Progress** if it will be worked soon; Backlog only if explicitly deferred.

3. **Determine label.** Ask: Ada, {{USER}}, or Low priority? Default: Ada for autonomous work, {{USER}} for things requiring host access or human decisions.

4. **Develop user acceptance criteria.** Before writing the spec, ask {{USER}} for a use scenario — a concrete example of how he'd use the feature end-to-end. Collaborate to turn that into a full set of acceptance criteria:
   - Walk through the scenario step by step
   - Identify edge cases and decision points (what happens when X?)
   - Ask clarifying questions until the criteria are specific and testable
   - The final acceptance criteria should read like a checklist someone could run through to verify the feature works

5. **Write or verify the spec.** Every story must have a spec file at `specs/<name>.md` before the card is created. The spec must include:
   - **User requirements** — what the user wants to accomplish, described from their perspective
   - **User acceptance criteria** — the full checklist developed in Step 4
   - **Technical specification** — how it works: architecture, tool functions, data flow
   - **Code references** — files that will be created or modified, with paths
   - **File locations** — where new code will live (e.g. `agents/browser.py`, `.claude/skills/browse/SKILL.md`)
   - **Implementation order** — numbered steps

   If the spec already exists, verify it covers all the above. If not, fill in the gaps.

6. **Write card description.** Keep it short — the spec is the source of truth. Include:
   - One sentence overview
   - `Full spec: specs/<filename>.md` — link to the file, do NOT summarize the spec content here

   Do NOT copy acceptance criteria or implementation details into the card description. The overnight pipeline reads the spec file directly.

7. **Create card.** Call `planka_create_card` with list_id, name, description.

8. **Assign label.** Call `planka_assign_label` with card_id and label_id (Ada label ID is `{{PLANKA_ADA_LABEL_ID}}`).

9. **Assign card member.** If label is Ada, also add Ada as a card member so the card appears in Ada's assignment view (separate from the label):

```bash
PLANKA_TOKEN=$(python3 /usr/src/app/tools/stateless/planka/planka.py list-projects 2>/dev/null \
  | python3 -c "import sys,json; print(json.load(sys.stdin))" 2>/dev/null || true)
# Use the API directly — planka.py does not have a card-memberships command
curl -sf -X POST "http://planka:1337/api/cards/<card_id>/card-memberships" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PLANKA_AUTH_TOKEN" \
  -d '{"userId":"{{PLANKA_ADA_USER_ID}}"}'
```

Simpler: use the Python venv directly:
```bash
python3 -c "
import requests, subprocess
planka_pass = subprocess.run(['grep','PLANKA_ADMIN_PASSWORD','/usr/src/app/.env'],capture_output=True,text=True).stdout.strip().split('=',1)[1]
token = requests.post('http://planka:1337/api/access-tokens', json={'emailOrUsername':'daniel.stewart77@gmail.com','password':planka_pass}).json()['item']
r = requests.post('http://planka:1337/api/cards/<card_id>/card-memberships', json={'userId':'{{PLANKA_ADA_USER_ID}}'}, headers={'Authorization':f'Bearer {token}'})
print(r.status_code)
"
```

10. **Confirm.** Report: card title, column, label, and assignee.

## Naming Convention

Use bracketed prefixes: `[Feature]`, `[Bug]`, `[DevOps]`, `[Security]`, `[Memory]`, `[Pipeline]`, `[Integration]`, `[UX]`, `[Roadmap]`.
