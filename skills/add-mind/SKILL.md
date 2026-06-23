---
name: add-mind
description: Connects a mind to the Hive Mind system. Supports three install types — Docker (containerised in this stack), remote (separate host), or bare-metal (systemd service on this host outside Docker). Scaffolds and registers accordingly.
argument-hint: "[name]"
user-invocable: true
---

# add-mind

`$ARGUMENTS[0]` = mind name. Ask if missing.

Every mind is its own process — a container, a bare-metal service, or a remote
host. There is no shared/subprocess mode. Each mind runs its own
`implementation.py` as an HTTP server (FastAPI) that comms dispatches sessions
to over the `hivemind` network.

The gateway/broker is the `comms` container. Broker writes need the admin token;
reads and session calls need the regular token. Where the coordinates live
depends on whether comms runs on this host or on a managing instance:

```bash
# instance (comms is local): read from the local nervous-system repo
NS=~/Storage/Dev/hive_nervous_system        # adjust to the nervous-system repo path
if [ -f "$NS/.env" ]; then
  COMMS_URL=http://localhost:8426
  CT=$(grep COMMS_BEARER_TOKEN "$NS/.env" | cut -d= -f2)
  AT=$(grep COMMS_ADMIN_BEARER_TOKEN "$NS/.env" | cut -d= -f2)
else
  # spoke (comms is remote): read the coordinates /setup-nervous-system wrote
  ENV=<hive_mind dir>/.env
  COMMS_URL=$(grep ^COMMS_URL= "$ENV" | cut -d= -f2-)
  CT=$(grep ^COMMS_BEARER_TOKEN= "$ENV" | cut -d= -f2-)
  AT=$(grep ^COMMS_ADMIN_BEARER_TOKEN= "$ENV" | cut -d= -f2-)
fi
```

Use `$COMMS_URL` for every broker/session call below — never a hardcoded
`localhost:8426`. In-container minds on the central host reach comms at
`http://hive-comms:8424`; a satellite mind reaches it at the remote `$COMMS_URL`.

## Step 1 — Determine scenario

Check if `minds/$ARGUMENTS[0]/` directory exists:

- **No directory → Scenario A, B, or D.** Ask the user:
  - "How does this mind run?"
  - "1. Docker — runs as a container in this stack"
  - "2. Remote — runs on a different host (separate machine or VM)"
  - "3. Bare-metal — runs directly on this host outside Docker (e.g. a systemd service at a localhost port)"
  - If 1 → Scenario A
  - If 2 → Scenario B
  - If 3 → Scenario D

- **Directory exists → Scenario C (re-registration).** The mind folder is already there but may not be in the broker.

Collect from the user (or read from `minds/<name>/runtime.yaml` for Scenario C):
- `name` (from argument)
- `mind_id` — the durable UUID. For a new mind, generate one: `python3 -c "import uuid;print(uuid.uuid4())"`. For Scenario C read it from `runtime.yaml`.
- `gateway_url` — where comms dispatches:
  - Docker (A): `http://hive-mind-<name>:<port>` (the container name on the `hivemind` network; port = the mind's `MIND_SERVER_PORT`, e.g. 8421)
  - Bare-metal (D): `http://localhost:<port>` if comms is on this same host; on a
    satellite host (comms remote) it must be this host's LAN address so comms can
    dispatch back, e.g. `http://192.168.5.64:<port>`
  - Remote (B): the remote host's URL, ask the user
- `model` (e.g. `sonnet`, `gpt-oss:20b`)
- `harness` (e.g. `claude`, `codex`)

For Scenario B: verify the external gateway is reachable before proceeding:
```bash
curl -sf -H "Authorization: Bearer $CT" <gateway_url>/health > /dev/null && echo "Reachable" || echo "UNREACHABLE"
```

## Step 2 — Scaffold runtime config (Scenarios A and B)

Each mind is configured by `minds/<name>/runtime.yaml`, not a MIND.md file:

```yaml
name: <name>
mind_id: <uuid>
default_model: <model>
provider: <anthropic | ollama | codex>
runtime_config_dir: /usr/src/app/minds/<name>/.codex   # or .claude per harness
env:
  # provider-specific, e.g. for ollama:
  OLLAMA_BASE_URL: http://<ollama-host>:11434/v1
```

**Scenario B (remote):** the mind lives on the other host; only register the
contact here. Add `remote: true` to your notes and skip Steps 3–4.

**Scenario D (bare-metal local):** the mind project lives at its own path on the
host. Ask for the port and confirm it is up before registering:
```bash
curl -sf http://localhost:<port>/health && echo "UP" || echo "NOT RUNNING — start the service first"
```
If not running, stop and tell the user to start the service, then re-run `/add-mind`. Skip to Step 5.

For Scenario C: `runtime.yaml` already exists — skip to Step 4.

## Step 3 — Scaffold implementation (Scenario A only)

Pick the template matching harness + model family. NOTE: only
`codex_cli_ollama.py` currently embeds the in-container FastAPI server; the
Claude templates still need that server ported in before they can run as a
container (see the mind-templates code task). Copy the template:
```bash
mkdir -p minds/<name>/container
cp mind_templates/<selected>.py minds/<name>/implementation.py
sed -i 's/MIND_NAME/<name>/g' minds/<name>/implementation.py
touch minds/<name>/__init__.py
```

Write `minds/<name>/container/compose.yaml` — a single-service fragment that
joins the external `hivemind` network and points at comms:
```yaml
services:
  <name>:
    image: hive_mind:latest
    container_name: hive-mind-<name>
    working_dir: /usr/src/app
    environment:
      - MIND_ID=<uuid>
      - MIND_SERVER_PORT=<port>
      - HIVE_MIND_SERVER_URL=http://hive-comms:8424
      - PYTHONPATH=/usr/src/app/vendor
      - PYTHONNOUSERSITE=1
    volumes:
      - <project-dir>:/usr/src/app:rw
    networks:
      - hivemind
    restart: unless-stopped
    command: ["/opt/venv/bin/python3", "-m", "minds.<name>.implementation"]

networks:
  hivemind:
    external: true
    name: hivemind
```

## Step 4 — Wire and start the container (Scenario A only)

Wire the fragment into the federated compose and start it:
```bash
# add minds/<name>/container/compose.yaml to docker-compose.yml include list
/generate-compose
docker compose -f minds/<name>/container/compose.yaml up -d
curl -sf http://localhost:<port>/health && echo "UP" || docker logs hive-mind-<name> --tail 30
```

## Step 5 — Register with broker

```bash
curl -s -X POST $COMMS_URL/broker/minds \
  -H "Authorization: Bearer $AT" -H "Content-Type: application/json" \
  -d '{"mind_id":"<uuid>","name":"<name>","gateway_url":"<gateway_url>","model":"<model>","harness":"<harness>"}'
```

If the response contains an error, stop and surface it to the user.

## Step 6 — Verify routability

Create a test session (note the response field is `id`):
```bash
curl -s -X POST $COMMS_URL/sessions \
  -H "Authorization: Bearer $AT" -H "Content-Type: application/json" \
  -d '{"owner_type":"test","owner_ref":"add-mind-verify","client_ref":"add-mind","mind_id":"<uuid>"}'
```

Send a test message (SSE stream) to the returned session id:
```bash
curl -s -N -X POST $COMMS_URL/sessions/<session_id>/message \
  -H "Authorization: Bearer $AT" -H "Content-Type: application/json" \
  -d '{"content":"Respond with exactly: registration verified."}'
```

Check the stream for "registration verified", then clean up:
```bash
curl -s -X DELETE -H "Authorization: Bearer $AT" $COMMS_URL/sessions/<session_id>
```

If routability check fails, surface the error clearly but do NOT roll back the
registration — the mind is registered, it just couldn't respond yet.

## Step 7 — Report

Summarize:
- Scenario handled (A=Docker / B=Remote / C=Re-registration / D=Bare-metal)
- Files created (runtime.yaml, implementation.py, container/compose.yaml, __init__.py — Scenario A only)
- Containerised (yes/no, compose include updated — Scenario A only)
- Broker registration status
- Routability verification result
