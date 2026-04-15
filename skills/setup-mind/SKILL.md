---
name: setup-mind
description: Set up minds for the Hive Mind system. Create new minds, import existing ones, or register minds from other instances. Configures per-mind volumes and authentication.
user-invocable: true
tools: Bash, Read
---

# setup-mind

Set up minds for the system. At least one mind is needed.

## Step 0 — Install type (fallback — skip if already set by /setup)

If `INSTALL_TYPE` was already set during `/setup` Step 0 (Question 2), skip this step entirely.

If running `/setup-mind` standalone (not via `/setup`), ask:

```
What kind of install is this?

(A) New instance — full Hive Mind, fully independent. During mind setup you
    can optionally register minds from other Hive Mind instances so they can
    message each other.

(B) Hub-spoke (managed mind) — single mind managed by an existing Hive Mind
    instance. No local gateway or broker.
```

Store as `INSTALL_TYPE` (values: `instance`, `spoke`).

Do NOT delegate to `/setup-remote` here. That skill installs Hive Mind on a
remote machine via SSH — it is not for configuring local minds.

## Step 1 — Prerequisite check

```bash
curl -sf http://localhost:8420/sessions > /dev/null || echo "Gateway not reachable. Run /setup-nervous-system first."
curl -sf http://localhost:8420/broker/minds | jq length
```

**If `spoke`:** skip — no local gateway or broker required. Verify Docker is running.

Verify at least one provider is configured (check config.yaml providers block).

## Step 2 — List current minds

Show only minds that are actually running as containers — do NOT surface mind folder names from the repo. The repo contains default templates; they are not "installed minds."

```bash
# Minds registered in the broker (actually deployed)
curl -sf http://localhost:8420/broker/minds 2>/dev/null | jq -r '.[].name' || echo "(none yet)"

# Running mind containers
docker ps --filter "label=hive-mind.role=mind" --format "{{.Names}}" 2>/dev/null || echo "(none running)"
```

**If `spoke`:** skip — no broker running yet.

## Step 3 — Add a mind

Present these options every time. Do not pre-populate or suggest mind names from the repo.

```
What would you like to do?

1. Create a new mind — run the mind creation wizard to build and deploy a new mind
   on this machine

2. Import an existing mind — you already have a complete minds/<name>/ folder
   (e.g. copied from another machine). Import it and register it here.

3. Register a mind from another Hive Mind instance — no local install. Adds a
   contact entry so minds on this machine can send messages to a mind running
   on a different Hive Mind instance. You'll need the mind's name and the other
   instance's gateway URL (e.g. http://192.168.4.64:8420).
```

There is no skip option. After each mind is set up, ask "Would you like to add another mind?" and loop back here until the user says no.

## Step 4 — Execute the chosen option

**Option 1 (create new mind):** delegate to `/create-mind`

**Option 2 (import existing mind folder):** delegate to `/add-mind`

**Option 3 (register from another instance):**
- Ask for: the mind's name, and the gateway URL of the other instance
- Register the contact in config.yaml under `remote_minds`:
  ```yaml
  remote_minds:
    - name: ada
      gateway: http://192.168.4.64:8420
  ```
- Confirm: "Registered. Minds on this instance can now address messages to `ada` at the remote gateway."
- Skip Steps 5, 5b, 6, 7 (no local container to configure)

## Step 5 — Per-mind volume config

Ask what host directories this mind should access:
- Default Docker named volume (most isolated)
- Host directory mounts: which paths, read-only or read-write?

## Step 5b — Personality setup

Ask: "Would you like to define `<mind_name>`'s personality and seed its identity now?"
- If yes → delegate to `/setup-personality <mind_id>`
- If no → "You can run `/setup-personality <mind_id>` anytime."

## Step 6 — Per-mind auth

If per-mind auth model was chosen in `/setup-auth`:

**API key:** inject `ANTHROPIC_API_KEY` into the container env and verify with a test call.

**OAuth:** OAuth for containerized minds requires an interactive terminal — the auth URL
cannot be extracted non-interactively. Tell the user clearly, give them the exact command,
and WAIT here for them to return. Do not skip. Do not move to the next step.

Say exactly this:

```
Sergeant needs OAuth login. This requires a brief terminal step.

Open a terminal on this machine and run:

    docker exec -it hive-mind-sergeant claude

A browser URL will appear. Open it, log in, and close the terminal.
Then come back here and tell me when it's done.
```

When the user confirms, verify auth worked:
```bash
docker exec hive-mind-<name> sh -c \
  'CLAUDE_CONFIG_DIR=/home/hivemind/.claude-config claude --output-format stream-json --verbose -p "say hi" 2>&1' \
  | python3 -c "import sys,json; [print(o.get('result','')) for l in sys.stdin for o in [json.loads(l)] if o.get('type')=='result']"
```

If it returns a response (not "Not logged in"), auth succeeded. Continue to Step 7.
If it still says "Not logged in", ask the user to retry the terminal step.

## Step 7 — Skill selection

Read `MIND-INSTALL-MANIFEST.md` to get the canonical skill groups and descriptions.

**Core groups (silent — install automatically, do not present):**
- Core — Identity
- Core — Utilities

**Present the remaining groups as selectable options:**

```
Skills for <mind_name>
======================
Core skills (memory, identity, utilities) are installed automatically.

Optional skill groups — select any that apply to this mind's role:

  1. Development    — coding, planning, review, story management
  2. Research       — web browsing, X/Twitter, crypto, weather
  3. Productivity   — Planka, reminders, inter-mind messaging
  4. Publishing     — email, LinkedIn, PDF, diagrams
  5. System / Ops   — sitrep, logs, updates, Discord sync
  6. Advanced       — skill/tool creation, memory auditing
  7. None — core only

Enter numbers separated by commas, or 'all', or 'none':
```

For each selected group, list the individual skills from `SKILLS.md` and confirm,
or offer "install whole group" as a default.

## Step 8 — Add another mind?

Ask: "Would you like to add another mind?"
- Yes → return to Step 3
- No → proceed to Step 9

## Step 9 — Spoke connection (spoke installs only)

**If `spoke`:** ask for the managing instance's gateway URL and configure
the mind to route through it.

**If `instance`:** nothing to do here. Remote mind contacts were handled
per-mind in Step 4 (option 3). You can add more anytime by re-running
`/setup-mind` and choosing option 3.

## Step 10 — Final mind roster

Present a table of all minds: name, type (local/remote), status, skills installed.
