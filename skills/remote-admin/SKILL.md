---
name: remote-admin
description: Manage SSH sessions on remote hosts via the remote-admin bridge service. Create sessions, run commands, stream interactive shells. Base URL http://localhost:8430.
argument-hint: "[connect|exec|list|close|shell] [args]"
user-invocable: true
tools: Bash
---

# remote-admin

Interact with the Remote Admin SSH bridge service at `http://localhost:8430`.
All requests require `Authorization: Bearer $REMOTE_ADMIN_TOKEN`.

Get the token:
```bash
TOKEN=$(python3 tools/stateless/secrets/secrets.py get remote_admin_token 2>/dev/null || echo "$REMOTE_ADMIN_TOKEN")
```

---

## Connect to a remote host

```bash
curl -s -X POST http://localhost:8430/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"host":"<host>","port":22,"username":"<user>","password":"<pass>"}'
# Returns: {"session_id":"abc12345", ...}
```

With a private key (PEM text, newlines as \n):
```bash
PKEY=$(cat ~/.ssh/id_rsa | awk '{printf "%s\\n", $0}')
curl -s -X POST http://localhost:8430/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"host\":\"<host>\",\"username\":\"<user>\",\"private_key\":\"$PKEY\"}"
```

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

Use `websocat` or any WebSocket client:
```bash
websocat "ws://localhost:8430/sessions/<session_id>/stream?token=$TOKEN"
```

---

## Common workflows

### Run a series of commands
```bash
SID=<session_id>
run() { curl -s -X POST http://localhost:8430/sessions/$SID/exec \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"command\":\"$1\"}" | jq -r '.stdout,.stderr'; }

run "docker --version"
run "git --version"
run "free -h"
```

### Full connect-exec-close pattern
```bash
TOKEN=$(python3 tools/stateless/secrets/secrets.py get remote_admin_token)
SID=$(curl -s -X POST http://localhost:8430/sessions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"host":"192.168.1.x","username":"pi","password":"raspberry"}' | jq -r '.session_id')

curl -s -X POST http://localhost:8430/sessions/$SID/exec \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"command":"uptime"}' | jq -r .stdout

curl -s -X DELETE http://localhost:8430/sessions/$SID \
  -H "Authorization: Bearer $TOKEN"
```

---

## Service management

The remote-admin service runs as a Docker container (`hive-mind-remote-admin`) on port 8430.

Start/stop:
```bash
docker compose up -d remote-admin
docker compose stop remote-admin
docker compose logs remote-admin
```

Token is set via `REMOTE_ADMIN_TOKEN` in your `.env` file.
