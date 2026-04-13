---
name: setup-mind
description: Set up minds for the Hive Mind system. Create new minds, import existing ones, or re-register discovered minds. Configures per-mind volumes and authentication.
user-invocable: true
tools: Bash, Read
---

# setup-mind

Set up minds for the system. At least one mind is needed.

## Step 0 — Topology selection

Ask the user which deployment topology they want:

1. **Federated (recommended)** — Minds run as containers routed through the main Hive Mind gateway and broker. Supports multi-mind conversations, group chat, inter-mind messaging, and memory. Requires the full server stack (nervous system already running).
2. **Standalone** — A single mind with a minimal container stack. No gateway dependency, no broker, no inter-mind features. Best for a first install or a dedicated single-purpose mind.
3. **Remote Federated** — A second Hive Mind instance on another machine, linked to this one via the broker API. Delegates to `/setup-remote`.

> **Warning (Standalone):** If this is your first mind and you choose standalone, you will not be able to use multi-mind features (group chat, inter-mind messaging, orchestrator). Federated is recommended unless you have a specific reason to stay isolated.

Store the topology as `TOPOLOGY` (values: `federated`, `standalone`, `remote`). All subsequent steps branch on this value.

**If `remote`:** delegate to `/setup-remote` and exit this skill.

## Step 1 — Prerequisite check

**If `federated`:**
```bash
curl -sf http://localhost:8420/sessions > /dev/null || echo "Gateway not reachable. Run /setup-nervous-system first."
curl -sf http://localhost:8420/broker/minds | jq length
```
Verify at least one provider is configured (check config.yaml providers block).

**If `standalone`:** Skip gateway check — broker is not required. Verify Docker is running.

## Step 2 — List current minds

**If `federated`:**
```bash
# Registered minds
curl -sf http://localhost:8420/broker/minds | jq -r ".[].name"

# Unregistered mind folders
for d in minds/*/; do
  name=$(basename "$d")
  [[ "$name" == "__pycache__" ]] && continue
  if [ -f "$d/MIND.md" ]; then
    registered=$(curl -sf http://localhost:8420/broker/minds | jq -r ".[] | select(.name==\"$name\") | .name")
    [ -z "$registered" ] && echo "UNREGISTERED: $name (has MIND.md)"
  fi
done
```

**If `standalone`:** Skip broker listing — no broker running yet.

## Step 3 — Present options

1. **Create a new mind from template** → delegates to `/create-mind`
2. **Add an existing local mind** → delegates to `/add-mind`
3. **Connect a remote mind** → delegates to `/add-mind` (remote scenario)
4. **Import a mind from another Hive Mind instance** → ask for the `minds/<name>/` folder path or archive, copy it in, delegate to `/add-mind` for registration
5. **Re-register a discovered mind** (folder exists, not in broker) → delegates to `/add-mind`
6. **Skip** — no changes needed

## Step 4 — Execute

Delegate to the appropriate skill based on user choice. Pass `--standalone` flag to `/create-mind` and `/add-mind` if `TOPOLOGY=standalone`.

## Step 5 — Per-mind volume config

Ask what host directories this mind should access:
- Internal-only volumes (default Docker named volume, most isolated)
- Host directory mounts: which paths, read-only or read-write?

## Step 5b — Personality setup

After the mind container is running (or after `/add-mind` confirms routability):

Ask: "Would you like to define `<mind_name>`'s personality and seed its identity now?"
- If yes → delegate to `/setup-personality <mind_id>`
- If no → "Skip. Run `/setup-personality <mind_id>` anytime to set up identity."

**If standalone topology:** same flow — `/setup-personality` does not require the broker.

## Step 6 — Per-mind auth

If per-mind auth model was chosen in `/setup-auth`:
- Guide user through authenticating inside the new mind container:
  ```bash
  docker exec -it <container-name> claude
  ```
- Or for API key: configure the key in the mind container env
- Verify auth works

## Step 7 — Skill selection

Read `skills/SKILLS.md` to get the canonical skill groups and descriptions.

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

For each selected group, list the individual skills from `SKILLS.md` and confirm, or offer "install whole group" as a default.

Note skipped groups: "You can add more skills later by re-running `/setup-mind`."

## Step 8 — Repeat or finish

Ask: "Would you like to set up another mind?"
- If yes → return to Step 3
- If no → present final mind roster and exit
