from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .aliases import load_aliases, resolve_aliases
from .config import CONFIG_FILE
from .diagnostics import ERROR, WARNING, Diagnostic, error, warning
from .project import SOURCE_SUBDIR, Project, is_valid_icon_name, walk_files
from .svg import check_svg
from .theme import size_dir, validate_index_theme

SECTIONS = ("Configuration", "Theme metadata", "Icon directories", "SVG files", "Aliases", "Generated files")


def _relative(project: Project, path: Path) -> str:
    """Format a project path for stable, platform-independent diagnostics."""
    return path.relative_to(project.root).as_posix()


def _is_inside(path: Path, root: Path) -> bool:
    """Return whether the resolved path remains within the given root."""
    return path.resolve().is_relative_to(root)


def check_icon_directories(project: Project) -> list[Diagnostic]:
    """Report missing contexts, unsafe links, disabled contexts, and misplaced source files."""
    if not project.icons_dir.is_dir():
        return [error("icons", "source directory is missing; create it or run `pabrikon init`")]

    found: list[Diagnostic] = []
    enabled = set(project.config.build.directories)
    for ctx in project.config.build.directories:
        if not project.source_dir(ctx).is_dir():
            found.append(warning(f"icons/{ctx}/{SOURCE_SUBDIR}", "enabled directory is missing"))

    for path in walk_files(project.icons_dir):
        label = _relative(project, path)
        if path.is_symlink():
            if not path.exists():
                found.append(error(label, "broken symbolic link"))
            elif not _is_inside(path, project.root):
                found.append(error(label, "symbolic link points outside the project"))
            else:
                found.append(warning(label, "symbolic links are not used as sources; declare aliases in data/aliases.toml"))
            continue
        parts = path.relative_to(project.icons_dir).parts
        if parts[0] not in enabled:
            found.append(warning(label, f"directory {parts[0]!r} is not enabled in {CONFIG_FILE}; file is ignored"))
        elif len(parts) != 3 or parts[1] != SOURCE_SUBDIR or path.suffix != ".svg":
            found.append(warning(label, f"orphaned file; sources must be icons/{parts[0]}/{SOURCE_SUBDIR}/<name>.svg"))
    return found


def check_svg_sources(project: Project) -> list[Diagnostic]:
    """Validate source SVGs and report duplicate names or missing viewBoxes."""
    found: list[Diagnostic] = []
    contexts_by_name: dict[str, list[str]] = defaultdict(list)
    for source in project.sources():
        label = _relative(project, source.path)
        contexts_by_name[source.name].append(source.context)
        if not is_valid_icon_name(source.name):
            found.append(error(label, "invalid icon name; use letters, digits, '.', '_', '+', '@' or '-'"))
            continue
        check = check_svg(source.path)
        if check.error:
            found.append(error(label, check.error))
        elif not check.has_viewbox:
            found.append(warning(label, "missing viewBox; the icon may not scale correctly"))
    for name, contexts in sorted(contexts_by_name.items()):
        if len(contexts) > 1:
            found.append(warning(name, f"duplicate icon name in directories: {', '.join(contexts)}"))
    return found


def check_generated(project: Project) -> list[Diagnostic]:
    """Report missing or stale build outputs and unsafe generated links."""
    if not project.build_dir.is_dir() or project.build_dir.is_symlink():
        return []
    found: list[Diagnostic] = []
    formats = project.config.build.formats
    expected_dirs = [size_dir(size) for size in project.config.build.sizes] if "png" in formats else []
    if "svg" in formats:
        expected_dirs.append("scalable")
    sources = project.sources()
    source_keys = {source.key for source in sources}

    for source in sources:
        missing = [
            subdir for subdir in expected_dirs
            if not (project.build_dir / source.context / subdir / f"{source.name}.{'svg' if subdir == 'scalable' else 'png'}").is_file()
        ]
        if missing:
            found.append(warning(_relative(project, source.path), f"missing generated size(s): {', '.join(missing)}; run `pabrikon build`"))

    for path in walk_files(project.build_dir):
        label = _relative(project, path)
        if path.is_symlink():
            if not path.exists():
                found.append(error(label, "broken symbolic link; run `pabrikon aliases build`"))
            elif not _is_inside(path, project.build_dir.resolve()):
                found.append(error(label, "symbolic link points outside build/"))
            continue
        parts = path.relative_to(project.build_dir).parts
        if len(parts) == 3 and f"{parts[0]}/{path.stem}" not in source_keys:
            found.append(warning(label, "stale generated file without a source; run `pabrikon clean` then `pabrikon build`"))
    return found


def validate_project(project: Project) -> dict[str, list[Diagnostic]]:
    """Run every check, grouped by section. Configuration errors are raised by ``Project.load``."""
    resolved_problems = resolve_aliases(project, load_aliases(project))[1]
    results = {
        "Configuration": [],
        "Theme metadata": validate_index_theme(project.index_theme, project.config),
        "Icon directories": check_icon_directories(project),
        "SVG files": check_svg_sources(project),
        "Aliases": resolved_problems,
        "Generated files": check_generated(project),
    }
    if project.config.validation.strict:
        results = {
            section: [Diagnostic(ERROR, item.path, item.message) if item.level == WARNING else item for item in items]
            for section, items in results.items()
        }
    return results
