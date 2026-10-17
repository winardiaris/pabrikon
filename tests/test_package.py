from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from conftest import add_svg
from pabrikon.build import build_project
from pabrikon.cli import main
from pabrikon.config import load_config, write_config
from pabrikon.errors import PabrikonError
from pabrikon.package import package_project, plan_package
from pabrikon.project import Project


def build_svg_theme(root: Path, *, alias: bool = False) -> Project:
    config_path = root / "data" / "pabrikon.toml"
    config = load_config(config_path)
    config.build.sizes = [16]
    config.build.formats = ["svg"]
    write_config(config_path, config)
    (root / "index.theme").unlink()
    add_svg(root, "apps", "firefox")
    if alias:
        (root / "data" / "aliases.toml").write_text(
            '[apps]\nbrowser = "firefox"\n',
            encoding="utf-8",
        )
    project = Project.load(root)
    build_project(project)
    return project


def test_package_requires_existing_build(project_root: Path) -> None:
    with pytest.raises(PabrikonError, match="run `pabrikon build`"):
        plan_package(Project.load(project_root))


def test_package_dry_run_does_not_write_archive(project_root: Path) -> None:
    project = build_svg_theme(project_root)

    assert main(["package", str(project_root), "--dry-run"]) == 0

    assert not (project.dist_dir / "demo-theme-0.1.0.tar.gz").exists()


def test_package_contains_theme_outputs_and_is_deterministic(project_root: Path) -> None:
    project = build_svg_theme(project_root)

    plan = package_project(project)
    first = plan.output.read_bytes()
    package_project(project)

    assert plan.output.name == "demo-theme-0.1.0.tar.gz"
    assert plan.output.read_bytes() == first
    with tarfile.open(plan.output, "r:gz") as archive:
        names = archive.getnames()
        assert "demo-theme/index.theme" in names
        assert "demo-theme/apps/scalable" in names
        assert "demo-theme/apps/scalable/firefox.svg" in names
        assert archive.extractfile("demo-theme/apps/scalable/firefox.svg").read().startswith(b"<svg")


def test_package_preserves_valid_relative_alias_links(project_root: Path) -> None:
    project = build_svg_theme(project_root, alias=True)

    plan = package_project(project)

    with tarfile.open(plan.output, "r:gz") as archive:
        alias = archive.getmember("demo-theme/apps/scalable/browser.svg")
        assert alias.issym()
        assert alias.linkname == "firefox.svg"


def test_package_rejects_incomplete_generated_outputs(project_root: Path) -> None:
    project = build_svg_theme(project_root)
    (project.build_dir / "apps" / "scalable" / "orphan.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"/>',
        encoding="utf-8",
    )

    with pytest.raises(PabrikonError, match="stale generated file"):
        plan_package(project)


def test_package_excludes_optimizer_temporary_files(project_root: Path) -> None:
    project = build_svg_theme(project_root)
    temporary = project.build_dir / "apps" / "scalable" / ".firefox.svg.tmp.svg"
    temporary.write_text("partial", encoding="utf-8")

    plan = plan_package(project)

    assert temporary not in plan.files
