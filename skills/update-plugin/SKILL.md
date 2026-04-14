---
name: update-plugin
description: Update the hivemind-claude-plugin to the latest version from GitHub and refresh all skill symlinks.
user-invocable: true
tools: Bash
---

# update-plugin

Pull the latest plugin version from GitHub, update the install record, remove stale cache folders, and refresh skill symlinks.

```bash
PLUGIN_CACHE="$HOME/.claude-config/plugins/cache/danielstewart77/hivemind-plugin"
INSTALLED_JSON="$HOME/.claude-config/plugins/installed_plugins.json"
SKILLS_DIR="$HOME/.claude-config/skills"
AGENTS_DIR="$HOME/.claude-config/agents"
REPO_URL="https://github.com/danielstewart77/hivemind-plugin.git"
PLUGIN_KEY="hivemind@danielstewart77"

# Get latest commit SHA from GitHub
LATEST_SHA=$(git ls-remote "$REPO_URL" HEAD 2>/dev/null | cut -f1)
if [ -z "$LATEST_SHA" ]; then
  echo "ERROR: Could not reach GitHub to check for updates."
  exit 1
fi
LATEST_SHORT="${LATEST_SHA:0:12}"

# Get currently installed version
CURRENT_SHORT=$(python3 -c "
import json, os
path = os.path.expanduser('$INSTALLED_JSON')
d = json.load(open(path))
entries = d.get('plugins', {}).get('$PLUGIN_KEY', [])
print(entries[0].get('version', '') if entries else '')
" 2>/dev/null)

if [ "$LATEST_SHORT" = "$CURRENT_SHORT" ]; then
  echo "Already up to date ($LATEST_SHORT)."
  # Refresh symlinks anyway in case they're stale
  bash "$HOME/.claude-config/hooks/plugin_skills_sync.sh" 2>/dev/null || true
  echo "Skill symlinks verified."
  exit 0
fi

echo "Updating: $CURRENT_SHORT → $LATEST_SHORT"

# Clone latest into cache
TARGET_DIR="$PLUGIN_CACHE/$LATEST_SHORT"
if [ ! -d "$TARGET_DIR" ]; then
  git clone --depth 1 "$REPO_URL" "$TARGET_DIR" 2>&1
  if [ $? -ne 0 ]; then
    echo "ERROR: Clone failed."
    exit 1
  fi
fi

# Update installed_plugins.json
NOW=$(python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'))")
python3 -c "
import json, os
path = os.path.expanduser('$INSTALLED_JSON')
d = json.load(open(path))
d['plugins']['$PLUGIN_KEY'] = [{
    'scope': 'user',
    'installPath': '$TARGET_DIR',
    'version': '$LATEST_SHORT',
    'installedAt': d['plugins']['$PLUGIN_KEY'][0].get('installedAt', '$NOW'),
    'lastUpdated': '$NOW',
    'gitCommitSha': '$LATEST_SHA'
}]
json.dump(d, open(path, 'w'), indent=2)
open(path, 'a').write('\n')
print('Install record updated.')
"

# Remove stale cache folders
for dir in "$PLUGIN_CACHE"/*/; do
  ver=$(basename "$dir")
  if [ "$ver" != "$LATEST_SHORT" ]; then
    rm -rf "$dir"
    echo "Removed stale cache: $ver"
  fi
done

# Refresh skill and agent symlinks
# Try the sync hook first (available after /setup-mind), fall back to manual symlinks
if [ -f "$HOME/.claude-config/hooks/plugin_skills_sync.sh" ]; then
  bash "$HOME/.claude-config/hooks/plugin_skills_sync.sh" 2>/dev/null
else
  # Manual symlink refresh
  for skill_dir in "$TARGET_DIR/skills"/*/; do
    skill=$(basename "$skill_dir")
    ln -sfn "$skill_dir" "$SKILLS_DIR/$skill"
  done
  for agent_file in "$TARGET_DIR/agents"/*.md; do
    [ -f "$agent_file" ] || continue
    ln -sfn "$agent_file" "$AGENTS_DIR/$(basename "$agent_file")"
  done
fi
echo "Skill and agent symlinks updated."

echo "Plugin updated to $LATEST_SHORT. Skills are live — no session restart needed."
```
