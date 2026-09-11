#!/usr/bin/env python3
"""Auto-generate .claude-plugin/plugin.json and marketplace.json.

Usage:
    python3 scripts/plugin_generate.py \
        <name> <description> <version> <author> <repo> <license> <out_dir>
"""

import sys
import json
import os
import glob
import re

RESERVED_NAMES = {"agent-skills", "claude-plugin", "skills", "agents", "hooks"}


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def resolve_name(name: str, repo: str, author: str) -> str:
    if name not in RESERVED_NAMES:
        return name
    if repo and "/" in repo:
        owner = slugify(repo.split("/")[0])
        return f"{owner}-{name}"
    if author:
        return f"{slugify(author)}-{name}"
    return name


def discover_agents(root: str = ".") -> list[str]:
    return sorted(
        "./" + p
        for p in glob.glob(os.path.join(root, "agents/*.md"))
        if os.path.basename(p).lower() != "readme.md"
    )


def discover_skills(root: str = ".") -> list[str]:
    return sorted(
        "./" + d
        for d in glob.glob(os.path.join(root, "skills/*/"))
        if os.path.isdir(d)
    )


def build_plugin(name, description, version, author, repo, license_, agents, skills_root, hooks_path) -> dict:
    plugin = {
        "name": name,
        "description": description,
        "version": version,
        "author": {"name": author},
        "license": license_,
        "skills": skills_root,
        "agents": agents,
    }
    if repo:
        plugin["homepage"] = f"https://github.com/{repo}"
        plugin["repository"] = f"https://github.com/{repo}"
    if hooks_path:
        plugin["hooks"] = hooks_path
    return plugin


def build_marketplace(name, description, author, repo) -> dict:
    source = {"source": "github", "repo": repo} if repo else {"source": "local"}
    return {
        "name": name,
        "owner": {"name": author},
        "metadata": {"description": description},
        "plugins": [{"name": name, "source": source, "description": description}],
    }


def write_json(path: str, data: dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main() -> None:
    args = sys.argv[1:]
    if len(args) != 7:
        die(f"expected 7 arguments, got {len(args)}\n{__doc__}")

    name, description, version, author, repo, license_, out = args

    if not name:
        die("name must not be empty")
    if not version:
        die("version must not be empty")

    name = resolve_name(name, repo, author)

    agents = discover_agents()
    skills = discover_skills()
    hooks_path = "./hooks/hooks.json" if os.path.isfile("hooks/hooks.json") else None

    plugin = build_plugin(name, description, version, author, repo, license_, agents, "./skills", hooks_path)
    marketplace = build_marketplace(name, description, author, repo)

    os.makedirs(out, exist_ok=True)

    plugin_path = os.path.join(out, "plugin.json")
    marketplace_path = os.path.join(out, "marketplace.json")

    write_json(plugin_path, plugin)
    write_json(marketplace_path, marketplace)

    print(f"  wrote {plugin_path}  ({len(agents)} agent(s), {len(skills)} skill(s))")
    print(f"  wrote {marketplace_path}")


if __name__ == "__main__":
    main()
