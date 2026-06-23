---
name: setup-nervous-system
description: Bootstrap and verify the Hive Mind nervous system — lucent (vector store + knowledge graph) and comms (gateway, broker, session manager). Deploys a new one locally, or connects this host to an existing hive-comms running on another machine.
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

## Step 0 — New deployment, or connect to an existing nervous system?

Before anything, ask which topology this is:

> Is this machine hosting its own nervous system, or connecting to an existing
> hive-comms running on another machine?
>
>   N) New — deploy lucent and comms locally on this host (default for a
>      standalone hive).
>   E) Existing — this is a satellite mind that joins a central hive; the
>      nervous system already runs elsewhere on the LAN.

If **New**, do Steps 1–6 below.
If **Existing**, skip Steps 1–6 entirely — no containers are deployed on this
host — and follow "Connecting to an existing nervous system" at the end instead.

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

---

# Connecting to an existing nervous system (the **Existing** path)

Use this when Step 0 was answered **E**. No lucent or comms containers run on
this host. This machine is a satellite mind; it only needs the coordinates of
the central nervous system and credentials to reach it. Skip Steps 1–6 above.

## Step E1 — Prompt for the central coordinates

Ask the operator for each value. The central host is whatever machine runs the
nervous system, reachable on the LAN (e.g. `192.168.4.64`):

- **comms base URL** — e.g. `http://192.168.4.64:8426`
- **comms bearer token** — the central host's `COMMS_BEARER_TOKEN`
- **comms admin bearer token** — the central host's `COMMS_ADMIN_BEARER_TOKEN`
  (required to register this mind with the broker)
- **lucent base URL** — e.g. `http://192.168.4.64:8425`
- **lucent bearer token** — the central host's `LUCENT_BEARER_TOKEN`

Do not invent or default these — they must come from the central host's
`hive_nervous_system/.env`.

## Step E2 — Verify reachability before writing anything

```bash
COMMS_URL=<comms base URL>; CT=<comms token>; AT=<comms admin token>
LUCENT_URL=<lucent base URL>; LT=<lucent token>
curl -s -o /dev/null -m 8 -w "comms /health        = %{http_code}\n" -H "Authorization: Bearer $CT" "$COMMS_URL/health"
curl -s -o /dev/null -m 8 -w "comms /broker/minds   = %{http_code}\n" -H "Authorization: Bearer $CT" "$COMMS_URL/broker/minds"
curl -s -o /dev/null -m 8 -w "lucent /health       = %{http_code}\n" "$LUCENT_URL/health"
curl -s -o /dev/null -m 8 -w "lucent /graph/schema = %{http_code}\n" -H "Authorization: Bearer $LT" "$LUCENT_URL/graph/schema"
```

All four must return `200`. Interpret failures before continuing:

- **A connection timeout** — routing or a firewall between this host and the
  central host. Routing must be open *both* ways: this mind reaches comms, and
  comms must reach *back* to this mind's server port to dispatch. Fix the network
  path first.
- **401 / 403** — wrong token for that service.

## Step E3 — Record the coordinates

Write them where the mind process and bots read them — `hive_mind/.env`:

```bash
cd <hive_mind dir>
for kv in "COMMS_URL=$COMMS_URL" "COMMS_BEARER_TOKEN=$CT" "COMMS_ADMIN_BEARER_TOKEN=$AT" "LUCENT_URL=$LUCENT_URL" "LUCENT_BEARER_TOKEN=$LT"; do
  key=${kv%%=*}
  grep -q "^$key=" .env 2>/dev/null && sed -i "s|^$key=.*|$kv|" .env || echo "$kv" >> .env
done
```

`/setup-mind` and the management skills read these from `hive_mind/.env` on a
satellite host (where no local `hive_nervous_system` exists). Two wiring rules
follow from being remote:

- The mind's process/container env must set `HIVE_MIND_SERVER_URL=$COMMS_URL` —
  the remote comms URL, **not** the in-network `hive-comms:8424` name, which only
  resolves on the central host's Docker network.
- When the mind registers, its `gateway_url` must be an address comms can reach
  it on — this host's LAN address and the mind's server port, e.g.
  `http://192.168.5.64:8421` — never `localhost`.

## Step E4 — Report

| Item | Status | Details |
|------|--------|---------|
| comms URL | OK/FAIL | reachable, /health 200 |
| lucent URL | OK/FAIL | reachable, /health + /graph/schema 200 |
| Coordinates | OK/FAIL | written to `hive_mind/.env` |
| Local containers | n/a | none deployed (satellite host) |
