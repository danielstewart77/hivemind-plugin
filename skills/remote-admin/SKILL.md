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
BASE="http://hive-mind-remote-admin:8430"

# Service auth token
TOKEN=$(python3 -m keyring get hive-mind remote_admin_token 2>/dev/null || echo "$REMOTE_ADMIN_TOKEN")

# Per-user SSH key — keyed by Telegram user ID
TID="${TELEGRAM_USER_ID:-default}"
PKEY=$(python3 -m keyring get hive-mind "remote_admin_ssh_key_${TID}" 2>/dev/null)
```

If `PKEY` is empty: this user has no enrolled SSH key yet. Direct them to run
`/setup-remote` on any target host first — enrollment happens automatically during setup.

### Sudo helper

After opening a session, define `sudorun` for privileged commands. The sudo
strategy is stored per-host in the keyring as `remote_admin_sudo_<host_underscored>`.

```bash
# Retrieve sudo password for this host (empty = no password configured)
SUDO_KEY="remote_admin_sudo_$(echo $TARGET_HOST | tr '.' '_')"
SUDO_PASS=$(python3 -c "
import keyring, os, sys
os.environ['PYTHON_KEYRING_BACKEND'] = 'keyrings.alt.file.PlaintextKeyring'
v = keyring.get_password('hive-mind', sys.argv[1].upper())
print(v or '')
" "$SUDO_KEY" 2>/dev/null)

sudorun() {
  if [ -n "$SUDO_PASS" ]; then
    run "echo '$SUDO_PASS' | sudo -S $1" ${2:-30}
  else
    run "sudo $1" ${2:-30}
  fi
}
```

If `SUDO_PASS` is empty and the command needs sudo, either:
- The host has passwordless sudo (works fine)
- Or direct the user to run `/setup-remote` again to configure sudo strategy

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
BPASS=$(python3 -m keyring get hive-mind "remote_admin_bootstrap_${TID}" 2>/dev/null)
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

# For commands containing quotes or special characters, build the payload safely:
# PAYLOAD=$(python3 -c "import json,sys; print(json.dumps({'command': sys.argv[1], 'timeout': 30}))" "echo 'hello'")
# curl -s -X POST http://localhost:8430/sessions/<session_id>/exec \
#   -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
#   -d "$PAYLOAD" | jq .
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
TOKEN=$(python3 -m keyring get hive-mind remote_admin_token 2>/dev/null || echo "$REMOTE_ADMIN_TOKEN")
TID="${TELEGRAM_USER_ID:-default}"
PKEY=$(python3 -m keyring get hive-mind "remote_admin_ssh_key_${TID}" 2>/dev/null)

SID=$(curl -s -X POST http://localhost:8430/sessions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"host\":\"192.168.1.x\",\"username\":\"pi\",\"private_key\":\"$PKEY\"}" \
  | jq -r '.session_id')

run() {
  python3 -c "
import sys, json, urllib.request
payload = json.dumps({'command': sys.argv[1], 'timeout': int(sys.argv[2]) if len(sys.argv) > 2 else 30}).encode()
req = urllib.request.Request(
    'http://localhost:8430/sessions/$SID/exec',
    data=payload,
    headers={'Authorization': 'Bearer $TOKEN', 'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req) as r:
    import json as j; d = j.loads(r.read()); print(d.get('stdout',''), d.get('stderr',''), sep='')
" "$1" "${2:-30}"
}

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
python3 -m keyring set hive-mind remote_admin_token <token>
```
