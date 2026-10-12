from __future__ import annotations

import gzip
import os
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from .aliases import load_aliases, plan_alias_links, resolve_aliases
from .diagnostics import ERROR
from .errors import PabrikonError
from .project import Project, walk_files
from .theme import theme_directories, validate_index_theme
from .validate import validate_project


@dataclass(frozen=True)
class PackagePlan:
    output: Path
    files: list[Path]
    directories: list[str]


def _is_temporary(path: Path) -> bool:
    """Identify transient files that must not be included in a theme archive."""
    return path.name.startswith(".") and ".tmp" in path.name


def _is_temporary_diagnostic(path: str) -> bool:
    """Identify validation messages caused only by excluded temporary outputs."""
    return _is_temporary(Path(path))


def _package_errors(project: Project) -> list[str]:
    """Collect build, metadata, and alias problems that make packaging unsafe."""
    sections = validate_project(project)
    errors = [
        f"{item.path}: {item.message}"
        for items in sections.values()
        for item in items
        if item.level == ERROR and not _is_temporary_diagnostic(item.path)
    ]
    errors.extend(
        f"{item.path}: {item.message}"
        for item in sections["Generated files"]
        if item.level != ERROR and not _is_temporary_diagnostic(item.path)
    )
    output_theme = project.build_dir / "index.theme"
    errors.extend(
        f"{item.path}: {item.message}"
        for item in validate_index_theme(output_theme, project.config)
        if item.level == ERROR
    )
    resolved, alias_problems = resolve_aliases(project, load_aliases(project))
    errors.extend(f"{item.path}: {item.message}" for item in alias_problems)
    links = plan_alias_links(project, resolved)
    if any(item.action != "unchanged" for item in links):
        errors.append("build/: alias links are out of date; run `pabrikon build`")
    return errors


def plan_package(project: Project) -> PackagePlan:
    """Validate generated output and create a deterministic archive-content plan."""
    project.check_build_dir()
    if not project.build_dir.is_dir():
        raise PabrikonError("build/ does not exist; run `pabrikon build` before packaging")
    if not (project.build_dir / "index.theme").is_file():
        raise PabrikonError("build/index.theme is missing; run `pabrikon build` before packaging")

    errors = _package_errors(project)
    if errors:
        raise PabrikonError("project outputs are not ready to package:\n" + "\n".join(f"- {item}" for item in errors))

    if project.dist_dir.is_symlink():
        raise PabrikonError(
            f"{project.dist_dir} is a symbolic link; refusing to write a package through it",
            hint="Remove the link or use a project with a regular dist/ directory.",
        )

    version = quote(project.config.version, safe=".-_")
    output = project.dist_dir / f"{project.config.name}-{version}.tar.gz"
    files = [path for path in walk_files(project.build_dir) if not _is_temporary(path)]
    relative_dirs: set[str] = set()
    for directory in theme_directories(project.config):
        current = Path(directory)
        while current.parts:
            relative_dirs.add(current.as_posix())
            current = current.parent
    for path in files:
        parent = path.relative_to(project.build_dir).parent
        while parent.parts:
            relative_dirs.add(parent.as_posix())
            parent = parent.parent
    return PackagePlan(output, files, sorted(relative_dirs))


def _tar_info(name: str, *, directory: bool = False, symlink: str | None = None, size: int = 0) -> tarfile.TarInfo:
    """Create normalized tar metadata with stable timestamps and permissions."""
    info = tarfile.TarInfo(name)
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.pax_headers = {}
    if directory:
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
    elif symlink is not None:
        info.type = tarfile.SYMTYPE
        info.mode = 0o777
        info.linkname = symlink
    else:
        info.type = tarfile.REGTYPE
        info.mode = 0o644
        info.size = size
    return info


def _add_to_archive(archive: tarfile.TarFile, project: Project, plan: PackagePlan) -> None:
    """Write planned files and safe relative symlinks into the archive."""
    prefix = project.config.name
    for directory in plan.directories:
        archive.addfile(_tar_info(f"{prefix}/{directory}/", directory=True))
    for path in plan.files:
        relative = path.relative_to(project.build_dir).as_posix()
        name = f"{prefix}/{relative}"
        if path.is_symlink():
            target = os.readlink(path)
            if os.path.isabs(target) or not path.resolve().is_relative_to(project.build_dir.resolve()):
                raise PabrikonError(f"unsafe generated symbolic link: {relative} -> {target}")
            archive.addfile(_tar_info(name, symlink=target))
        else:
            with path.open("rb") as source:
                archive.addfile(_tar_info(name, size=path.stat().st_size), source)


def package_project(project: Project, *, dry_run: bool = False) -> PackagePlan:
    """Create a deterministic theme archive, or return its validated plan in dry-run mode."""
    plan = plan_package(project)
    if dry_run:
        return plan

    project.dist_dir.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{plan.output.name}.",
        suffix=".tmp",
        dir=project.dist_dir,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with temporary.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                    _add_to_archive(archive, project, plan)
        temporary.chmod(0o644)
        os.replace(temporary, plan.output)
    finally:
        temporary.unlink(missing_ok=True)
    return plan
