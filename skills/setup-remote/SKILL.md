---
name: setup-remote
description: Install Hive Mind on a remote host via SSH. Uses the remote-admin bridge service. Walks through an onboarding questionnaire covering machine purpose, SSH key enrollment, and sudo strategy before installing.
argument-hint: "[host] [--standalone | --federated]"
user-invocable: true
tools: Bash
---

# setup-remote

Install Hive Mind on a remote host. Drives the remote-admin SSH bridge.
SSH credentials are per-user, keyed by Telegram user ID. Sudo strategy is
determined by machine purpose and user preference.

---

## Step 1 — Onboarding questionnaire

Ask the user for the following. Parse from `$ARGUMENTS` where possible, ask for the rest.

### 1a — Target machine
- `TARGET_HOST` — IP or hostname
- `TARGET_PORT` — SSH port (default 22)
- `TARGET_USER` — username on the remote host
- `TOPOLOGY` — `standalone` (default) or `federated`

### 1b — Machine purpose
Ask: "What is this machine? (e.g. public-facing server, home lab, cloud VM, Raspberry Pi, etc.)"

Based on the answer, classify as:
- **HIGH_RISK** — public-facing (VPN gateway, web server, exposed SSH, cloud VM with public IP)
- **MEDIUM_RISK** — LAN-accessible but not directly internet-exposed
- **LOW_RISK** — local-only, air-gapped, or heavily firewalled

Give a brief security note based on classification:
- HIGH_RISK: "This machine is internet-exposed. I recommend using a sudo password rather than passwordless sudo."
- MEDIUM_RISK: "Passwordless sudo is moderate risk here. I'd still recommend a password for sudo."
- LOW_RISK: "Passwordless sudo is low risk on a local-only machine."

### 1c — SSH key situation
Ask: "Do you already have an SSH key set up on this machine, or do I need to enroll one?"
- `KEY_STATUS` = `existing` | `enroll`

### 1d — Sudo strategy
Ask: "How should I handle sudo on this machine?"
Present options based on risk classification:
- **(a) Passwordless sudo** — recommended only for LOW_RISK
- **(b) Sudo with stored password** — I'll store it securely in the keyring, inject it per command. Recommended for HIGH_RISK and MEDIUM_RISK.
- **(c) Already passwordless** — skip setup, just use sudo directly
- **(d) Skip sudo** — I'll install Docker and other tools only if you already have them

Set `SUDO_STRATEGY` = `passwordless` | `stored_password` | `already_passwordless` | `skip`

If `stored_password`: ask for the sudo password now and store it:
```bash
# Store in keyring — never echoed or logged
SUDO_KEY="remote_admin_sudo_$(echo $TARGET_HOST | tr '.' '_')"
# Use secrets tool or keyring directly to store SUDO_PASS
```

---

## Step 2 — Get service token

```bash
TOKEN=$(python3 -m keyring get hive-mind REMOTE_ADMIN_TOKEN 2>/dev/null || echo "$REMOTE_ADMIN_TOKEN")
```

If empty: "Set REMOTE_ADMIN_TOKEN in your .env and restart the remote-admin container, then re-run this skill."

---

## Step 3 — Resolve or enroll SSH key

```bash
TID="${TELEGRAM_USER_ID:-default}"
PKEY=$(python3 -m keyring get hive-mind "remote_admin_ssh_key_${TID}" 2>/dev/null)
```

**If `PKEY` is set OR `KEY_STATUS=existing`:** skip to Step 4.

**If `PKEY` is empty AND `KEY_STATUS=enroll`:** run enrollment flow:

Ask for a one-time bootstrap password for `$TARGET_USER@$TARGET_HOST`. Store temporarily:
```bash
echo "$BOOTSTRAP_PASS" | python3 -m keyring set hive-mind "remote_admin_bootstrap_${TID}"
BPASS=$(python3 -m keyring get hive-mind "remote_admin_bootstrap_${TID}" 2>/dev/null)
```

Open bootstrap session with password:
```bash
BOOT_SID=$(curl -s -X POST $BASE/sessions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"host\":\"$TARGET_HOST\",\"port\":$TARGET_PORT,\"username\":\"$TARGET_USER\",\"password\":\"$BPASS\"}" \
  | jq -r '.session_id')
```

Generate ed25519 key pair and deploy:
```bash
ssh-keygen -t ed25519 -f /tmp/hive_admin_${TID} -N "" -q
PUBKEY=$(cat /tmp/hive_admin_${TID}.pub)
PRIVKEY=$(cat /tmp/hive_admin_${TID})

curl -s -X POST $BASE/sessions/$BOOT_SID/exec \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"command\":\"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$PUBKEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\"}"

# Store private key, clean up
echo "$PRIVKEY" | python3 -m keyring set hive-mind "remote_admin_ssh_key_${TID}"
python3 -m keyring del hive-mind "remote_admin_bootstrap_${TID}"
rm -f /tmp/hive_admin_${TID} /tmp/hive_admin_${TID}.pub
curl -s -X DELETE $BASE/sessions/$BOOT_SID -H "Authorization: Bearer $TOKEN"
PKEY=$(python3 -m keyring get hive-mind "remote_admin_ssh_key_${TID}" 2>/dev/null)
echo "SSH key enrolled."
```

---

## Step 4 — Open SSH session

```bash
BASE="http://hive-mind-remote-admin:8430"

SID=$(curl -s -X POST $BASE/sessions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"host\":\"$TARGET_HOST\",\"port\":$TARGET_PORT,\"username\":\"$TARGET_USER\",\"private_key\":\"$PKEY\"}" \
  | jq -r '.session_id')
echo "Session: $SID"
```

Define exec helpers:
```bash
# Unprivileged command
run() {
  curl -s -X POST $BASE/sessions/$SID/exec \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d "{\"command\":\"$1\",\"timeout\":${2:-30}}" | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(d.get('stdout','').strip())
e=d.get('stderr','').strip()
if e: print('[stderr]', e)
"
}

# Privileged command — strategy determined in Step 1d
sudorun() {
  if [ "$SUDO_STRATEGY" = "stored_password" ] && [ -n "$SUDO_PASS" ]; then
    run "echo '$SUDO_PASS' | sudo -S $1" ${2:-30}
  elif [ "$SUDO_STRATEGY" = "already_passwordless" ] || [ "$SUDO_STRATEGY" = "passwordless" ]; then
    run "sudo $1" ${2:-30}
  else
    echo "SKIP (no sudo configured): $1"
  fi
}
```

If `SUDO_STRATEGY=stored_password`, retrieve the password:
```bash
SUDO_KEY="remote_admin_sudo_$(echo $TARGET_HOST | tr '.' '_')"
SUDO_PASS=$(# retrieve from keyring using venv python)
```

---

## Step 5 — Configure passwordless sudo (if chosen)

Only if `SUDO_STRATEGY=passwordless`:
```bash
sudorun "bash -c \"echo '$TARGET_USER ALL=(ALL) NOPASSWD:ALL | tee /etc/sudoers.d/hivemind-admin\""
```

---

## Step 6 — Prerequisites check

```bash
run "uname -a"
run "docker --version" && run "docker compose version"
run "git --version"
run "free -h"
run "df -h /"
```

If Docker is missing, install it:
```bash
sudorun "sh -c 'curl -fsSL https://get.docker.com | sh'" 120
sudorun "usermod -aG docker $TARGET_USER"
```

---

## Step 7 — Clone the repo

```bash
run "git clone https://github.com/danielstewart77/hive_mind.git ~/hive_mind || (cd ~/hive_mind && git pull)" 60
```

---

## Step 8 — Configure

```bash
run "cd ~/hive_mind && cp .env.example .env"
```

Ask for required config values (Anthropic API key, Neo4j password, etc.) and write to remote `.env`:
```bash
run "cd ~/hive_mind && sed -i 's/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$ANTHROPIC_KEY/' .env"
run "cd ~/hive_mind && echo 'COMPOSE_PROFILES=standalone' >> .env"  # if standalone
```

---

## Step 9 — Start services

```bash
sudorun "bash -c 'cd ~/hive_mind && docker compose pull'" 120
sudorun "bash -c 'cd ~/hive_mind && docker compose up -d'" 60
```

Verify:
```bash
run "curl -sf http://localhost:8420/sessions > /dev/null && echo UP || echo DOWN"
```

---

## Step 10 — Register mind (federated only)

```bash
REMOTE_MIND_URL="http://$TARGET_HOST:8420"
curl -s -X POST http://localhost:8420/broker/minds \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$MIND_NAME\",\"url\":\"$REMOTE_MIND_URL\"}"
```

---

## Step 11 — Claude Code auth

```bash
echo "Connect interactively to complete Claude auth:"
echo "websocat 'ws://localhost:8430/sessions/$SID/stream?token=$TOKEN'"
echo "Then run: claude auth login"
```

---

## Step 12 — Clean up and report

```bash
curl -s -X DELETE $BASE/sessions/$SID -H "Authorization: Bearer $TOKEN"
```

```
Remote Setup Complete
====================
Host:        $TARGET_HOST
Topology:    $TOPOLOGY
Sudo:        $SUDO_STRATEGY
SSH key:     enrolled for user $TID
Gateway:     $STATUS

Next steps:
- SSH in and run: claude auth login  (if not done interactively)
- Run /setup-personality <mind_id> to seed identity
- Run /list-minds to verify registration
```
