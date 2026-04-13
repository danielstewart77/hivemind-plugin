---
name: setup-remote
description: Install Hive Mind on a remote host via SSH. Uses the remote-admin bridge service. Handles SSH key enrollment automatically — first connection uses a one-time bootstrap password, subsequent connections use a keyring-stored key.
argument-hint: "[host] [--standalone | --federated]"
user-invocable: true
tools: Bash
---

# setup-remote

Install Hive Mind on a remote host. Drives the remote-admin SSH bridge.
SSH credentials are per-user, keyed by Telegram user ID. Key enrollment is
handled automatically on first use.

---

## Step 1 — Gather target info

Ask the user (or parse from `$ARGUMENTS`):
- `TARGET_HOST` — IP or hostname
- `TARGET_PORT` — SSH port (default 22)
- `TARGET_USER` — username on the remote host
- `TOPOLOGY` — `standalone` (default) or `federated`

Do NOT ask for a password or key — these are resolved in Step 2.

---

## Step 2 — Get service token

```bash
TOKEN=$(python3 tools/stateless/secrets/secrets.py get remote_admin_token 2>/dev/null || echo "$REMOTE_ADMIN_TOKEN")
```

If empty: "Set REMOTE_ADMIN_TOKEN in your .env and restart the remote-admin container, then re-run this skill."

---

## Step 3 — Resolve or enroll SSH key

```bash
TID="${TELEGRAM_USER_ID:-default}"
PKEY=$(python3 tools/stateless/secrets/secrets.py get "remote_admin_ssh_key_${TID}" 2>/dev/null)
```

**If `PKEY` is set:** skip to Step 4 — key already enrolled, use it.

**If `PKEY` is empty:** run enrollment flow:

### Enrollment flow (first-time setup for this user)

```
"No SSH key found for your user. I'll set one up now.
Please provide a one-time bootstrap password for $TARGET_USER@$TARGET_HOST.
This password will be used only once to install your key and will not be stored after enrollment."
```

Store the bootstrap password temporarily:
```bash
# Prompt user for password, then:
python3 tools/stateless/secrets/secrets.py set "remote_admin_bootstrap_${TID}" "$BOOTSTRAP_PASS"
BPASS=$(python3 tools/stateless/secrets/secrets.py get "remote_admin_bootstrap_${TID}")
```

Open bootstrap session with password:
```bash
BOOT_SID=$(curl -s -X POST http://localhost:8430/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"host\":\"$TARGET_HOST\",\"port\":$TARGET_PORT,\"username\":\"$TARGET_USER\",\"password\":\"$BPASS\"}" \
  | jq -r '.session_id')
```

Generate ed25519 key pair locally:
```bash
ssh-keygen -t ed25519 -f /tmp/hive_admin_${TID} -N "" -q
PUBKEY=$(cat /tmp/hive_admin_${TID}.pub)
PRIVKEY=$(cat /tmp/hive_admin_${TID})
```

Deploy public key to remote host:
```bash
curl -s -X POST http://localhost:8430/sessions/$BOOT_SID/exec \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"command\":\"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$PUBKEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\"}"
```

Store private key in keyring, clean up temp files and bootstrap session:
```bash
python3 tools/stateless/secrets/secrets.py set "remote_admin_ssh_key_${TID}" "$PRIVKEY"
python3 tools/stateless/secrets/secrets.py delete "remote_admin_bootstrap_${TID}"
rm -f /tmp/hive_admin_${TID} /tmp/hive_admin_${TID}.pub
curl -s -X DELETE http://localhost:8430/sessions/$BOOT_SID -H "Authorization: Bearer $TOKEN"
PKEY=$(python3 tools/stateless/secrets/secrets.py get "remote_admin_ssh_key_${TID}")
echo "SSH key enrolled. Bootstrap password removed."
```

---

## Step 4 — Open SSH session (key auth)

```bash
SID=$(curl -s -X POST http://localhost:8430/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"host\":\"$TARGET_HOST\",\"port\":$TARGET_PORT,\"username\":\"$TARGET_USER\",\"private_key\":\"$PKEY\"}" \
  | jq -r '.session_id')
echo "Session: $SID"
```

Define exec helper:
```bash
run() {
  curl -s -X POST http://localhost:8430/sessions/$SID/exec \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"command\":\"$1\",\"timeout\":${2:-30}}"
}
```

---

## Step 5 — Prerequisites check

```bash
run "uname -a"
run "docker --version"
run "docker compose version"
run "git --version"
run "free -h"
run "df -h /"
```

If Docker is missing, offer to install it:
```bash
run "curl -fsSL https://get.docker.com | sh" 120
run "sudo usermod -aG docker $TARGET_USER"
```

---

## Step 6 — Clone the repo

```bash
run "git clone https://github.com/danielstewart77/hive_mind.git ~/hive_mind || (cd ~/hive_mind && git pull)" 60
```

---

## Step 7 — Configure

```bash
run "cd ~/hive_mind && cp .env.example .env" 10
```

Ask for required config values (Anthropic API key, Neo4j password, etc.) and write to remote `.env`:
```bash
run "cd ~/hive_mind && sed -i 's/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$ANTHROPIC_KEY/' .env"
```

For standalone topology:
```bash
run "cd ~/hive_mind && echo 'COMPOSE_PROFILES=standalone' >> .env"
```

---

## Step 8 — Start services

```bash
run "cd ~/hive_mind && docker compose pull" 120
run "cd ~/hive_mind && docker compose up -d" 60
```

Verify:
```bash
run "curl -sf http://localhost:8420/sessions > /dev/null && echo UP || echo DOWN"
```

---

## Step 9 — Register mind (federated only)

```bash
REMOTE_MIND_URL="http://$TARGET_HOST:8420"
curl -s -X POST http://localhost:8420/broker/minds \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$MIND_NAME\",\"url\":\"$REMOTE_MIND_URL\"}"
```

---

## Step 10 — Install Claude Code auth

```bash
echo "Connect interactively to complete Claude auth:"
echo "websocat 'ws://localhost:8430/sessions/$SID/stream?token=$TOKEN'"
echo "Then run: claude auth login"
```

---

## Step 11 — Clean up and report

```bash
curl -s -X DELETE http://localhost:8430/sessions/$SID -H "Authorization: Bearer $TOKEN"
```

```
Remote Setup Complete
====================
Host:       $TARGET_HOST
Topology:   $TOPOLOGY
Gateway:    $STATUS
Mind:       $MIND_NAME ($REGISTRATION_STATUS)
SSH key:    enrolled for user $TID

Next steps:
- SSH in and run: claude auth login  (if not done interactively)
- Run /setup-personality <mind_id> to seed identity
- Run /list-minds to verify registration
```
