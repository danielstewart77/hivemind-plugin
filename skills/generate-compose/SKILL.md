---
name: generate-compose
description: Wire every per-mind container fragment (minds/<name>/container/compose.yaml) into the top-level docker-compose.yml include list. Use after adding or removing a containerised mind.
argument-hint: "[--standalone <mind-name>]"
user-invocable: true
tools: Bash, Read, Write
---

# generate-compose

**If `--standalone <name>` is passed:** jump to [Standalone Mode](#standalone-mode) below.

Each containerised mind owns a complete Compose fragment at
`minds/<name>/container/compose.yaml` (a single-service document, authored by
`/create-mind`). The top-level `docker-compose.yml` wires them in through its
`include:` list — one `- path:` entry per mind. This skill keeps that list in
sync with the fragments on disk. It does not generate service bodies; the
fragment is the source of truth.

## Step 1 — Scan for fragments

```bash
for d in minds/*/; do
  name=$(basename "$d")
  [[ "$name" == "__pycache__" || "$name" == "example" ]] && continue
  [ -f "$d/container/compose.yaml" ] && echo "minds/$name/container/compose.yaml"
done
```

## Step 2 — Reconcile the include list

Read `docker-compose.yml`. Ensure its top-level `include:` block lists every
fragment found in Step 1, and drop any `- path:` entry whose fragment no longer
exists. Preserve all other content untouched.

```yaml
include:
  - path: minds/<name>/container/compose.yaml
  # one line per mind
```

If `docker-compose.yml` does not exist yet, create it from
`docker-compose.example.yml` first (`cp docker-compose.example.yml docker-compose.yml`),
then reconcile.

Note: fragments join the external `hivemind` network and reach the gateway at
`http://hive-comms:8424`. There is no `server` service or `hive_mind_net` to
depend on — those belong to the retired single-repo architecture.

## Step 3 — Validate

```bash
docker compose config > /dev/null 2>&1 && echo "Compose config valid" || echo "INVALID — check syntax"
```

## Step 4 — Report

List which fragments are now included, which include lines were removed, and the
validation result.

---

## Standalone Mode

Bring up a single mind fragment on its own, without editing the federated
`docker-compose.yml`:

```bash
docker compose -f minds/<name>/container/compose.yaml up -d
```

The fragment already joins the external `hivemind` network and points
`HIVE_MIND_SERVER_URL` at `http://hive-comms:8424`, so the mind is reachable by
comms as soon as it is registered (see `/setup-mind`). Validate the fragment with:

```bash
docker compose -f minds/<name>/container/compose.yaml config > /dev/null 2>&1 \
  && echo "Compose config valid" || echo "INVALID — check syntax"
```
