import json, os, sys

cfg = os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude"))
inst = os.path.join(cfg, "plugins", "installed_plugins.json")
log = open(os.path.join(os.path.expanduser("~"), ".hivemind_sync.log"), "a")

if not os.path.exists(inst):
    log.write(f"[hivemind sync] installed_plugins.json not found at {inst}\n")
    log.close()
    sys.exit(0)

try:
    data = json.load(open(inst))
except Exception as e:
    log.write(f"[hivemind sync] failed to parse installed_plugins.json: {e}\n")
    log.close()
    sys.exit(1)

skills_dir = os.path.join(cfg, "skills")
agents_dir = os.path.join(cfg, "agents")
os.makedirs(skills_dir, exist_ok=True)
os.makedirs(agents_dir, exist_ok=True)

synced = 0
for plugin_key, entries in data.get("plugins", {}).items():
    if not entries:
        continue
    install_path = entries[0].get("installPath", "")
    if not install_path or not os.path.isdir(install_path):
        log.write(f"[hivemind sync] {plugin_key}: installPath missing or not a dir: {install_path}\n")
        continue

    # Symlink skills
    plugin_skills = os.path.join(install_path, "skills")
    if os.path.isdir(plugin_skills):
        for skill in os.listdir(plugin_skills):
            src = os.path.join(plugin_skills, skill)
            dst = os.path.join(skills_dir, skill)
            if os.path.islink(dst):
                if os.readlink(dst) != src:
                    os.unlink(dst)
                    os.symlink(src, dst)
                    synced += 1
            elif not os.path.exists(dst):
                os.symlink(src, dst)
                synced += 1

    # Symlink agents
    plugin_agents = os.path.join(install_path, "agents")
    if os.path.isdir(plugin_agents):
        for agent in os.listdir(plugin_agents):
            src = os.path.join(plugin_agents, agent)
            dst = os.path.join(agents_dir, agent)
            if os.path.islink(dst):
                if os.readlink(dst) != src:
                    os.unlink(dst)
                    os.symlink(src, dst)
                    synced += 1
            elif not os.path.exists(dst):
                os.symlink(src, dst)
                synced += 1

log.write(f"[hivemind sync] done — {synced} symlinks created/updated across {len(data.get('plugins',{}))} plugins\n")
log.close()
