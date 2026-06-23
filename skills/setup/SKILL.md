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

**If (B) Remote:** this installer runs on whatever host it's invoked from. To install
on another machine, open an SSH session to that machine yourself and run `/setup all`
there — there is no bridge or proxy, you are the operator on that box. Every step below
then executes locally on the target. Continue with Question 2 once you're on the target host.

### Question 2 — What kind of install?

```
What kind of install is this?

(A) New instance — full Hive Mind install. Nervous system (lucent + comms),
    minds, communication surfaces — everything. Each Hive Mind instance is fully
    independent. During mind setup you can optionally register minds from
    other Hive Mind instances so they can message each other — but there is
    no system-level link between instances. Choose this for any new machine.

(B) Hub-spoke (managed mind) — a single mind on this machine, managed and
    routed by an existing Hive Mind instance. No local gateway or broker
    needed. The managing instance handles routing, memory, and orchestration.
```

Store as `INSTALL_TYPE` (values: `instance`, `spoke`).

- **instance**: run every step below in full — the Nervous System step deploys
  lucent + comms locally (`/setup-nervous-system`, New path).
- **spoke**: do **not** deploy a local nervous system, but still run
  `/setup-nervous-system` in its **Existing** path — that is where the wizard
  prompts for the managing instance's comms and lucent URLs and bearer tokens,
  verifies it can reach them, and records them in `hive_mind/.env`. Then go
  Config → Auth → Provider → Mind (single mind only). The mind's `gateway_url`
  and `HIVE_MIND_SERVER_URL` are wired to those remote coordinates, not local.

---

## Step 1 — Parse arguments

`$ARGUMENTS[0]` = optional component name.
Valid: `prerequisites`, `config`, `auth`, `nervous-system`, `provider`, `body`, `mind`, `all`
Default (no argument): show the menu.

## Step 2 — Show menu with quick health scan

```bash
# lucent /health needs no auth; comms /health is bearer-gated.
# Resolve coordinates: local nervous-system repo (instance), else the remote
# coordinates a spoke recorded in hive_mind/.env. Defaults to localhost.
CT=$(grep -h COMMS_BEARER_TOKEN */.env ~/Storage/Dev/hive_nervous_system/.env 2>/dev/null | head -1 | cut -d= -f2)
COMMS_URL=$(grep -h ^COMMS_URL= */.env 2>/dev/null | head -1 | cut -d= -f2-); COMMS_URL=${COMMS_URL:-http://localhost:8426}
LUCENT_URL=$(grep -h ^LUCENT_URL= */.env 2>/dev/null | head -1 | cut -d= -f2-); LUCENT_URL=${LUCENT_URL:-http://localhost:8425}
luc=$(curl -sf "$LUCENT_URL/health" > /dev/null 2>&1 && echo "UP" || echo "DOWN")
comms=$(curl -sf -H "Authorization: Bearer $CT" "$COMMS_URL/health" > /dev/null 2>&1 && echo "UP" || echo "DOWN")
dk=$(docker info > /dev/null 2>&1 && echo "UP" || echo "DOWN")
minds=$(curl -sf -H "Authorization: Bearer $CT" "$COMMS_URL/broker/minds" 2>/dev/null | jq length 2>/dev/null || echo 0)
```

```
Hive Mind Setup
===============

Quick scan: lucent [$luc]  comms [$comms]  Docker [$dk]  Minds [$minds]

1. Prerequisites     — hardware, OS, Docker, Git          [not checked]
2. Configuration     — config.yaml, .env, compose profile [not generated]
3. Authentication    — Claude Code auth tokens            [not configured]
4. Nervous System    — lucent + comms                     [$luc/$comms]
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
