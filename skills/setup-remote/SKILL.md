---
name: setup-remote
description: Install Hive Mind on a remote host via SSH. Uses the remote-admin bridge service to run the full setup sequence interactively on the target machine.
argument-hint: "[host] [--standalone | --federated]"
user-invocable: true
tools: Bash
---

# setup-remote

Install Hive Mind on a remote host. This skill drives the remote-admin SSH bridge
to run setup commands on the target interactively. The remote machine must be
reachable via SSH.

---

## Step 1 — Gather target info

Ask the user (or parse from `$ARGUMENTS`):
- `TARGET_HOST` — IP or hostname
- `TARGET_PORT` — SSH port (default 22)
- `TARGET_USER` — SSH username
- Auth method: password or private key path
- Topology: `standalone` (default for remote) or `federated`

---

## Step 2 — Get admin token

```bash
TOKEN=$(python3 tools/stateless/secrets/secrets.py get remote_admin_token 2>/dev/null || echo "$REMOTE_ADMIN_TOKEN")
```

If empty, prompt: "Set REMOTE_ADMIN_TOKEN in your .env and restart the remote-admin container."

---

## Step 3 — Open SSH session

```bash
SID=$(curl -s -X POST http://localhost:8430/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"host\": \"$TARGET_HOST\",
    \"port\": $TARGET_PORT,
    \"username\": \"$TARGET_USER\",
    \"password\": \"$TARGET_PASS\"
  }" | jq -r '.session_id')
echo "Session: $SID"
```

Define a helper for the rest of this skill:
```bash
run() {
  curl -s -X POST http://localhost:8430/sessions/$SID/exec \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"command\":\"$1\",\"timeout\":${2:-30}}"
}
```

---

## Step 4 — Prerequisites check

```bash
run "uname -a"
run "docker --version"
run "docker compose version"
run "git --version"
run "free -h"
run "df -h /"
```

Report results. If Docker is missing, offer to install it:

```bash
run "curl -fsSL https://get.docker.com | sh" 120
run "sudo usermod -aG docker $TARGET_USER"
```

---

## Step 5 — Clone the repo

```bash
run "git clone https://github.com/danielstewart77/hive_mind.git ~/hive_mind || (cd ~/hive_mind && git pull)" 60
```

---

## Step 6 — Configure

```bash
run "cd ~/hive_mind && cp .env.example .env" 10
```

Ask the user for required config values (Anthropic API key, Neo4j password, etc.)
and write them to the remote `.env`:

```bash
run "cd ~/hive_mind && sed -i 's/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$ANTHROPIC_KEY/' .env"
```

For standalone topology, set the compose profile:
```bash
run "cd ~/hive_mind && echo 'COMPOSE_PROFILES=standalone' >> .env"
```

---

## Step 7 — Start services

```bash
run "cd ~/hive_mind && docker compose pull" 120
run "cd ~/hive_mind && docker compose up -d" 60
```

Wait ~15 seconds, then verify:
```bash
run "curl -sf http://localhost:8420/sessions > /dev/null && echo UP || echo DOWN"
```

---

## Step 8 — Register mind (federated only)

If `TOPOLOGY=federated`, register the remote mind with the local broker:

```bash
REMOTE_MIND_URL="http://$TARGET_HOST:8420"
curl -s -X POST http://localhost:8420/broker/minds \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$MIND_NAME\",\"url\":\"$REMOTE_MIND_URL\"}"
```

---

## Step 9 — Install Claude Code auth

Guide the user through authenticating Claude Code on the remote host:

```bash
# Interactive — use the WebSocket stream for this step
echo "Connect interactively:"
echo "websocat 'ws://localhost:8430/sessions/$SID/stream?token=$TOKEN'"
echo "Then run: claude auth login"
```

---

## Step 10 — Clean up and report

```bash
curl -s -X DELETE http://localhost:8430/sessions/$SID \
  -H "Authorization: Bearer $TOKEN"
```

Report:

```
Remote Setup Complete
====================
Host:       $TARGET_HOST
Topology:   $TOPOLOGY
Gateway:    $STATUS
Mind:       $MIND_NAME ($REGISTRATION_STATUS)

Next steps:
- SSH in and run: claude auth login  (if not done)
- Run /setup-personality <mind_id> to seed identity
- Run /list-minds to verify registration
```
