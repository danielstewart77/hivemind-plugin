---
name: create-mind
description: Create a new mind from a template. Scaffolds MIND.md and implementation.py, then registers with the broker. Use when the user wants to add a brand-new mind to the system.
argument-hint: "[name] [--standalone]"
user-invocable: true
---

# create-mind

`$ARGUMENTS[0]` = mind name. Ask if missing.
`$ARGUMENTS[1]` = `--standalone` if creating a standalone (non-federated) mind. Default: federated.

Set `STANDALONE=true` if `--standalone` is present.

## Step 1 — Gather info

Ask in this order:

**1a. Harness:**
```
Which harness should this mind use?

(A) Claude — uses the Claude CLI or SDK. Supports Claude models (sonnet, opus,
    haiku) and Ollama models.

(B) Codex — uses the Codex CLI or SDK. Supports OpenAI Codex models and
    Ollama models.
```

**1b. Model (ask based on harness chosen):**

If Claude:
```
Which model?
  (A) sonnet   — fast, capable, recommended
  (B) opus     — most capable, slower
  (C) haiku    — lightweight, fastest
  (D) Ollama   — local model (you'll be asked for the model name)
```

If Codex:
```
Which model?
  (A) codex-mini  — lightweight Codex model
  (B) o3          — most capable Codex model
  (C) Ollama      — local model (you'll be asked for the model name)
```

If Ollama (either harness): ask for the model name (e.g. `llama3`, `mistral`).

**1c. Soul seed — ask these questions one at a time:**

1. "What is Sergeant's role? What does it do — what problems does it solve?"
2. "What is Sergeant's identity? How does it present itself — its personality,
   tone, and character? (This is separate from what it does.)"
3. "Would you like to write a backstory or manifesto for this character —
   something that gives it history, values, or a point of view?"
   - If yes: ask open-ended, let the user write as much or as little as they want.
     Incorporate it into the soul seed.
   - If no: skip. The soul seed will be built from name + role + identity alone.

Do not tell the user to be brief. Let them say as much or as little as they want.

## Step 2 — Select template

Based on harness and model, auto-select the template. Do not ask the user to choose a template — they already answered the relevant questions in Step 1.

Mapping:
- Claude + Claude model → `claude_cli_claude` (tested)
- Claude + Ollama       → `claude_cli_ollama` (tested)
- Codex + Codex model  → `codex_cli_codex` (tested)
- Codex + Ollama       → `codex_cli_ollama` (untested — warn the user)

If the selected template is marked `# UNTESTED` in the file, tell the user:
"This combination is untested — it may need adjustments. Continuing anyway."

## Step 3 — Scaffold files

```bash
mkdir -p minds/<name>
cp mind_templates/<selected>.py minds/<name>/implementation.py
sed -i 's/MIND_NAME/<name>/g' minds/<name>/implementation.py
touch minds/<name>/__init__.py
```

Write `minds/<name>/MIND.md` with frontmatter from user's choices and soul seed from their description.

## Step 4 — Container isolation

Ask: "Should this mind run in its own isolated container? (recommended — gives each mind
granular control over what it can access)"

Default: **yes**. Own container is recommended because it lets you control exactly what
each mind can see and write. A shared container means all minds have the same access.

**If yes (own container):**

Show the user the standard mounts that other minds use, and ask them to confirm or
customize. Never say "defaults only" — always list the explicit paths:

```
These are the standard mounts used by other minds on this system:

  /usr/src/app  ←  /home/<user>/hive_mind  (rw)  — project code
  /home/hivemind/.host-claude  ←  /home/<user>/.claude  (ro)  — host Claude auth
  /home/hivemind/.claude-config  ←  /home/<user>/hive_mind/minds/<name>/.claude  (rw)  — per-mind config

Note: host bind mounts (paths on your drive) are recommended over Docker named volumes.
Host mounts give you immediate visibility into what the mind is reading and writing.
Docker named volumes are managed by Docker and stored in a system location — harder to
inspect directly.

Would you like to:
  (A) Use these mounts as-is
  (B) Customize — add, remove, or change paths
```

If the user wants a more restricted or different set, let them list paths freely.
Ask which secrets the mind needs.
Write the `container:` block into the MIND.md frontmatter.
Note: `/add-mind` will call `/generate-compose` to update docker-compose.yml.

**If no (shared container):**
The mind runs as a subprocess inside the main hive_mind container. It inherits all
mounts from that container with no additional isolation.

## Step 5 — Register or Generate Standalone Compose

**If federated:**
Delegate to `/add-mind <name>` (it will detect Scenario C — directory exists — and handle compose generation, registration, and routability check).

**If standalone:**
Delegate to `/generate-compose <name> --standalone` to generate a minimal `docker-compose.yml` with only the mind container and a lightweight message handler. No broker, no gateway, no Neo4j.

After compose generation:
```bash
docker compose up -d --build
```

Confirm the mind container is running:
```bash
docker compose ps
```

Note: standalone minds cannot be registered with the broker. Skip the broker registration step entirely.

## Step 6 — Report

- Template used
- Topology: federated or standalone
- Files created
- Registration and routability status (federated only)
- Container status (standalone)
