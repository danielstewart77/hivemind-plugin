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

```bash
# Registered minds
curl -sf http://localhost:8420/broker/minds | jq -r ".[].name"

# Unregistered mind folders (have MIND.md but not in broker)
for d in minds/*/; do
  name=$(basename "$d")
  [[ "$name" == "__pycache__" ]] && continue
  if [ -f "$d/MIND.md" ]; then
    registered=$(curl -sf http://localhost:8420/broker/minds | jq -r ".[] | select(.name==\"$name\") | .name")
    [ -z "$registered" ] && echo "UNREGISTERED: $name (has MIND.md)"
  fi
done
```

**If `spoke`:** skip — no broker running yet.

## Step 3 — Add a mind

```
What would you like to do?

1. Install a new mind from template — creates and deploys a new mind on this machine
2. Install an existing local mind — registers a minds/ folder already on this machine
```

There is no skip option. After each mind is set up, ask "Would you like to add another mind?" and loop back here until the user says no.

## Step 4 — Execute the chosen option

**Option 1 (new mind from template):** delegate to `/create-mind`

**Option 2 (existing local mind):** delegate to `/add-mind`

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
```bash
docker exec -it <container-name> claude
```
Or for API key: configure the key in the mind container env. Verify auth works.

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

## Step 9 — Cross-instance mind contacts (optional)

For each mind just installed, ask:

> "Does this mind need to message minds on another Hive Mind instance?"

- If yes: ask for the name and gateway URL of each remote mind
  (e.g. `ada` at `http://192.168.4.64:8420`). Store in the mind's config
  so it can address messages to them.
- If no: skip. This can be configured anytime by re-running `/setup-mind`.

**If `spoke`:** ask for the managing instance's gateway URL and configure
the mind to route through it.

## Step 10 — Final mind roster

Present a table of all minds: name, type (local/remote), status, skills installed.
