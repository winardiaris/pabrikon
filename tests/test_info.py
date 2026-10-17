import json
from pathlib import Path

import pytest

from conftest import add_svg
from pabrikon.cli import main


def test_info_on_empty_project(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["info", str(project_root), "--json"]) == 0

    info = json.loads(capsys.readouterr().out)
    assert info["project"] == "demo-theme"
    assert info["icons"] == {"svg": 0, "png": 0, "aliases": 0}
    assert info["last_build"] is None


def test_info_counts_sources_and_aliases(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    add_svg(project_root, "apps", "firefox")
    add_svg(project_root, "places", "user-home")
    (project_root / "data" / "aliases.toml").write_text('[places]\nfolder-home = "user-home"\n', encoding="utf-8")

    assert main(["info", str(project_root)]) == 0

    out = capsys.readouterr().out
    assert "SVG:          2" in out
    assert "Aliases:      1" in out
    assert "Last build: never" in out


def test_list_icons_is_sorted_and_ignores_files_outside_scalable(
    project_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    add_svg(project_root, "places", "user-home")
    add_svg(project_root, "apps", "firefox")
    (project_root / "icons" / "apps" / "stray.svg").write_text("<svg/>", encoding="utf-8")

    assert main(["list", "icons", str(project_root)]) == 0

    assert capsys.readouterr().out.splitlines() == ["apps/firefox", "places/user-home"]


def test_list_aliases_json(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (project_root / "data" / "aliases.toml").write_text(
        '[categories]\napplications-mathematics = "apps/accessories-calculator"\n', encoding="utf-8"
    )

    assert main(["list", "aliases", str(project_root), "--json"]) == 0

    assert json.loads(capsys.readouterr().out) == ["categories/applications-mathematics -> apps/accessories-calculator"]


def test_list_invalid_kind_is_usage_error(project_root: Path) -> None:
    assert main(["list", "nonsense", str(project_root)]) == 2
