---
name: remote-admin
description: Manage SSH sessions on remote hosts via the remote-admin bridge service. Create sessions, run commands, stream interactive shells. Credentials are resolved automatically from the keyring by Telegram user ID.
argument-hint: "[connect|exec|list|close|shell] [args]"
user-invocable: true
tools: Bash
---

# remote-admin

Interact with the Remote Admin SSH bridge service at `http://localhost:8430`.

---

## Step 0 — Resolve credentials

Do this before any operation:

```bash
# Service auth token
TOKEN=$(python3 tools/stateless/secrets/secrets.py get remote_admin_token 2>/dev/null || echo "$REMOTE_ADMIN_TOKEN")

# Per-user SSH key — keyed by Telegram user ID
TID="${TELEGRAM_USER_ID:-default}"
PKEY=$(python3 tools/stateless/secrets/secrets.py get "remote_admin_ssh_key_${TID}" 2>/dev/null)
```

If `PKEY` is empty: this user has no enrolled SSH key yet. Direct them to run
`/setup-remote` on any target host first — enrollment happens automatically during setup.

---

## Connect to a remote host

**Standard (key auth — resolved from keyring):**
```bash
SID=$(curl -s -X POST http://localhost:8430/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"host\":\"<host>\",\"port\":22,\"username\":\"<user>\",\"private_key\":\"$PKEY\"}" \
  | jq -r '.session_id')
echo "Session: $SID"
```

**Bootstrap only (password — first connection to a new host before key enrollment):**
```bash
# Retrieve one-time bootstrap password from keyring — never hardcode or display
BPASS=$(python3 tools/stateless/secrets/secrets.py get "remote_admin_bootstrap_${TID}" 2>/dev/null)
SID=$(curl -s -X POST http://localhost:8430/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"host\":\"<host>\",\"port\":22,\"username\":\"<user>\",\"password\":\"$BPASS\"}" \
  | jq -r '.session_id')
```

---

## List sessions

```bash
curl -s http://localhost:8430/sessions \
  -H "Authorization: Bearer $TOKEN" | jq .
```

## Session detail

```bash
curl -s http://localhost:8430/sessions/<session_id> \
  -H "Authorization: Bearer $TOKEN" | jq .
```

## Run a command

```bash
curl -s -X POST http://localhost:8430/sessions/<session_id>/exec \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command":"uname -a","timeout":30}' | jq .
# Returns: {"stdout":"...","stderr":"...","exit_code":0}
```

## Close a session

```bash
curl -s -X DELETE http://localhost:8430/sessions/<session_id> \
  -H "Authorization: Bearer $TOKEN"
```

## Interactive shell (WebSocket)

```bash
websocat "ws://localhost:8430/sessions/<session_id>/stream?token=$TOKEN"
```

---

## Common workflows

### Full connect-exec-close
```bash
TOKEN=$(python3 tools/stateless/secrets/secrets.py get remote_admin_token)
TID="${TELEGRAM_USER_ID:-default}"
PKEY=$(python3 tools/stateless/secrets/secrets.py get "remote_admin_ssh_key_${TID}")

SID=$(curl -s -X POST http://localhost:8430/sessions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"host\":\"192.168.1.x\",\"username\":\"pi\",\"private_key\":\"$PKEY\"}" \
  | jq -r '.session_id')

run() { curl -s -X POST http://localhost:8430/sessions/$SID/exec \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"command\":\"$1\",\"timeout\":${2:-30}}" | jq -r '.stdout,.stderr'; }

run "uptime"
run "df -h /"

curl -s -X DELETE http://localhost:8430/sessions/$SID -H "Authorization: Bearer $TOKEN"
```

---

## Service management

```bash
# Via MCP (preferred from inside Ada):
# compose_up(project="hive_mind", service="remote-admin")

# Direct docker (from host):
docker compose up -d remote-admin
docker compose logs remote-admin
```

`REMOTE_ADMIN_TOKEN` is set in `.env`. Store it in keyring too:
```bash
python3 tools/stateless/secrets/secrets.py set remote_admin_token <token>
```
