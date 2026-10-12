from __future__ import annotations

import shutil
from pathlib import Path

from .project import Project, walk_files

CLEAN_TYPES = ("build", "png", "svg", "symlink")


def plan_clean(project: Project, kind: str = "build") -> list[Path]:
    """List generated paths to remove. Only build/ is ever considered, never icons/ or other project files."""
    project.check_build_dir()
    if not project.build_dir.is_dir():
        return []
    paths = walk_files(project.build_dir)
    if kind == "build":
        return paths
    if kind == "symlink":
        return [path for path in paths if path.is_symlink()]
    return [path for path in paths if path.suffix == f".{kind}"]


def apply_clean(project: Project, kind: str, paths: list[Path]) -> None:
    """Remove the selected generated paths without following links outside the build tree."""
    if kind == "build":
        if project.build_dir.is_dir():
            shutil.rmtree(project.build_dir)
        return
    for path in paths:
        path.unlink()
