---
name: setup
description: Master setup wizard for the Hive Mind system. Bootstraps a new deployment from zero or verifies an existing one. Runs sub-setup skills in dependency order.
argument-hint: "[component]"
user-invocable: true
tools: Bash, Read
---

# setup

Master setup wizard. Run `/setup all` for full onboarding or `/setup <component>` for a specific step.

## Step 0 — Where and what kind of install?

**These are the first two questions. Ask them before anything else.**

### Question 1 — Local or Remote?

```
Where do you want to install Hive Mind?

(A) This machine  — you are already on the target host
(B) Remote machine — install on another machine via SSH
```

**If (B) Remote:** collect the target machine's host, SSH port (default 22), and username.
Then open a remote-admin session:

```bash
TOKEN=$(python3 -m keyring get hive-mind remote_admin_token)
PKEY=$(python3 -m keyring get hive-mind remote_admin_ssh_key_default)
SID=$(curl -s -X POST http://hive-mind-remote-admin:8430/sessions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"host\":\"<host>\",\"port\":22,\"username\":\"<user>\",\"private_key\":\"$PKEY\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
```

All remaining questions and setup steps (including Question 2 below) apply to the remote
machine and are executed via `exec` calls on that session. Relay each question and answer
through the session exactly as you would locally.

### Question 2 — What kind of install?

```
What kind of install is this?

(A) New instance — full Hive Mind install. Gateway, broker, Neo4j, minds,
    communication surfaces — everything. Each Hive Mind instance is fully
    independent. During mind setup you can optionally register minds from
    other Hive Mind instances so they can message each other — but there is
    no system-level link between instances. Choose this for any new machine.

(B) Hub-spoke (managed mind) — a single mind on this machine, managed and
    routed by an existing Hive Mind instance. No local gateway or broker
    needed. The managing instance handles routing, memory, and orchestration.
```

Store as `INSTALL_TYPE` (values: `instance`, `spoke`).

- **instance**: run every step below in full.
- **spoke**: skip Nervous System and Neo4j; go straight to Config → Auth →
  Provider → Mind (single mind only), then configure the connection to the
  managing instance.

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
