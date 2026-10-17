from pathlib import Path

import pytest

from conftest import FakeRenderer, add_svg
from pabrikon.cli import main


@pytest.fixture
def built_project(project_root: Path, fake_renderer: FakeRenderer) -> Path:
    add_svg(project_root, "places", "user-home")
    (project_root / "data" / "aliases.toml").write_text('[places]\nfolder-home = "user-home"\n', encoding="utf-8")
    (project_root / "notes.txt").write_text("keep\n", encoding="utf-8")
    assert main(["build", str(project_root), "--size", "16"]) == 0
    return project_root


def project_files(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() or path.is_symlink()}


def test_clean_removes_build_and_preserves_sources(built_project: Path) -> None:
    before = {path for path in project_files(built_project) if not path.startswith("build/")}

    assert main(["clean", str(built_project)]) == 0

    assert not (built_project / "build").exists()
    assert project_files(built_project) == before
    assert (built_project / "icons" / "places" / "scalable" / "user-home.svg").is_file()
    assert (built_project / "notes.txt").read_text(encoding="utf-8") == "keep\n"


def test_clean_dry_run_lists_without_deleting(built_project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    before = project_files(built_project)

    assert main(["clean", str(built_project), "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "would remove build/places/16x16/user-home.png" in out
    assert "icons/" not in out
    assert project_files(built_project) == before


def test_clean_png_keeps_svg_copies(built_project: Path) -> None:
    assert main(["clean", str(built_project), "--type", "png"]) == 0

    build = built_project / "build" / "places"
    assert not (build / "16x16" / "user-home.png").exists()
    assert not (build / "16x16" / "folder-home.png").is_symlink()
    assert (build / "scalable" / "user-home.svg").is_file()
    assert (build / "scalable" / "folder-home.svg").is_symlink()


def test_clean_symlink_removes_only_links(built_project: Path) -> None:
    assert main(["clean", str(built_project), "--type", "symlink"]) == 0

    assert not list((built_project / "build").rglob("folder-home*"))
    assert (built_project / "build" / "places" / "16x16" / "user-home.png").is_file()


def test_clean_with_nothing_built(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["clean", str(project_root)]) == 0
    assert "Nothing to clean" in capsys.readouterr().out


def test_clean_refuses_symlinked_build_dir(project_root: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.png").write_bytes(b"data")
    (project_root / "build").symlink_to(outside)

    assert main(["clean", str(project_root)]) == 1

    assert (outside / "precious.png").read_bytes() == b"data"


def test_clean_does_not_follow_links_inside_build(built_project: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.png").write_bytes(b"data")
    (built_project / "build" / "escape").symlink_to(outside)

    assert main(["clean", str(built_project)]) == 0

    assert (outside / "precious.png").read_bytes() == b"data"
