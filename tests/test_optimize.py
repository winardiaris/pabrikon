from __future__ import annotations

from pathlib import Path

from conftest import add_svg
from pabrikon.cli import main
from pabrikon.project import Project
from pabrikon.optimize import optimize_project


class FakeOptimizer:
    def __init__(self, output: str | None = None) -> None:
        """Set the SVG text that the fake optimizer will write."""
        self.output = output
        self.calls: list[tuple[Path, Path]] = []

    def ensure_available(self) -> str:
        """Return a marker executable path without requiring svgcleaner."""
        return "fake-svgcleaner"

    def optimize(self, source: Path, destination: Path) -> None:
        """Write configured optimizer output to the requested temporary file."""
        self.calls.append((source, destination))
        content = self.output if self.output is not None else source.read_text(encoding="utf-8").replace(
            "<rect width=\"16\" height=\"16\"/>", "<rect/>"
        )
        destination.write_text(content, encoding="utf-8")


def test_optimize_dry_run_plans_copy_without_writing(project_root: Path, capsys) -> None:
    source = add_svg(project_root, "apps", "firefox")

    assert main(["optimize", str(project_root), "--dry-run"]) == 0

    assert "would optimize icons/apps/scalable/firefox.svg -> dist/optimized/icons/apps/scalable/firefox.svg" in capsys.readouterr().out
    assert source.exists()
    assert not (project_root / "dist" / "optimized").exists()


def test_optimize_writes_validated_copy_and_preserves_source(project_root: Path) -> None:
    source = add_svg(project_root, "apps", "firefox")
    original = source.read_bytes()
    optimizer = FakeOptimizer()

    report = optimize_project(Project.load(project_root), optimizer=optimizer)

    destination = project_root / "dist" / "optimized" / "icons" / "apps" / "scalable" / "firefox.svg"
    assert len(report.completed) == 1
    assert report.failures == []
    assert source.read_bytes() == original
    assert destination.read_text(encoding="utf-8") == (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><rect/></svg>\n'
    )
    assert optimizer.calls[0][0] == source
    assert not list(destination.parent.glob(".*.tmp.svg"))


def test_optimize_requires_in_place_flag_to_replace_source(project_root: Path) -> None:
    source = add_svg(project_root, "apps", "firefox")
    optimizer = FakeOptimizer()

    report = optimize_project(Project.load(project_root), optimizer=optimizer, in_place=True)

    assert len(report.completed) == 1
    assert source.read_text(encoding="utf-8").endswith("<rect/></svg>\n")
    assert not (project_root / "dist" / "optimized").exists()


def test_invalid_optimizer_output_does_not_replace_source(project_root: Path) -> None:
    source = add_svg(project_root, "apps", "firefox")
    original = source.read_bytes()

    report = optimize_project(
        Project.load(project_root),
        optimizer=FakeOptimizer("<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 20 20\"/>"),
        in_place=True,
    )

    assert report.completed == []
    assert report.failures == [("icons/apps/scalable/firefox.svg", "optimized output changed the SVG viewBox")]
    assert source.read_bytes() == original
    assert not list(source.parent.glob(".*.tmp.svg"))


def test_optimize_reports_missing_svgcleaner(project_root: Path, monkeypatch, capsys) -> None:
    add_svg(project_root, "apps", "firefox")
    monkeypatch.setattr("pabrikon.optimize.shutil.which", lambda executable: None)

    assert main(["optimize", str(project_root)]) == 1

    assert "svgcleaner not found" in capsys.readouterr().err
    assert not (project_root / "dist" / "optimized").exists()
