from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .diagnostics import Diagnostic, error
from .errors import ConfigError, PabrikonError
from .project import Project, is_valid_icon_name, walk_files
from .theme import size_dir


@dataclass(frozen=True)
class Alias:
    context: str
    name: str
    target_context: str
    target_name: str

    @property
    def key(self) -> str:
        """Return this alias's fully qualified destination icon key."""
        return f"{self.context}/{self.name}"

    @property
    def target_key(self) -> str:
        """Return the fully qualified key of the icon this alias resolves to."""
        return f"{self.target_context}/{self.target_name}"


@dataclass(frozen=True)
class AliasLink:
    link: Path
    target: str
    action: str  # "create", "replace", "unchanged" or "remove"


def parse_aliases(data: dict, label: str = "aliases.toml") -> list[Alias]:
    """Convert TOML tables into normalized alias records, preserving source location in errors."""
    aliases: list[Alias] = []
    for context, table in data.items():
        if not isinstance(table, dict):
            raise ConfigError(f"{label}: [{context}] must be a table of alias = \"target\" entries")
        for name, target in table.items():
            if not isinstance(target, str) or not target:
                raise ConfigError(f"{label}: {context}.{name} must be a target icon name string")
            target_context, _, target_name = target.rpartition("/")
            aliases.append(Alias(context, name, target_context or context, target_name))
    return sorted(aliases, key=lambda alias: (alias.context, alias.name))


def load_aliases(project: Project) -> list[Alias]:
    """Read and parse the optional alias file for a project."""
    path = project.aliases_file
    if not path.is_file():
        return []
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path.relative_to(project.root)} is not valid TOML: {exc}") from exc
    return parse_aliases(data, str(path.relative_to(project.root)))


def resolve_aliases(project: Project, aliases: list[Alias]) -> tuple[dict[str, str], list[Diagnostic]]:
    """Resolve each alias through alias chains to a real source icon.

    Returns ``{alias key: source icon key}`` for valid aliases and the problems
    found for the rest.
    """
    label = str(project.aliases_file.relative_to(project.root))
    directories = set(project.config.build.directories)
    sources = {source.key for source in project.sources()}
    by_key = {alias.key: alias for alias in aliases}
    resolved: dict[str, str] = {}
    problems: list[Diagnostic] = []

    for alias in aliases:
        if alias.context not in directories or alias.target_context not in directories:
            problems.append(error(label, f"{alias.key} -> {alias.target_key}: directory is not enabled in pabrikon.toml"))
            continue
        if not is_valid_icon_name(alias.name) or not is_valid_icon_name(alias.target_name):
            problems.append(error(label, f"{alias.key} -> {alias.target_key}: invalid icon name"))
            continue
        if alias.key in sources:
            problems.append(error(label, f"{alias.key} would replace the real icon {alias.key}.svg"))
            continue

        chain = [alias.key]
        current = alias.target_key
        while current in by_key and current not in chain:
            chain.append(current)
            current = by_key[current].target_key
        if current in chain:
            problems.append(error(label, f"alias cycle: {' -> '.join(chain + [current])}"))
        elif current not in sources:
            problems.append(error(label, f"{alias.key} -> {alias.target_key}: target icon {current} does not exist"))
        else:
            resolved[alias.key] = current
    return resolved, problems


def plan_alias_links(project: Project, resolved: dict[str, str]) -> list[AliasLink]:
    """Plan symlinks in build/ for every built size of each alias target.

    Links are relative so the theme stays valid after it is moved or packaged.
    Stale symbolic links in build/ are removed; regular files are never touched.
    """
    build_dir = project.build_dir
    subdirs = [size_dir(size) for size in project.config.build.sizes] if "png" in project.config.build.formats else []
    if "svg" in project.config.build.formats:
        subdirs.append("scalable")

    wanted: dict[Path, str] = {}
    for alias_key, source_key in sorted(resolved.items()):
        context, name = alias_key.split("/")
        target_context, target_name = source_key.split("/")
        for subdir in subdirs:
            extension = "svg" if subdir == "scalable" else "png"
            target_file = build_dir / target_context / subdir / f"{target_name}.{extension}"
            if not target_file.is_file():
                continue
            if target_context == context:
                relative = f"{target_name}.{extension}"
            else:
                relative = f"../../{target_context}/{subdir}/{target_name}.{extension}"
            wanted[build_dir / context / subdir / f"{name}.{extension}"] = relative

    links: list[AliasLink] = []
    for link, target in wanted.items():
        if link.is_symlink():
            action = "unchanged" if os.readlink(link) == target else "replace"
        elif link.exists():
            raise PabrikonError(
                f"cannot create alias {link.relative_to(project.root)}: a regular file already exists there",
                hint="Remove the alias or rename the icon so names do not collide.",
            )
        else:
            action = "create"
        links.append(AliasLink(link, target, action))

    if build_dir.is_dir():
        for path in walk_files(build_dir):
            if path.is_symlink() and path not in wanted:
                links.append(AliasLink(path, os.readlink(path), "remove"))
    return links


def apply_alias_links(links: list[AliasLink]) -> None:
    """Apply planned alias changes, replacing only links owned by the alias plan."""
    for item in links:
        if item.action in ("replace", "remove"):
            item.link.unlink()
        if item.action in ("create", "replace"):
            item.link.parent.mkdir(parents=True, exist_ok=True)
            item.link.symlink_to(item.target)
