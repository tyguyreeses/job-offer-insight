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


def print_myteam_tree(base: Path) -> None:
    myteam = get_myteam_root(base)
    print_directory_tree(myteam)


def main() -> int:
    base = Path(__file__).resolve().parent  # .myteam/<role>
    print_instructions(base)

    print_myteam_tree(base)
    
    myteam = get_myteam_root(base)
    list_roles(base, myteam, [])
    list_skills(base, myteam, [])
    list_tools(base, myteam, [])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
