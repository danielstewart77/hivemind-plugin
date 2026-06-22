---
name: setup-nervous-system
description: Bootstrap and verify the Hive Mind nervous system — lucent (vector store + knowledge graph) and comms (gateway, broker, session manager). Deploys from scratch if nothing exists.
user-invocable: true
tools: Bash, Read
---

# setup-nervous-system

Deploy and verify the core infrastructure. Everything else depends on this.

The nervous system is the standalone
[`hive_nervous_system`](https://github.com/danielstewart77/hive_nervous_system)
repo, not part of `hive_mind`. It runs two containers on the shared `hivemind`
Docker network:

- **lucent** (`hive-lucent`, host `8425` → container `8424`) — vector store +
  knowledge graph, backed by SQLite at `/data/lucent.db`. No Neo4j.
- **comms** (`hive-comms`, host `8426` → container `8424`) — gateway, broker,
  and session manager, backed by SQLite (`broker.db`, `sessions.db`).

## Step 1 — Docker prerequisites

```bash
docker info > /dev/null 2>&1 || echo "BLOCKER: Docker not running"
docker network inspect hivemind >/dev/null 2>&1 || docker network create hivemind
```

## Step 2 — Clone the nervous system repo

Ask for the parent directory for repos (default: the same parent as `hive_mind`,
e.g. `~/Storage/Dev`). If `hive_nervous_system` is missing there, clone it:

```bash
git clone https://github.com/danielstewart77/hive_nervous_system.git <parent>/hive_nervous_system
```

## Step 3 — Generate bearer tokens

`comms` and `lucent` gate every non-health route behind bearer tokens. Three are
required (comms needs an additional admin token for broker register/update/delete):

```bash
cd <parent>/hive_nervous_system
grep -q LUCENT_BEARER_TOKEN .env 2>/dev/null || echo "LUCENT_BEARER_TOKEN=$(openssl rand -hex 32)" >> .env
grep -q COMMS_BEARER_TOKEN .env 2>/dev/null || echo "COMMS_BEARER_TOKEN=$(openssl rand -hex 32)" >> .env
grep -q COMMS_ADMIN_BEARER_TOKEN .env 2>/dev/null || echo "COMMS_ADMIN_BEARER_TOKEN=$(openssl rand -hex 32)" >> .env
```

Note: `lucent` reads `/health` with no auth; every other route needs the lucent
token. `comms` gates `/health` too — pass the comms token to reach it.
`COMMS_ADMIN_BEARER_TOKEN` is mandatory: without it the broker register/update/
delete endpoints return 503 and no mind can be registered (see `/setup-mind`).

Surfaces and minds will need these tokens too. Record them where the consuming
component reads them — `hive_mind/.env` for the bots, each mind's container env
for the minds.

## Step 4 — Build and deploy

First build is slow (lucent pulls vector-store ML dependencies). Run it in the
background and poll:

```bash
cd <parent>/hive_nervous_system
docker compose up -d --build
```

Wait for both containers to report healthy:

```bash
for i in $(seq 1 60); do
  [ "$(docker ps --format '{{.Names}}' | grep -cE 'hive-lucent|hive-comms')" -ge 2 ] && break
  sleep 5
done
```

## Step 5 — Verify

```bash
LT=$(grep LUCENT_BEARER_TOKEN .env | cut -d= -f2)
CT=$(grep COMMS_BEARER_TOKEN .env | cut -d= -f2)
curl -s -o /dev/null -w "lucent /health  = %{http_code}\n" http://127.0.0.1:8425/health
curl -s -o /dev/null -w "lucent /graph/schema = %{http_code}\n" -H "Authorization: Bearer $LT" http://127.0.0.1:8425/graph/schema
curl -s -o /dev/null -w "comms /health  = %{http_code}\n" -H "Authorization: Bearer $CT" http://127.0.0.1:8426/health
curl -s -H "Authorization: Bearer $CT" http://127.0.0.1:8426/broker/minds | jq length   # 0 on a fresh box
```

All four should return `200` (and the broker mind count `0` on first install).
If a container is unhealthy: `docker logs hive-lucent --tail 30` or
`docker logs hive-comms --tail 30`.

## Step 6 — Report

Present status table:

| Component | Status | Details |
|-----------|--------|---------|
| Docker | OK/FAIL | version |
| Network | OK/FAIL | hivemind |
| lucent (8425) | OK/FAIL | container status, /health 200 |
| comms (8426) | OK/FAIL | container status, /health 200 |
| Broker | OK/FAIL | N minds registered |
| Tokens | OK/FAIL | lucent, comms, comms-admin set in .env |
