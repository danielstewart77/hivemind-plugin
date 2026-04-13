---
name: planka
description: Manage Planka Kanban board cards and projects
user-invocable: false
---

# Planka Tool

Interact with the Planka Kanban board.

## Usage

```bash
python3 /usr/src/app/tools/stateless/planka/planka.py <command> [args]
```

**Do not use the venv path** — the tool runs on host Python using `python3`. The venv path is stale.

## Credentials

Credentials are stored in the keyring (`hive-mind` service):

| Key | Value |
|-----|-------|
| `PLANKA_EMAIL` | stored in keyring (set during `/setup-body`) |
| `PLANKA_PASSWORD` | stored in keyring |
| `PLANKA_URL` | `http://planka:1337` |

`get_credential()` reads keyring first, then falls back to env vars. **Do not override with env vars** — keyring takes precedence. If you pass env vars expecting them to override, they will be silently ignored if keyring has a value.

### If the tool returns 401

The keyring has stale or wrong credentials. Diagnose first:

```bash
python3 -c "
import sys; sys.path.insert(0, '/usr/src/app')
from core.secrets import get_credential
print('EMAIL:', get_credential('PLANKA_EMAIL'))
print('URL:', get_credential('PLANKA_URL'))
"
```

If URL is a LAN IP instead of internal Docker hostname, fix it:

```bash
python3 -c "
import sys; sys.path.insert(0, '/usr/src/app')
import keyring
keyring.set_password('hive-mind', 'PLANKA_URL', 'http://planka:1337')
print('Fixed.')
"
```

### If the tool returns "No module named 'requests'" or "No module named 'keyring'"

Host Python is missing dependencies. Install:

```bash
pip install requests keyring keyrings.alt --break-system-packages -q
```

Safe — small packages, no compiled extensions. Do NOT install pydantic or fastapi this way (breaks pydantic_core in the test environment).

### If requests gives a `RequestsDependencyWarning` about chardet

Warning only, not an error. Tool still works. To silence:

```bash
pip install charset-normalizer --break-system-packages -q
```

## Commands

- `list-projects` — List all projects and boards (returns project IDs, board IDs)
- `get-board --board-id <id>` — Get board with lists and cards (returns list IDs)
- `list-labels --board-id <id>` — List all labels on a board with IDs (used by `/setup-resolve-placeholders` for auto-discovery)
- `get-card --card-id <id>` — Get card details
- `move-card --card-id <id> --list-id <id>` — Move card to list
- `add-comment --card-id <id> --text "<text>"` — Add comment
- `update-card --card-id <id> [--name "..."] [--description "..."]` — Update card
- `assign-label --card-id <id> --label-id <id>` — Assign label
- `create-card --list-id <id> --name "..." [--description "..."] [--card-type story]` — Create card

## Known IDs (Hive Mind board)

| Name | Type | ID |
|------|------|----|
| Hive Mind | Project | `{{PLANKA_PROJECT_ID}}` |
| Development | Board | `{{PLANKA_BOARD_ID}}` |
| Backlog | List | `{{PLANKA_BACKLOG_LIST_ID}}` |
| In Progress | List | `{{PLANKA_IN_PROGRESS_LIST_ID}}` |
| Done | List | `{{PLANKA_DONE_LIST_ID}}` |
| Ada label | Label | `{{PLANKA_ADA_LABEL_ID}}` |
| {{USER}} label | Label | `{{PLANKA_OWNER_LABEL_ID}}` |

Use these directly — no need to look them up first.

## Assigning Labels (not supported by CLI — use curl)

The `assign-label` command has a known issue with the card-labels endpoint. Use curl directly:

```bash
TOKEN=$(curl -s -X POST http://planka:1337/api/access-tokens \
  -H "Content-Type: application/json" \
  -d "{\"emailOrUsername\":\"$(python3 -c \"import sys; sys.path.insert(0,'/usr/src/app'); from core.secrets import get_credential; print(get_credential('PLANKA_EMAIL'))\")\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['item'])")

curl -s -X POST "http://planka:1337/api/cards/<card-id>/card-labels" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"labelId":"<label-id>"}'
```

## Output

JSON with operation results.
