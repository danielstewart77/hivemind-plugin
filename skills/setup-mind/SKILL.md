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
What kind of Hive Mind install is this?

(A) First instance — full install, this machine is the primary Hub
(B) Federated second instance — own full stack, can also register minds from
    other instances for cross-instance messaging
(C) Hub-spoke (managed) — single mind managed by an existing Hive Mind instance
```

Store as `INSTALL_TYPE` (values: `first`, `federated`, `spoke`).

Do NOT delegate to `/setup-remote` here. That skill installs Hive Mind on a
remote machine via SSH — it is not for configuring federation on this machine.

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

Present the options that apply to this install type:

**For `first` and `federated`:**
```
What would you like to do?

1. Install a new mind from template — creates and deploys a new mind on this machine
2. Install an existing local mind — registers a minds/ folder already on this machine
3. Register a mind from another instance — no local install needed; just registers
   the remote mind's broker endpoint so both instances can message each other.
   You'll need: the mind's name, its host URL, and its broker endpoint.
```

**For `spoke`:**
```
What would you like to do?

1. Install a new mind from template — creates and deploys a new mind on this machine
2. Install an existing local mind — registers a minds/ folder already on this machine
```

There is no skip option. Loop through Step 3 → Step 4 until the user says they are done.

## Step 4 — Execute the chosen option

**Option 1 (new mind from template):** delegate to `/create-mind`

**Option 2 (existing local mind):** delegate to `/add-mind`

**Option 3 (register from another instance):**
- Ask for: mind name, host URL of the other instance (e.g. `http://192.168.4.64:8420`), and broker endpoint
- Register with the local broker:
  ```bash
  curl -s -X POST http://localhost:8420/broker/minds \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"<mind_name>\", \"host\": \"<host_url>\", \"broker_url\": \"<broker_endpoint>\"}"
  ```
- Verify: send a test ping via the broker and confirm the mind responds

## Step 5 — Per-mind volume config

*(Skip for Option 3 — no local container)*

Ask what host directories this mind should access:
- Default Docker named volume (most isolated)
- Host directory mounts: which paths, read-only or read-write?

## Step 5b — Personality setup

*(Skip for Option 3 — no local container)*

Ask: "Would you like to define `<mind_name>`'s personality and seed its identity now?"
- If yes → delegate to `/setup-personality <mind_id>`
- If no → "You can run `/setup-personality <mind_id>` anytime."

## Step 6 — Per-mind auth

*(Skip for Option 3 — auth is on the remote instance)*

If per-mind auth model was chosen in `/setup-auth`:
```bash
docker exec -it <container-name> claude
```
Or for API key: configure the key in the mind container env. Verify auth works.

## Step 7 — Skill selection

*(Skip for Option 3 — skills are configured on the remote instance)*

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

## Step 9 — Broker federation (federated and spoke installs only)

**If `federated`:**
Ask: "Do you want to configure broker federation with another Hive Mind instance now?"
- If yes: ask for the Hub's broker URL (e.g. `http://192.168.4.64:8420`)
  - Register this instance with the Hub:
    ```bash
    curl -s -X POST http://<hub>/broker/minds \
      -H "Content-Type: application/json" \
      -d "{\"name\": \"<this_instance_name>\", \"host\": \"http://<this_ip>:8420\"}"
    ```
  - Verify cross-instance messaging works
- If no → "You can configure federation later by re-running `/setup-mind`."

**If `spoke`:**
Ask for the managing Hub's URL and register this mind with it (same as above).

## Step 10 — Final mind roster

Present a table of all minds: name, type (local/remote), status, skills installed.
