import json, os

cfg = os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude"))
data = json.load(open(os.path.join(cfg, "plugins", "installed_plugins.json")))
skills_dir = os.path.join(cfg, "skills")
agents_dir = os.path.join(cfg, "agents")

os.makedirs(skills_dir, exist_ok=True)
os.makedirs(agents_dir, exist_ok=True)

for entries in data.get("plugins", {}).values():
    if not entries:
        continue
    install_path = entries[0]["installPath"]

    # Symlink skills
    plugin_skills = os.path.join(install_path, "skills")
    if os.path.isdir(plugin_skills):
        for skill in os.listdir(plugin_skills):
            src = os.path.join(plugin_skills, skill)
            dst = os.path.join(skills_dir, skill)
            if os.path.islink(dst) and os.readlink(dst) != src:
                os.unlink(dst)
            if not os.path.exists(dst):
                os.symlink(src, dst)

    # Symlink agents
    plugin_agents = os.path.join(install_path, "agents")
    if os.path.isdir(plugin_agents):
        for agent in os.listdir(plugin_agents):
            src = os.path.join(plugin_agents, agent)
            dst = os.path.join(agents_dir, agent)
            if os.path.islink(dst) and os.readlink(dst) != src:
                os.unlink(dst)
            if not os.path.exists(dst):
                os.symlink(src, dst)
