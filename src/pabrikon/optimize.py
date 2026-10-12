from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .errors import PabrikonError, ToolNotFoundError
from .project import Project
from .svg import check_svg, parse_svg

OPTIMIZE_TIMEOUT_SECONDS = 60


class OptimizeError(PabrikonError):
    pass


class SvgOptimizer(Protocol):
    def ensure_available(self) -> str:
        """Return the optimizer executable path or raise a tool availability error."""
        ...

    def optimize(self, source: Path, destination: Path) -> None:
        """Write an optimized version of the source SVG to the destination."""
        ...


class SvgCleaner:
    executable = "svgcleaner"

    def __init__(self) -> None:
        """Initialize the adapter without resolving the external binary eagerly."""
        self._path: str | None = None

    def ensure_available(self) -> str:
        """Resolve svgcleaner once, raising an actionable error when it is missing."""
        if self._path is not None:
            return self._path
        path = shutil.which(self.executable)
        if path is None:
            raise ToolNotFoundError(
                f"{self.executable} not found; it is required to optimize SVG icons",
                hint="Install svgcleaner with `cargo install svgcleaner`, then retry.",
            )
        self._path = path
        return path

    def optimize(self, source: Path, destination: Path) -> None:
        """Run svgcleaner with argument-safe paths and report tool failures."""
        command = [self.ensure_available(), str(source.absolute()), str(destination.absolute())]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=OPTIMIZE_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise OptimizeError(f"{self.executable} timed out after {OPTIMIZE_TIMEOUT_SECONDS}s") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or f"exit status {completed.returncode}"
            raise OptimizeError(f"{self.executable} failed: {detail}")


@dataclass(frozen=True)
class OptimizeTask:
    source: Path
    destination: Path
    original_size: int


@dataclass(frozen=True)
class OptimizedAsset:
    task: OptimizeTask
    optimized_size: int

    @property
    def saved(self) -> int:
        """Return the number of bytes removed by this optimization, possibly negative."""
        return self.task.original_size - self.optimized_size


@dataclass
class OptimizeReport:
    tasks: list[OptimizeTask] = field(default_factory=list)
    completed: list[OptimizedAsset] = field(default_factory=list)
    failures: list[tuple[str, str]] = field(default_factory=list)

    @property
    def bytes_saved(self) -> int:
        """Sum byte savings across successfully optimized assets."""
        return sum(asset.saved for asset in self.completed)


def _viewbox(path: Path) -> tuple[float, ...] | str | None:
    """Parse a viewBox into numeric coordinates while preserving malformed text for comparison."""
    root = parse_svg(path).getroot()
    value = root.get("viewBox")
    if value is None:
        return None
    parts = re.split(r"[\s,]+", value.strip())
    try:
        return tuple(float(part) for part in parts)
    except ValueError:
        return value


def _safe_destination(project: Project, destination: Path) -> None:
    """Reject output paths that would write through a symlink inside the project."""
    current = project.root
    for part in destination.relative_to(project.root).parts[:-1]:
        current /= part
        if current.is_symlink():
            raise PabrikonError(
                f"refusing to write through symbolic link: {current}",
                hint="Remove the link or choose a project path that does not redirect generated files.",
            )


def _plan(project: Project, in_place: bool) -> OptimizeReport:
    """Map source SVGs to optimized copies or their explicit in-place destinations."""
    report = OptimizeReport()
    for source in project.sources():
        if in_place:
            destination = source.path
        else:
            relative = source.path.relative_to(project.icons_dir)
            destination = project.dist_dir / "optimized" / "icons" / relative
        report.tasks.append(OptimizeTask(source.path, destination, source.path.stat().st_size))
    return report


def _run_task(task: OptimizeTask, optimizer: SvgOptimizer) -> int:
    """Optimize one SVG atomically and verify its validity and unchanged viewBox."""
    source_check = check_svg(task.source)
    if source_check.error:
        raise OptimizeError(source_check.error)

    task.destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{task.destination.name}.",
        suffix=".tmp.svg",
        dir=task.destination.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        optimizer.optimize(task.source, temporary)
        optimized_check = check_svg(temporary)
        if optimized_check.error:
            raise OptimizeError(f"optimized output is invalid: {optimized_check.error}")
        if _viewbox(task.source) != _viewbox(temporary):
            raise OptimizeError("optimized output changed the SVG viewBox")
        size = temporary.stat().st_size
        shutil.copymode(task.source, temporary)
        os.replace(temporary, task.destination)
        return size
    finally:
        temporary.unlink(missing_ok=True)


def optimize_project(
    project: Project,
    *,
    optimizer: SvgOptimizer | None = None,
    in_place: bool = False,
    dry_run: bool = False,
) -> OptimizeReport:
    """Plan or execute SVG optimization, preserving sources unless in-place mode is requested."""
    report = _plan(project, in_place)
    if dry_run or not report.tasks:
        return report

    optimizer = optimizer or SvgCleaner()
    optimizer.ensure_available()
    for task in report.tasks:
        try:
            _safe_destination(project, task.destination)
            optimized_size = _run_task(task, optimizer)
        except PabrikonError as exc:
            report.failures.append((task.source.relative_to(project.root).as_posix(), exc.message))
        except OSError as exc:
            report.failures.append(
                (task.source.relative_to(project.root).as_posix(), f"cannot optimize SVG: {exc.strerror or exc}")
            )
        else:
            report.completed.append(OptimizedAsset(task, optimized_size))
    return report
