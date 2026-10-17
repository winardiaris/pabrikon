from __future__ import annotations

import configparser
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from .config import CONFIG_FILE, DEFAULT_DIRECTORIES, ProjectConfig, is_valid_name, render_config, write_config
from .errors import PabrikonError
from .project import is_valid_icon_name

SIZE_DIRECTORY = re.compile(r"^(\d+)(?:x\1)?(?:@([23])x)?$")
IGNORED_DIRECTORY_NAMES = {".git", ".hg", ".svn", ".venv", "build", "dist", "node_modules"}
ICON_SUFFIXES = {".svg", ".png", ".xpm", ".webp"}
THEME_CONTEXTS = {
    "Actions": "actions",
    "Animations": "animations",
    "Applications": "apps",
    "Categories": "categories",
    "Devices": "devices",
    "Emblems": "emblems",
    "Emotes": "emotes",
    "MimeTypes": "mimetypes",
    "Places": "places",
    "Status": "status",
    "Stock": "stock",
}


@dataclass(frozen=True)
class AssetCopy:
    source: Path
    destination: Path


@dataclass(frozen=True)
class AliasProposal:
    context: str
    name: str
    target: str


@dataclass(frozen=True)
class IconCollision:
    first_source: str
    second_source: str
    destination: str


@dataclass(frozen=True)
class AdoptionPlan:
    repository: Path
    theme_root: Path
    config: ProjectConfig
    copies: tuple[AssetCopy, ...]
    collisions: tuple[IconCollision, ...]
    directories: tuple[Path, ...]
    ignored: tuple[str, ...]
    aliases: tuple[AliasProposal, ...]
    skipped_links: tuple[tuple[str, str], ...]
    aliases_file_conflict: bool
    alternate_metadata: tuple[str, ...]
    license_files: tuple[str, ...]
    submodules: tuple[str, ...]
    config_backup: Path | None

    @property
    def config_path(self) -> Path:
        """Return the destination path of the generated project config."""
        return self.theme_root / CONFIG_FILE

    @property
    def aliases_path(self) -> Path:
        """Return the destination path for imported symbolic-link aliases."""
        return self.theme_root / "data" / "aliases.toml"

    def render_aliases(self) -> str:
        """Render proposed aliases using Pabrikon's context-table TOML format."""
        tables: dict[str, list[AliasProposal]] = {}
        for alias in self.aliases:
            tables.setdefault(alias.context, []).append(alias)
        chunks = []
        for context, aliases in sorted(tables.items()):
            chunks.append(f"[{context}]\n")
            for alias in sorted(aliases, key=lambda item: item.name):
                chunks.append(f'"{alias.name}" = "{alias.target}"\n')
            chunks.append("\n")
        return "".join(chunks)

    def to_dict(self, *, dry_run: bool) -> dict[str, object]:
        """Serialize the adoption plan for JSON output and automation."""
        config_text = render_config(self.config)
        return {
            "command": "init",
            "mode": "adopt",
            "ok": True,
            "dry_run": dry_run,
            "repository": str(self.repository),
            "theme_root": str(self.theme_root),
            "config_path": self.config_path.relative_to(self.repository).as_posix(),
            "config": config_text,
            "contexts": self.config.build.directories,
            "directories": [path.relative_to(self.theme_root).as_posix() for path in self.directories],
            "copies": [
                {
                    "source": item.source.relative_to(self.repository).as_posix(),
                    "destination": item.destination.relative_to(self.theme_root).as_posix(),
                }
                for item in self.copies
            ],
            "collisions": [
                {
                    "sources": [item.first_source, item.second_source],
                    "destination": item.destination,
                }
                for item in self.collisions
            ],
            "aliases_path": self.aliases_path.relative_to(self.repository).as_posix(),
            "aliases": [
                {"context": item.context, "name": item.name, "target": item.target}
                for item in self.aliases
            ],
            "aliases_toml": self.render_aliases(),
            "aliases_file_conflict": self.aliases_file_conflict,
            "skipped_links": [{"path": path, "reason": reason} for path, reason in self.skipped_links],
            "ignored": list(self.ignored),
            "alternate_metadata": list(self.alternate_metadata),
            "license_files": list(self.license_files),
            "submodules": list(self.submodules),
            "config_backup": self.config_backup.relative_to(self.theme_root).as_posix()
            if self.config_backup
            else None,
        }


def _safe_walk(root: Path) -> tuple[list[Path], list[str]]:
    """Walk a checkout without entering VCS metadata, symlink trees, or submodules."""
    files: list[Path] = []
    skipped: list[str] = []
    for current, dirs, filenames in os.walk(root, followlinks=False):
        base = Path(current)
        kept_dirs: list[str] = []
        for name in sorted(dirs):
            path = base / name
            if name in IGNORED_DIRECTORY_NAMES:
                continue
            if path.is_symlink():
                skipped.append(path.relative_to(root).as_posix())
                continue
            if (path / ".git").exists():
                skipped.append(path.relative_to(root).as_posix())
                continue
            kept_dirs.append(name)
        dirs[:] = kept_dirs
        files.extend(base / name for name in filenames)
    return sorted(files), skipped


def _candidate_roots(repository: Path, files: list[Path]) -> list[Path]:
    """Find directories containing a regular index.theme file."""
    candidates = []
    for path in files:
        if path.name == "index.theme" and not path.is_symlink() and path.is_file():
            candidates.append(path.parent)
    return sorted(set(candidates), key=lambda path: path.relative_to(repository).as_posix())


def _select_theme_root(repository: Path, candidates: list[Path], requested: str | None) -> Path:
    """Choose the sole theme root or resolve an explicit repository-relative choice."""
    if requested:
        requested_path = Path(requested)
        if requested_path.is_absolute():
            raise PabrikonError("--theme-root must be relative to the repository directory")
        selected = (repository / requested_path).resolve()
        if selected not in candidates:
            available = ", ".join(path.relative_to(repository).as_posix() or "." for path in candidates)
            raise PabrikonError(
                f"theme root {requested!r} does not contain index.theme",
                hint=f"Choose one of the detected roots: {available or '(none found)'}.",
            )
        return selected
    if not candidates:
        raise PabrikonError(
            f"no icon-theme root containing index.theme found under {repository}",
            hint="Pass a directory containing index.theme or inspect the checkout manually.",
        )
    if len(candidates) > 1:
        available = ", ".join(path.relative_to(repository).as_posix() or "." for path in candidates)
        raise PabrikonError(
            "multiple icon-theme roots found",
            hint=f"Choose one with --theme-root: {available}.",
        )
    return candidates[0]


def _read_theme_metadata(path: Path) -> tuple[str | None, str | None, list[str], dict[str, tuple[str, str, int, int]]]:
    """Read theme metadata and context/type/size for each declared icon directory."""
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        with path.open(encoding="utf-8") as source:
            parser.read_file(source)
    except (OSError, UnicodeError, configparser.Error) as exc:
        raise PabrikonError(f"cannot read theme metadata {path}: {exc}") from exc
    section = parser["Icon Theme"] if parser.has_section("Icon Theme") else None
    if section is None:
        raise PabrikonError(f"{path} does not contain an [Icon Theme] section")
    name = section.get("Name")
    comment = section.get("Comment")
    inherits = [value.strip() for value in section.get("Inherits", "").split(",") if value.strip()]
    theme_directories: dict[str, tuple[str, str, int, int]] = {}
    directory_names = section.get("Directories", "").split(",")
    directory_names.extend(section.get("ScaledDirectories", "").split(","))
    for directory in directory_names:
        directory = directory.strip()
        relative_directory = PurePosixPath(directory)
        if (
            not directory
            or relative_directory.is_absolute()
            or any(part in {".", ".."} for part in relative_directory.parts)
            or not parser.has_section(directory)
        ):
            continue
        context = THEME_CONTEXTS.get(parser.get(directory, "Context", fallback=""))
        directory_type = parser.get(directory, "Type", fallback="")
        try:
            size = parser.get(directory, "Size", fallback="")
            parsed_size = int(size)
        except ValueError:
            continue
        inferred_scale = re.search(r"@(\d+)x$", directory)
        try:
            parsed_scale = int(parser.get(directory, "Scale", fallback=inferred_scale.group(1) if inferred_scale else "1"))
        except ValueError:
            continue
        if context and parsed_size > 0 and parsed_scale > 0 and directory_type in {"Fixed", "Scalable", "Threshold"}:
            theme_directories[directory] = (context, directory_type, parsed_size, parsed_scale)
    return name, comment, inherits, theme_directories


def _context_for_path(
    relative: Path,
    contexts: set[str],
    theme_directories: dict[str, tuple[str, str, int, int]],
) -> tuple[str | None, str | None, str | None, int | None, int | None]:
    """Match a source's parent to a declared theme directory or recognizable layout."""
    parent = relative.parent.as_posix()
    for directory, (context, directory_type, size, scale) in sorted(
        theme_directories.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if parent == directory or parent.endswith(f"/{directory}"):
            return context, directory, directory_type, size, scale
    if any(parent.startswith(f"{directory}/") for directory in theme_directories):
        return None, None, None, None, None
    parts = relative.parts[:-1]
    for part in parts:
        if part not in contexts:
            continue
        directory = Path(*parts).as_posix()
        if "scalable" in parts:
            return part, directory, "Scalable", 16, 1
        size_match = next(
            (match for item in parts if (match := SIZE_DIRECTORY.fullmatch(item))),
            None,
        )
        if size_match:
            return part, directory, "Fixed", int(size_match.group(1)), int(size_match.group(2) or 1)
    return None, None, None, None, None


def _submodule_paths(repository: Path) -> list[str]:
    """Read declared submodule paths without initializing or contacting them."""
    config_path = repository / ".gitmodules"
    if not config_path.is_file() or config_path.is_symlink():
        return []
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read(config_path, encoding="utf-8")
    except (OSError, configparser.Error):
        return [".gitmodules (could not parse; not initialized)"]
    paths = [
        parser.get(section, "path", fallback="")
        for section in parser.sections()
        if section.startswith("submodule ")
    ]
    return sorted(path for path in paths if path)


def _reject_symlink_parents(root: Path, path: Path) -> None:
    """Refuse adoption writes whose existing parent path redirects through a symlink."""
    current = root
    for component in path.relative_to(root).parts[:-1]:
        current = current / component
        if current.is_symlink():
            raise PabrikonError(f"refusing to write through symbolic-link directory: {current}")


def analyze_adoption(
    repository: Path,
    *,
    theme_root: str | None = None,
    name: str | None = None,
    regenerate_config: bool = False,
) -> AdoptionPlan:
    """Inspect a local checkout and prepare a non-destructive v2 adoption plan."""
    if repository.is_symlink():
        raise PabrikonError(f"refusing to adopt a symbolic-link checkout: {repository}")
    root = repository.resolve()
    if not root.is_dir():
        raise PabrikonError(f"repository directory not found: {root}")

    files, skipped = _safe_walk(root)
    candidates = _candidate_roots(root, files)
    selected_root = _select_theme_root(root, candidates, theme_root)
    display_name, comment, inherits, theme_directories = _read_theme_metadata(selected_root / "index.theme")

    project_name = name or selected_root.name
    project_name = re.sub(r"[^A-Za-z0-9._-]+", "-", project_name).strip(".-_") or "icon-theme"
    if not is_valid_name(project_name):
        raise PabrikonError(f"could not derive a valid project name from {project_name!r}")
    config = ProjectConfig.default(project_name)
    config.license = "UNKNOWN"
    if display_name:
        config.theme.name = display_name.strip()
    if comment:
        config.theme.comment = comment.strip()
        config.description = comment.strip()
    config.theme.inherits = inherits or config.theme.inherits

    context_names = set(DEFAULT_DIRECTORIES)
    candidate_assets = [path for path in files if path.suffix.lower() in ICON_SUFFIXES]
    contexts: set[str] = set()
    copies: dict[Path, Path] = {}
    sources_by_destination: dict[Path, Path] = {}
    ambiguous_destinations: dict[Path, Path] = {}
    collisions: list[IconCollision] = []
    ignored = [*skipped]
    adopted_sources: set[Path] = set()
    symlink_assets: list[tuple[Path, str]] = []
    canonical_sources: dict[Path, tuple[str, str]] = {}
    source_sizes = {
        size
        for _, directory_type, size, scale in theme_directories.values()
        if directory_type != "Scalable"
    }
    for source in candidate_assets:
        if not source.is_relative_to(selected_root):
            continue
        relative = source.relative_to(selected_root)
        context, source_directory, directory_type, size, scale = _context_for_path(relative, context_names, theme_directories)
        if context is None or source_directory is None or directory_type is None or size is None or scale is None:
            continue
        contexts.add(context)
        if source.suffix.lower() != ".svg":
            continue
        if source.is_symlink():
            symlink_assets.append((source, context))
            continue
        if not source.is_file():
            continue
        if not is_valid_icon_name(source.stem):
            continue
        destination = selected_root / "icons" / source_directory / f"{source.stem}.svg"
        previous_source = sources_by_destination.get(destination)
        if destination in ambiguous_destinations:
            first_source = ambiguous_destinations[destination]
            collisions.append(
                IconCollision(
                    first_source.relative_to(root).as_posix(),
                    source.relative_to(root).as_posix(),
                    destination.relative_to(selected_root).as_posix(),
                )
            )
            canonical_sources.pop(source.resolve(), None)
            continue
        if previous_source is not None and previous_source != source:
            copies.pop(destination, None)
            adopted_sources.discard(previous_source)
            ambiguous_destinations[destination] = previous_source
            canonical_sources.pop(previous_source.resolve(), None)
            canonical_sources.pop(source.resolve(), None)
            collisions.append(
                IconCollision(
                    previous_source.relative_to(root).as_posix(),
                    source.relative_to(root).as_posix(),
                    destination.relative_to(selected_root).as_posix(),
                )
            )
            continue
        sources_by_destination[destination] = source
        canonical_sources[source.resolve()] = (context, source.stem)
        _reject_symlink_parents(selected_root, destination)
        temporary_destination = destination.with_name(destination.name + ".pabrikon-tmp")
        if temporary_destination.exists() or temporary_destination.is_symlink():
            raise PabrikonError(f"temporary adoption path already exists: {temporary_destination}")
        if source.resolve() == destination.resolve(strict=False):
            adopted_sources.add(source)
            continue
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink() or not destination.is_file():
                raise PabrikonError(f"unsafe adoption destination: {destination}")
            if destination.read_bytes() != source.read_bytes():
                raise PabrikonError(
                    f"adoption would overwrite a different file: {destination.relative_to(selected_root)}"
                )
            adopted_sources.add(source)
            continue
        copies[destination] = source
        adopted_sources.add(source)

    skipped_links: list[tuple[str, str]] = []
    for skipped_path in skipped:
        absolute = root / skipped_path
        if absolute.is_relative_to(selected_root):
            skipped_links.append((skipped_path, "symbolic-link directories are not traversed"))

    aliases_by_key: dict[tuple[str, str], AliasProposal] = {}
    conflicted_aliases: set[tuple[str, str]] = set()
    canonical_keys = set(canonical_sources.values())
    for source, context in symlink_assets:
        display_path = source.relative_to(root).as_posix()
        if not is_valid_icon_name(source.stem):
            skipped_links.append((display_path, "invalid alias icon name"))
            continue
        if (context, source.stem) in canonical_keys:
            skipped_links.append((display_path, "alias name collides with a canonical icon"))
            continue
        try:
            resolved_target = source.resolve(strict=True)
        except (OSError, RuntimeError):
            skipped_links.append((display_path, "broken or cyclic symbolic-link target"))
            continue
        if not resolved_target.is_relative_to(selected_root):
            skipped_links.append((display_path, "target escapes the selected theme root"))
            continue
        if not resolved_target.is_file() or resolved_target.suffix.lower() != ".svg":
            skipped_links.append((display_path, "target is not a regular SVG icon"))
            continue
        target_key = canonical_sources.get(resolved_target)
        if target_key is None:
            skipped_links.append((display_path, "target is not a recognized adopted scalable icon"))
            continue
        target_context, target_name = target_key
        target = target_name if target_context == context else f"{target_context}/{target_name}"
        key = (context, source.stem)
        proposal = AliasProposal(context, source.stem, target)
        previous = aliases_by_key.get(key)
        if previous and previous != proposal:
            aliases_by_key.pop(key)
            conflicted_aliases.add(key)
            skipped_links.append((display_path, "alias name maps to multiple target icons"))
            continue
        if key in conflicted_aliases:
            skipped_links.append((display_path, "alias name maps to multiple target icons"))
            continue
        aliases_by_key[key] = proposal

    aliases = tuple(sorted(aliases_by_key.values(), key=lambda item: (item.context, item.name)))
    accepted_keys = set(aliases_by_key)
    adopted_sources.update(
        source for source, context in symlink_assets if (context, source.stem) in accepted_keys
    )

    if not contexts:
        raise PabrikonError(
            f"no recognizable icon context directories found under {selected_root}",
            hint="Expected scalable assets under a known context such as apps/scalable/ or scalable/apps/.",
        )
    config.build.directories = [context for context in DEFAULT_DIRECTORIES if context in contexts]
    config.build.sizes = sorted(set(config.build.sizes) | source_sizes)
    ignored.extend(
        path.relative_to(root).as_posix()
        for path in files
        if path.is_relative_to(selected_root)
        and path not in adopted_sources
        and path.name != "index.theme"
    )

    config_path = selected_root / CONFIG_FILE
    _reject_symlink_parents(selected_root, config_path)
    backup: Path | None = None
    if config_path.exists() or config_path.is_symlink():
        if config_path.is_symlink() or not config_path.is_file():
            raise PabrikonError(f"refusing to replace unsafe configuration path: {config_path}")
        if not regenerate_config:
            raise PabrikonError(
                f"configuration already exists: {config_path}",
                hint="Use --regenerate-config to replace it and keep a .bak copy.",
            )
        backup = config_path.with_name(config_path.name + ".bak")
        if backup.exists() or backup.is_symlink():
            raise PabrikonError(f"configuration backup already exists: {backup}")

    alternate_metadata = [
        path.relative_to(selected_root).as_posix()
        for path in files
        if path.parent == selected_root and path.name.startswith("index.theme_")
    ]
    license_files = [
        path.relative_to(root).as_posix()
        for path in files
        if path.parent in {root, selected_root}
        and path.name.lower().startswith(("license", "copying", "copyright"))
    ]
    destination_dirs = tuple(
        [selected_root / "data"]
        + sorted({destination.parent for destination in copies})
    )
    aliases_path = selected_root / "data" / "aliases.toml"
    aliases_file_conflict = bool(aliases and (aliases_path.exists() or aliases_path.is_symlink()))
    temporary_aliases = aliases_path.with_name(aliases_path.name + ".tmp")
    if aliases and not aliases_file_conflict and (temporary_aliases.exists() or temporary_aliases.is_symlink()):
        raise PabrikonError(f"temporary alias configuration path already exists: {temporary_aliases}")
    for directory in destination_dirs:
        _reject_symlink_parents(selected_root, directory / "placeholder")
    temporary_config = config_path.with_name(config_path.name + ".tmp")
    if temporary_config.exists() or temporary_config.is_symlink():
        raise PabrikonError(f"temporary configuration path already exists: {temporary_config}")

    return AdoptionPlan(
        repository=root,
        theme_root=selected_root,
        config=config,
        copies=tuple(AssetCopy(source, destination) for destination, source in sorted(copies.items())),
        collisions=tuple(sorted(collisions, key=lambda item: (item.destination, item.first_source, item.second_source))),
        directories=destination_dirs,
        ignored=tuple(sorted(set(ignored))),
        aliases=aliases,
        skipped_links=tuple(sorted(skipped_links)),
        aliases_file_conflict=aliases_file_conflict,
        alternate_metadata=tuple(sorted(alternate_metadata)),
        license_files=tuple(sorted(license_files)),
        submodules=tuple(_submodule_paths(root)),
        config_backup=backup,
    )


def apply_adoption(plan: AdoptionPlan) -> list[str]:
    """Copy recognized SVGs and write config, rolling back newly copied files on failure."""
    created: list[Path] = []
    created_dirs: list[Path] = []
    temporary_destinations: list[Path] = []
    temporary_config = plan.config_path.with_name(plan.config_path.name + ".tmp")
    temporary_aliases = plan.aliases_path.with_name(plan.aliases_path.name + ".tmp")
    config_replaced = False
    try:
        _reject_symlink_parents(plan.theme_root, plan.config_path)
        if temporary_config.exists() or temporary_config.is_symlink():
            raise PabrikonError(f"temporary configuration path already exists: {temporary_config}")
        if plan.aliases and not plan.aliases_file_conflict:
            _reject_symlink_parents(plan.theme_root, plan.aliases_path)
            if plan.aliases_path.exists() or plan.aliases_path.is_symlink():
                raise PabrikonError(f"alias configuration was created after preview: {plan.aliases_path}")
            if temporary_aliases.exists() or temporary_aliases.is_symlink():
                raise PabrikonError(f"temporary alias configuration path already exists: {temporary_aliases}")
        if plan.config_backup:
            if plan.config_path.is_symlink() or not plan.config_path.is_file():
                raise PabrikonError(f"configuration changed after preview: {plan.config_path}")
            if plan.config_backup.exists() or plan.config_backup.is_symlink():
                raise PabrikonError(f"configuration backup already exists: {plan.config_backup}")
        elif plan.config_path.exists() or plan.config_path.is_symlink():
            raise PabrikonError(f"configuration was created after preview: {plan.config_path}")

        for directory in plan.directories:
            _reject_symlink_parents(plan.theme_root, directory / "placeholder")
            missing: list[Path] = []
            current = directory
            while current != plan.theme_root and not current.exists():
                missing.append(current)
                current = current.parent
            directory.mkdir(parents=True, exist_ok=True)
            created_dirs.extend(reversed(missing))

        for item in plan.copies:
            _reject_symlink_parents(plan.theme_root, item.destination)
            if item.source.is_symlink() or not item.source.is_file():
                raise PabrikonError(f"source changed or became unsafe during adoption: {item.source}")
            temporary_destination = item.destination.with_name(item.destination.name + ".pabrikon-tmp")
            if temporary_destination.exists() or temporary_destination.is_symlink():
                raise PabrikonError(f"temporary adoption path already exists: {temporary_destination}")
            if item.destination.exists() or item.destination.is_symlink():
                if item.destination.is_symlink() or not item.destination.is_file():
                    raise PabrikonError(f"unsafe adoption destination: {item.destination}")
                if item.destination.read_bytes() == item.source.read_bytes():
                    continue
                raise PabrikonError(f"adoption destination changed during operation: {item.destination}")
            temporary_destinations.append(temporary_destination)
            shutil.copy2(item.source, temporary_destination)
            temporary_destination.replace(item.destination)
            temporary_destinations.remove(temporary_destination)
            created.append(item.destination)

        if plan.aliases and not plan.aliases_file_conflict:
            temporary_aliases.write_text(plan.render_aliases(), encoding="utf-8")
            temporary_aliases.replace(plan.aliases_path)
            created.append(plan.aliases_path)

        if plan.config_backup:
            shutil.copy2(plan.config_path, plan.config_backup)
        write_config(temporary_config, plan.config)
        temporary_config.replace(plan.config_path)
        config_replaced = True
        created.append(plan.config_path)
        return [path.relative_to(plan.theme_root).as_posix() for path in created]
    except (OSError, PabrikonError):
        temporary_config.unlink(missing_ok=True)
        temporary_aliases.unlink(missing_ok=True)
        for path in temporary_destinations:
            path.unlink(missing_ok=True)
        for path in reversed(created):
            path.unlink(missing_ok=True)
        if config_replaced and plan.config_backup and plan.config_backup.exists():
            plan.config_backup.replace(plan.config_path)
        for path in reversed(created_dirs):
            try:
                path.rmdir()
            except OSError:
                pass
        if plan.config_backup and not config_replaced:
            plan.config_backup.unlink(missing_ok=True)
        raise


def clone_repository(url: str, target: Path, ref: str | None = None) -> Path:
    """Clone an explicitly supplied Git URL without initializing its submodules."""
    if not is_git_url(url):
        raise PabrikonError("remote adoption requires an HTTPS, SSH, or Git URL")
    if target.exists() or target.is_symlink():
        git_config = target / ".git" / "config"
        parser = configparser.ConfigParser(interpolation=None)
        try:
            if target.is_symlink() or not git_config.is_file() or git_config.is_symlink():
                raise PabrikonError(f"clone target already exists and is not a matching checkout: {target}")
            parser.read(git_config, encoding="utf-8")
        except (OSError, configparser.Error) as exc:
            raise PabrikonError(f"cannot verify existing clone at {target}: {exc}") from exc
        if parser.get('remote "origin"', "url", fallback=None) != url:
            raise PabrikonError(f"clone target already exists and has a different origin: {target}")
        return target.resolve()
    if not shutil.which("git"):
        raise PabrikonError("git was not found", hint="Install Git to adopt a remote repository.")
    command = ["git", "-c", "core.hooksPath=/dev/null", "clone", "--no-recurse-submodules", "--depth", "1"]
    if ref:
        command.extend(["--branch", ref])
    command.extend(["--", url, str(target)])
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_LFS_SKIP_SMUDGE": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    result = subprocess.run(command, capture_output=True, text=True, check=False, env=environment)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"git exited with status {result.returncode}"
        raise PabrikonError(f"could not clone {url}: {detail}")
    return target.resolve()


def is_git_url(value: str) -> bool:
    """Return whether a source string uses an explicitly supported Git URL form."""
    parsed = urlsplit(value)
    return parsed.scheme in {"https", "ssh", "git"} or re.fullmatch(
        r"[A-Za-z0-9._-]+@[A-Za-z0-9.-]+:.+", value
    ) is not None
