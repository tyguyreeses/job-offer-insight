#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from myteam.utils import (
    get_myteam_root,
    list_roles,
    list_skills,
    list_tools,
    print_directory_tree,
    print_instructions,
)


def print_project_tree(root: Path, *, max_depth: int = 5) -> None:
    if not root.exists():
        print(f"Project path not found: {root}")
        return

    print_directory_tree(
        root=root,
        max_levels=max_depth,
        exclude=(
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
            ".DS_Store",
        ),
    )


def main() -> int:
    base = Path(__file__).resolve().parent  # .myteam/<role>
    print_instructions(base)

    project_root = base.parents[2]
    print_project_tree(project_root / "backend")

    myteam = get_myteam_root(base)
    list_roles(base, myteam, [])
    list_skills(base, myteam, [])
    list_tools(base, myteam, [])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
