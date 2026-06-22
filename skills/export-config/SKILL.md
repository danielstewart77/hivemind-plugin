---
name: export-config
description: Export the current Hive Mind configuration for migration or duplication. Produces a portable config bundle that /setup-config can import on another machine.
user-invocable: true
tools: Bash, Read
---

# export-config

Export the current deployment configuration for migration or duplication.

## Step 1 — Scan current state

Detect all installed components:
```bash
# Providers
grep -A1 "^providers:" config.yaml

# Minds
CT=$(grep COMMS_BEARER_TOKEN ~/Storage/Dev/hive_nervous_system/.env | cut -d= -f2)
curl -sf http://localhost:8426/broker/minds -H "Authorization: Bearer $CT" | jq -r ".[].name"

# Running containers
docker compose ps --format "{{.Name}} {{.Status}}"

# Compose profile
grep COMPOSE_PROFILES .env 2>/dev/null
```

## Step 2 — Export config files

```bash
mkdir -p hive-mind-export
cp config.yaml hive-mind-export/
cp .env hive-mind-export/ 2>/dev/null
cp .mcp.json hive-mind-export/ 2>/dev/null
cp .mcp.container.json hive-mind-export/ 2>/dev/null
```

Sanitize .env — replace secret values with placeholders.

## Step 3 — Export mind definitions

```bash
for d in minds/*/; do
  name=$(basename "$d")
  [[ "$name" == "__pycache__" ]] && continue
  if [ -f "$d/runtime.yaml" ]; then
    mkdir -p "hive-mind-export/minds/$name"
    cp "$d/runtime.yaml" "hive-mind-export/minds/$name/"
    [ -f "$d/container/compose.yaml" ] && mkdir -p "hive-mind-export/minds/$name/container" && cp "$d/container/compose.yaml" "hive-mind-export/minds/$name/container/"
  fi
done
```

Copy runtime.yaml (and the container compose fragment) only (not implementation.py — that comes from templates).

## Step 4 — Export secret manifest

List all secret keys in the keyring (names only, not values):
```bash
python3 -c "import keyring; keys = keyring.get_password('hive-mind', '_KEY_REGISTRY'); print(keys or '[]')" > hive-mind-export/secret-manifest.txt
```

## Step 5 — Export compose profile

```bash
echo "profile: ${COMPOSE_PROFILES:-cpu-only}" > hive-mind-export/profile.txt
```

## Step 6 — Bundle

```bash
tar czf hive-mind-export.tar.gz hive-mind-export/
rm -rf hive-mind-export/
```

## Step 7 — Report

What was exported, file location, how to import:
"To import on another machine: `/setup-config --import hive-mind-export.tar.gz`"
