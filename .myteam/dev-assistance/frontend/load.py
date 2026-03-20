#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from myteam.utils import print_instructions, get_myteam_root, list_roles, list_skills, list_tools


def print_project_tree(root: Path, *, max_depth: int = 5) -> None:
    excluded_dirs = {
        ".git",
        ".idea",
        ".mypy_cache",
        ".next",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        ".vscode",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "venv",
    }
    excluded_files = {".DS_Store"}

    if not root.exists():
        print(f"Project path not found: {root}")
        return

    print(f"\n{root.name}")

    def walk(path: Path, prefix: str, depth: int) -> None:
        if depth >= max_depth:
            return

        entries = []
        for entry in path.iterdir():
            if entry.is_dir() and entry.name in excluded_dirs:
                continue
            if entry.is_file() and entry.name in excluded_files:
                continue
            entries.append(entry)
        entries.sort(key=lambda p: (p.is_file(), p.name.lower()))

        last_index = len(entries) - 1
        for i, entry in enumerate(entries):
            connector = "\\-- " if i == last_index else "|-- "
            print(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                next_prefix = f"{prefix}{'    ' if i == last_index else '|   '}"
                walk(entry, next_prefix, depth + 1)

    walk(root, "", 0)


def main() -> int:
    base = Path(__file__).resolve().parent  # .myteam/<role>
    print_instructions(base)

    project_root = base.parents[2]
    print_project_tree(project_root / "frontend")

    myteam = get_myteam_root(base)
    list_roles(base, myteam, [])
    list_skills(base, myteam, [])
    list_tools(base, myteam, [])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
