---
name: setup
description: Master setup wizard for the Hive Mind system. Bootstraps a new deployment from zero or verifies an existing one. Runs sub-setup skills in dependency order.
argument-hint: "[component]"
user-invocable: true
tools: Bash, Read
---

# setup

Master setup wizard. Run `/setup all` for full onboarding or `/setup <component>` for a specific step.

## Step 0 — Local or Remote?

**This is the first question. Ask it before anything else.**

```
Where do you want to install Hive Mind?

(A) This machine  — install locally (you are already on the target host)
(B) Remote machine — install on another machine via SSH
```

**If (B) Remote:**
Ask:
- IP or hostname of the target machine
- SSH port (default: 22)
- Username on that machine

Connect via remote-admin:
```bash
TOKEN=$(python3 -m keyring get hive-mind remote_admin_token)
SID=$(curl -s -X POST http://hive-mind-remote-admin:8430/sessions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"host\":\"<host>\",\"port\":22,\"username\":\"<user>\",\"private_key\":\"$(python3 -m keyring get hive-mind remote_admin_ssh_key_default)\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
```

Then run setup on the remote machine via the session:
```bash
curl -s -X POST http://hive-mind-remote-admin:8430/sessions/$SID/exec \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"command": "CLAUDE_CONFIG_DIR=~/.claude-config claude --dangerously-skip-permissions -p \"/setup all\"", "timeout": 3600}' | ...
```

All subsequent setup steps run on the remote machine. This skill exits after confirming the remote session is running.

**If (A) Local — continue below.**

---

## Step 0b — Topology (local installs only)

```
Is this the first Hive Mind instance, or does a Hub already exist?

(A) Hub (first install, recommended) — This machine IS the Hub. Runs the full
    stack: gateway, broker, Neo4j, all infrastructure. Every other instance
    connects here.

(B) Spoke — Connect this machine to an existing Hub. Minds here route through
    the Hub's gateway and broker. Requires a running Hub — without one, this
    gives you no working system.

(C) Remote Hub — A second independent Hive Mind instance on this machine,
    linked to an existing Hub via the broker API. Both run full stacks but
    share messaging.
```

Store the answer as `TOPOLOGY` (values: `hub`, `spoke`, `remote-hub`). This is used by later steps.

- **Hub**: proceed with full setup — all steps below apply.
- **Spoke**: skip Nervous System (no local gateway/broker needed), skip Neo4j. Go straight to Providers → Body → Mind, then configure the broker link to the Hub at the end.
- **Remote Hub**: run full setup (same as Hub), then configure broker federation with the existing Hub at the end of Step 3.

---

## Step 1 — Parse arguments

`$ARGUMENTS[0]` = optional component name.
Valid: `prerequisites`, `config`, `auth`, `nervous-system`, `provider`, `body`, `mind`, `all`
Default (no argument): show the menu.

## Step 2 — Show menu with quick health scan

```bash
gw=$(curl -sf http://localhost:8420/sessions > /dev/null 2>&1 && echo "UP" || echo "DOWN")
neo=$(curl -sf http://localhost:7474 > /dev/null 2>&1 && echo "UP" || echo "DOWN")
dk=$(docker info > /dev/null 2>&1 && echo "UP" || echo "DOWN")
minds=$(curl -sf http://localhost:8420/broker/minds 2>/dev/null | jq length 2>/dev/null || echo 0)
```

```
Hive Mind Setup
===============

Quick scan: Gateway [$gw]  Neo4j [$neo]  Docker [$dk]  Minds [$minds]

1. Prerequisites     — hardware, OS, Docker, Git         [not checked]
2. Configuration     — config.yaml, .env, compose profile [not generated]
3. Authentication    — Claude Code auth tokens            [not configured]
4. Nervous System    — gateway, broker, Neo4j, MCP        [$gw]
5. Providers         — Anthropic, OpenAI, Ollama          [check config]
6. Body              — surfaces, integrations, services   [check containers]
7. Minds             — AI minds                           [$minds registered]

Run all:  /setup all
Run one:  /setup <component>
```

## Step 3 — Run selected components in dependency order

If `all`, run in this order (each completes before the next):
1. `/setup-prerequisites`
2. `/setup-config`
3. `/setup-auth`
4. `/setup-nervous-system`
5. `/setup-provider`
6. `/setup-body`
7. `/setup-resolve-placeholders`
8. `/setup-mind`

If a specific component, run just that sub-skill.

## Step 4 — Final report

After all requested components complete:

```
Setup Complete
==============

| Component       | Result       |
|-----------------|--------------|
| Prerequisites   | OK / ISSUES  |
| Configuration   | OK / ISSUES  |
| Authentication  | OK / ISSUES  |
| Nervous System  | OK / ISSUES  |
| Providers       | OK / ISSUES  |
| Body            | OK / ISSUES  |
| Minds           | OK / ISSUES  |

Next steps: <any outstanding issues or recommendations>

Skills installed:
  Core (auto): Identity pipeline, utilities — installed on all minds
  Optional:    <list groups selected during setup-mind, or "none selected">

Run `/setup-mind` to add or change skills for any mind.
See `MIND-INSTALL-MANIFEST.md` for the full skill catalog.
```
