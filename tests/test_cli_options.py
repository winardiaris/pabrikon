from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import add_svg, write_config_sizes
from pabrikon.build import build_project
from pabrikon.cli import main
from pabrikon.project import Project


def run_json(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, dict | list]:
    code = main(args)
    captured = capsys.readouterr()
    assert captured.err == ""
    return code, json.loads(captured.out)


def test_json_option_is_available_before_and_after_nested_commands(
    tmp_path: Path, project_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, created = run_json(["--json", "init", str(tmp_path / "new-theme")], capsys)
    assert code == 0
    assert created["command"] == "init"
    assert created["project"].endswith("new-theme")

    code, theme = run_json(["theme", "show", str(project_root), "--json"], capsys)
    assert code == 0
    assert theme["command"] == "theme show"
    assert theme["content"].startswith("[Icon Theme]\n")


def test_json_supports_build_clean_and_aliases(
    project_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config_sizes(project_root, [16], formats=["svg"])
    add_svg(project_root, "apps", "firefox")
    (project_root / "data" / "aliases.toml").write_text('[apps]\nweb-browser = "firefox"\n', encoding="utf-8")

    code, built = run_json(["build", str(project_root), "--dry-run", "--size", "16", "--json"], capsys)
    assert code == 0
    assert built["command"] == "build"
    assert built["sources"] == 1
    assert built["tasks"][0]["source"] == "icons/apps/scalable/firefox.svg"
    assert not (project_root / "build").exists()

    build_project(Project.load(project_root), sizes=[16])
    (project_root / "build" / "apps" / "scalable" / "web-browser.svg").unlink()
    code, aliases = run_json(["aliases", "build", str(project_root), "--dry-run", "--json"], capsys)
    assert code == 0
    assert aliases["command"] == "aliases build"
    assert aliases["counts"]["create"] == 1

    code, cleaned = run_json(["clean", str(project_root), "--dry-run", "--json"], capsys)
    assert code == 0
    assert cleaned["command"] == "clean"
    assert cleaned["count"] > 0
    assert (project_root / "build").exists()


def test_json_supports_optimize_package_and_theme_commands(
    project_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config_sizes(project_root, [16], formats=["svg"])
    add_svg(project_root, "apps", "firefox")

    code, optimized = run_json(["optimize", str(project_root), "--dry-run", "--json"], capsys)
    assert code == 0
    assert optimized["command"] == "optimize"
    assert optimized["tasks"][0]["source"] == "icons/apps/scalable/firefox.svg"

    build_project(Project.load(project_root))
    code, packaged = run_json(["package", str(project_root), "--dry-run", "--json"], capsys)
    assert code == 0
    assert packaged["command"] == "package"
    assert packaged["file_count"] >= 2

    code, initialized = run_json(["theme", "init", str(project_root), "--force", "--json"], capsys)
    assert code == 0
    assert initialized["command"] == "theme init"

    code, validated = run_json(["theme", "validate", str(project_root), "--json"], capsys)
    assert code == 0
    assert validated["valid"] is True


def test_json_wraps_expected_command_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, report = run_json(["build", str(tmp_path), "--json"], capsys)

    assert code == 2
    assert report["command"] == "build"
    assert report["ok"] is False
    assert "configuration file not found" in report["error"]["message"]


def test_quiet_suppresses_normal_output_but_keeps_errors(
    project_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["info", str(project_root), "--quiet"]) == 0
    assert capsys.readouterr().out == ""

    (project_root / "pabrikon.toml").write_text("[project\n", encoding="utf-8")
    assert main(["validate", str(project_root), "--quiet"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not valid TOML" in captured.err


def test_quiet_does_not_suppress_json_output(
    project_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, report = run_json(["--quiet", "info", str(project_root), "--json"], capsys)
    assert code == 0
    assert report["project"] == "demo-theme"


def test_verbose_adds_per_file_build_details(
    project_root: Path, fake_renderer, capsys: pytest.CaptureFixture[str]
) -> None:
    add_svg(project_root, "apps", "firefox")

    assert main(["build", str(project_root), "--size", "16"]) == 0
    normal = capsys.readouterr().out
    assert "icons/apps/scalable/firefox.svg" not in normal

    assert main(["build", str(project_root), "--size", "16", "--all", "--verbose"]) == 0
    verbose = capsys.readouterr().out
    assert "icons/apps/scalable/firefox.svg" in verbose
