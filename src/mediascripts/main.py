#!/bin/bash

import argparse
import importlib.metadata
import shutil
from pathlib import Path


def create_script_symlinks(dest_dir: Path):
    # Resolve the scripts directory from this file's location
    scripts_dir = Path(__file__).resolve().parent
    shell_dir = scripts_dir / "shell"

    # Symlink every media* console script entry point (except this script itself)
    eps = importlib.metadata.entry_points(group="console_scripts")
    for ep in eps:
        package_name = ep.dist.name if ep.dist else "Unknown"
        if not package_name.startswith("media"):
            continue
        if ep.name == "mediascripts":
            continue
        command_path = shutil.which(ep.name)
        if command_path is None:
            print(f"  warning: {ep.name} not found on PATH, skipping")
            continue
        dest = dest_dir / ep.name
        if dest.exists() or dest.is_symlink():
            print(f"  skipping {dest.name} (already exists)")
            continue
        dest.symlink_to(command_path)
        print(f"  {dest.name} -> {command_path}")

    # Symlink every shell script in scripts/shell with hyphenated name
    if shell_dir.is_dir():
        for shell_script in sorted(shell_dir.glob("*.sh")):
            name = shell_script.stem.replace("_", "-")
            dest = dest_dir / name
            if dest.exists() or dest.is_symlink():
                print(f"  skipping {dest.name} (already exists)")
                continue
            dest.symlink_to(shell_script)
            print(f"  {dest.name} -> {shell_script}")
    else:
        print(f"  warning: shell script directory not found: {shell_dir}")


def list_media_scripts():
    # Fetch all entry points belonging to the 'console_scripts' group
    eps = importlib.metadata.entry_points(group="console_scripts")

    # Group command names by the scripts subdirectory of the target module,
    # e.g. "scripts.convert.convert_covers:main" belongs to the "convert" group
    groups: dict[str, list[str]] = {}
    for ep in eps:
        # ep.value holds the 'module:function' path
        # ep.dist holds metadata about the package providing it (if available)
        package_name = ep.dist.name if ep.dist else "Unknown"
        if not package_name.startswith("media"):
            continue
        parts = ep.value.split(":")[0].split(".")
        group = parts[1] if len(parts) > 2 else "(root)"
        if ep.name != "mediascripts":
            groups.setdefault(group, []).append(ep.name)

    for group in sorted(groups):
        print(f"{group}:")
        for name in sorted(groups[group]):
            print(f"  {name}")


def main():
    parser = argparse.ArgumentParser(
        description="Utility for media* console script entry points."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list all media* console script entry points, grouped by scripts subdirectory",
    )
    parser.add_argument(
        "--create-script-symlinks",
        action="store_true",
        help="create hyphenated symlinks in the current directory to every console entry script "
        "and every shell script in scripts/shell",
    )
    args = parser.parse_args()
    if args.list:
        list_media_scripts()
    elif args.create_script_symlinks:
        create_script_symlinks(Path.cwd())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
