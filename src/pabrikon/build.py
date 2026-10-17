from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .aliases import AliasLink, apply_alias_links, load_aliases, plan_alias_links, resolve_aliases
from .config import CONFIG_FILE, MAX_ICON_SIZE
from .errors import PabrikonError, UsageError
from .project import IconSource, Project, is_valid_icon_name
from .render import RenderError, RsvgRenderer
from .svg import check_svg
from .theme import render_index_theme, size_dir


@dataclass(frozen=True)
class BuildTask:
    source: IconSource
    output: Path
    size: int | None  # None copies the scalable SVG

    def describe(self, root: Path) -> str:
        """Format this render operation as a project-relative progress line."""
        kind = f"{self.size}x{self.size}" if self.size else "scalable"
        return f"{self.source.path.relative_to(root)} -> {self.output.relative_to(root)} ({kind})"


@dataclass
class BuildReport:
    sources: int = 0
    tasks: list[BuildTask] = field(default_factory=list)
    up_to_date: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)
    aliases: list[AliasLink] = field(default_factory=list)

    @property
    def rendered(self) -> int:
        """Count planned tasks that require raster rendering."""
        return sum(1 for task in self.tasks if task.size is not None)

    @property
    def copied(self) -> int:
        """Count planned tasks that copy scalable SVG files."""
        return sum(1 for task in self.tasks if task.size is None)


def parse_size_values(size: int | None, sizes: str | None) -> list[int]:
    """Combine size options, rejecting malformed or out-of-range values."""
    values: list[int] = []
    if size is not None:
        values.append(size)
    for item in (sizes or "").split(","):
        if item.strip():
            try:
                values.append(int(item))
            except ValueError:
                raise UsageError(f"invalid size {item.strip()!r} in --sizes", hint="Example: --sizes 16,24,32") from None
    for value in values:
        if not 1 <= value <= MAX_ICON_SIZE:
            raise UsageError(f"size {value} is out of range 1-{MAX_ICON_SIZE}")
    return sorted(set(values))


def select_sources(project: Project, directory: str | None, icon: str | None) -> list[IconSource]:
    """Select configured SVG sources matching optional context and icon filters."""
    if directory:
        project.require_directory(directory)
    sources = project.sources(directory)
    if icon:
        sources = [source for source in sources if icon in (source.name, source.key)]
        if not sources:
            where = f"icons/{directory}/scalable/" if directory else "icons/<directory>/scalable/"
            raise PabrikonError(f"icon source not found: {icon}\n\nExpected:\n    {where}{icon}.svg",
                                hint="Run `pabrikon list icons`")
    return sources


def plan_build(project: Project, sources: list[IconSource], sizes: list[int], rebuild_all: bool) -> BuildReport:
    """Plan outputs that are missing or older than their source."""
    report = BuildReport(sources=len(sources))
    formats = project.config.build.formats
    for source in sources:
        if not is_valid_icon_name(source.name):
            report.failures.append((str(source.path.relative_to(project.root)), "invalid icon file name"))
            continue
        outputs: list[tuple[Path, int | None]] = []
        if "png" in formats:
            outputs += [(project.build_dir / source.context / size_dir(size) / f"{source.name}.png", size) for size in sizes]
        if "svg" in formats:
            outputs.append((project.build_dir / source.context / "scalable" / f"{source.name}.svg", None))

        source_mtime = source.path.stat().st_mtime
        pending = [
            BuildTask(source, output, size)
            for output, size in outputs
            if rebuild_all or not output.is_file() or output.stat().st_mtime < source_mtime
        ]
        report.up_to_date += len(outputs) - len(pending)
        if not pending:
            continue
        check = check_svg(source.path)
        if check.error:
            report.failures.append((str(source.path.relative_to(project.root)), check.error))
            continue
        report.tasks.extend(pending)
    return report


def _write_atomically(destination: Path, write) -> None:
    """Write generated output to a sibling temporary file before replacing the destination."""
    """Write via a temporary file so an interrupted or failed write never leaves a corrupt output."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        write(temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def build_project(
    project: Project,
    *,
    renderer: RsvgRenderer | None = None,
    sizes: list[int] | None = None,
    directory: str | None = None,
    icon: str | None = None,
    rebuild_all: bool = False,
    dry_run: bool = False,
) -> BuildReport:
    """Build configured SVG/PNG outputs and apply validated aliases."""
    project.check_build_dir()
    if sizes:
        unknown = sorted(set(sizes) - set(project.config.build.sizes))
        if unknown:
            raise UsageError(
                f"size(s) {', '.join(map(str, unknown))} are not in build.sizes",
                hint=f"Add them to build.sizes in {CONFIG_FILE} so index.theme declares their directories.",
            )
    aliases = load_aliases(project)
    sources = select_sources(project, directory, icon)
    report = plan_build(project, sources, sizes or project.config.build.sizes, rebuild_all)
    resolved, alias_problems = resolve_aliases(project, aliases)
    report.failures += [(problem.path, problem.message) for problem in alias_problems]

    if dry_run:
        report.aliases = plan_alias_links(project, resolved)
        return report

    renderer = renderer or RsvgRenderer()
    if report.rendered:
        renderer.ensure_available()

    completed: list[BuildTask] = []
    for task in report.tasks:
        try:
            if task.size is None:
                _write_atomically(task.output, lambda tmp, src=task.source.path: shutil.copyfile(src, tmp))
            else:
                _write_atomically(task.output, lambda tmp, t=task: renderer.render(t.source.path, tmp, t.size))
        except RenderError as exc:
            report.failures.append((task.describe(project.root), exc.message))
            continue
        completed.append(task)
    report.tasks = completed

    index = project.index_theme
    metadata = index.read_text(encoding="utf-8") if index.is_file() else render_index_theme(project.config)
    project.build_dir.mkdir(exist_ok=True)
    (project.build_dir / "index.theme").write_text(metadata, encoding="utf-8")

    report.aliases = plan_alias_links(project, resolved)
    apply_alias_links(report.aliases)
    return report
