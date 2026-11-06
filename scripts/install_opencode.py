#!/usr/bin/env python3
"""Expose the complete shared bundle to OpenCode without editing its config."""

import argparse
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def install(config_dir, source=ROOT):
    config_dir, source = Path(config_dir).expanduser().absolute(), Path(source).resolve()
    # Keep the entire tree together: skills use ../../reference and ../../scripts.
    links = {config_dir / "skills/agent-collab": source}
    for command in sorted((source / "opencode/commands").glob("*.md")):
        links[config_dir / "commands" / command.name] = command
    links[config_dir / "agents/agent-collab-reviewer.md"] = (
        source / "opencode/agents/agent-collab-reviewer.md"
    )
    for target, origin in links.items():
        if not origin.exists():
            raise ValueError(f"Missing source: {origin}")
        if target.is_symlink() and target.resolve() == origin:
            continue
        if target.exists() or target.is_symlink():
            raise ValueError(f"Existing unrelated file or link: {target}; nothing installed")
    for target, origin in links.items():
        if target.is_symlink():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(origin, target_is_directory=origin.is_dir())
    return links


def main():
    default = os.environ.get("OPENCODE_CONFIG_DIR") or str(
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "opencode"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=default,
                        help="OpenCode config directory (default: user config)")
    args = parser.parse_args()
    try:
        for target, source in install(args.config_dir).items():
            print(f"{target} -> {source}")
    except ValueError as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
