from pathlib import Path

import pytest

from pabrikon.cli import main
from pabrikon.config import ProjectConfig
from pabrikon.diagnostics import ERROR, WARNING
from pabrikon.theme import parse_index_theme, render_index_theme, validate_index_theme


def small_config() -> ProjectConfig:
    config = ProjectConfig.default("demo")
    config.build.sizes = [16, 48]
    config.build.directories = ["apps", "places"]
    config.theme.inherits = ["Adwaita", "hicolor"]
    return config


def test_render_index_theme_declares_every_output_directory() -> None:
    parser = parse_index_theme(render_index_theme(small_config()))

    header = parser["Icon Theme"]
    assert header["Name"] == "Demo"
    assert header["Inherits"] == "Adwaita,hicolor"
    assert header["Directories"] == "apps/16x16,apps/48x48,apps/scalable,places/16x16,places/48x48,places/scalable"
    assert dict(parser["apps/48x48"]) == {"Size": "48", "Context": "Applications", "Type": "Fixed"}
    assert parser["places/scalable"]["Type"] == "Scalable"


def test_render_index_theme_is_deterministic() -> None:
    assert render_index_theme(small_config()) == render_index_theme(small_config())


def test_png_only_build_has_no_scalable_directory() -> None:
    config = small_config()
    config.build.formats = ["png"]

    assert "scalable" not in render_index_theme(config)


def test_generated_index_theme_is_valid(tmp_path: Path) -> None:
    path = tmp_path / "index.theme"
    path.write_text(render_index_theme(small_config()), encoding="utf-8")

    assert validate_index_theme(path, small_config()) == []


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("Name=x\n", "cannot be parsed"),
        ("[Other]\nName=x\n", "missing [Icon Theme]"),
        ("[Icon Theme]\nComment=c\nDirectories=\n", "missing required key Name"),
        ("[Icon Theme]\nName=n\nComment=c\nDirectories=apps/16x16\n", "has no section"),
        ("[Icon Theme]\nName=n\nComment=c\nDirectories=apps/16x16\n\n[apps/16x16]\nSize=big\n", "Size must be"),
        ("[Icon Theme]\nName=n\nComment=c\nDirectories=apps/16x16\n\n[apps/16x16]\nSize=16\nType=Odd\n", "invalid Type"),
    ],
)
def test_invalid_index_theme_is_reported(tmp_path: Path, content: str, expected: str) -> None:
    path = tmp_path / "index.theme"
    path.write_text(content, encoding="utf-8")

    messages = [item.message for item in validate_index_theme(path, small_config()) if item.level == ERROR]

    assert any(expected in message for message in messages), messages


def test_undeclared_build_directory_is_error_and_extra_is_warning(tmp_path: Path) -> None:
    config = small_config()
    path = tmp_path / "index.theme"
    path.write_text(render_index_theme(config), encoding="utf-8")
    config.build.sizes = [16, 64]

    diagnostics = validate_index_theme(path, config)

    assert any(d.level == ERROR and "'apps/64x64'" in d.message for d in diagnostics)
    assert any(d.level == WARNING and "'apps/48x48'" in d.message for d in diagnostics)


def test_theme_init_refuses_overwrite_without_force(project_root: Path) -> None:
    index = project_root / "index.theme"
    index.write_text("custom\n", encoding="utf-8")

    assert main(["theme", "init", str(project_root)]) == 1
    assert index.read_text(encoding="utf-8") == "custom\n"

    assert main(["theme", "init", "--force", str(project_root)]) == 0
    assert index.read_text(encoding="utf-8").startswith("[Icon Theme]")


def test_theme_show_prints_generated_metadata_when_file_missing(
    project_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (project_root / "index.theme").unlink()

    assert main(["theme", "show", str(project_root)]) == 0
    assert capsys.readouterr().out.startswith("[Icon Theme]\nName=Demo Theme\n")


def test_theme_validate_fails_on_invalid_metadata(project_root: Path) -> None:
    (project_root / "index.theme").write_text("[Icon Theme]\n", encoding="utf-8")

    assert main(["theme", "validate", str(project_root)]) == 1
