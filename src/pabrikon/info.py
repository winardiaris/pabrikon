from __future__ import annotations

from datetime import datetime

from .aliases import load_aliases
from .project import Project, walk_files

LIST_KINDS = ("icons", "directories", "aliases", "generated")


def list_items(project: Project, kind: str) -> list[str]:
    """Return sorted project entries for the requested listing category."""
    if kind == "icons":
        return [
            f"{source.key} [{source.directory}]"
            if source.directory != f"{source.context}/scalable"
            else source.key
            for source in project.sources()
        ]
    if kind == "directories":
        return list(project.config.build.directories)
    if kind == "aliases":
        return [f"{alias.key} -> {alias.target_key}" for alias in load_aliases(project)]
    if not project.build_dir.is_dir():
        return []
    return [path.relative_to(project.build_dir).as_posix() for path in walk_files(project.build_dir)]


def project_info(project: Project) -> dict:
    """Collect project metadata and source/generated asset counts."""
    generated = walk_files(project.build_dir) if project.build_dir.is_dir() else []
    index = project.build_dir / "index.theme"
    last_build = datetime.fromtimestamp(index.stat().st_mtime).strftime("%Y-%m-%d %H:%M") if index.is_file() else None
    return {
        "project": project.config.name,
        "version": project.config.version,
        "theme": project.config.theme.name,
        "icons": {
            "svg": len(project.sources()),
            "png": sum(1 for path in generated if path.suffix == ".png" and not path.is_symlink()),
            "aliases": len(load_aliases(project)),
        },
        "directories": {
            ctx: len(project.sources(ctx))
            for ctx in project.config.build.directories
        },
        "sizes": project.config.build.sizes,
        "last_build": last_build,
    }


def format_info(info: dict) -> list[str]:
    """Format a project summary as concise human-readable output lines."""
    icons = info["icons"]
    lines = [
        f"Project: {info['project']}",
        f"Version: {info['version']}",
        f"Theme:   {info['theme']}",
        "",
        "Icons:",
        f"  SVG:     {icons['svg']:>6,}",
        f"  PNG:     {icons['png']:>6,}",
        f"  Aliases: {icons['aliases']:>6,}",
        "",
        "Directories:",
    ]
    lines.extend(f"  {ctx:<12} {count:>6,}" for ctx, count in info["directories"].items())
    lines += [
        "",
        "Build:",
        f"  Sizes:      {', '.join(str(size) for size in info['sizes'])}",
        f"  Last build: {info['last_build'] or 'never'}",
    ]
    return lines
