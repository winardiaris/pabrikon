import json
from pathlib import Path

import pytest

from conftest import FakeRenderer, add_svg, write_config_sizes
from pabrikon.cli import main


def run_json(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, dict]:
    code = main(["validate", str(root), "--json"])
    return code, json.loads(capsys.readouterr().out)


def messages(report: dict, level: str) -> list[str]:
    return [f"{item['path']}: {item['message']}" for item in report["diagnostics"] if item["level"] == level]


def test_new_project_is_valid(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(project_root)]) == 0

    out = capsys.readouterr().out
    assert "✓ Configuration" in out
    assert "Validation passed" in out


def test_valid_project_with_icons_and_build(
    project_root: Path, fake_renderer: FakeRenderer, capsys: pytest.CaptureFixture[str]
) -> None:
    add_svg(project_root, "apps", "firefox")
    (project_root / "data" / "aliases.toml").write_text('[apps]\nweb-browser = "firefox"\n', encoding="utf-8")
    main(["build", str(project_root)])
    capsys.readouterr()

    code, report = run_json(project_root, capsys)

    assert code == 0
    assert report == {"valid": True, "errors": 0, "warnings": 0, "diagnostics": []}


def test_missing_configuration_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(tmp_path)]) == 2

    err = capsys.readouterr().err
    assert "configuration file not found" in err
    assert "Traceback" not in err


def test_invalid_toml_json_output_stays_valid(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (project_root / "data" / "pabrikon.toml").write_text("[project\n", encoding="utf-8")

    code, report = run_json(project_root, capsys)

    assert code == 2
    assert report["valid"] is False
    assert "not valid TOML" in report["diagnostics"][0]["message"]


def test_invalid_svg_and_missing_viewbox(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    add_svg(project_root, "mimetypes", "application-pdf", "<svg")
    add_svg(project_root, "apps", "no-viewbox", '<svg xmlns="http://www.w3.org/2000/svg"/>')
    add_svg(project_root, "apps", "no-namespace", "<svg viewBox='0 0 1 1'/>")

    code, report = run_json(project_root, capsys)

    assert code == 1
    errors = messages(report, "error")
    assert any(m.startswith("icons/mimetypes/scalable/application-pdf.svg: invalid SVG XML") for m in errors)
    assert any(m.startswith("icons/apps/scalable/no-namespace.svg: root <svg> element is missing xmlns") for m in errors)
    assert "icons/apps/scalable/no-viewbox.svg: missing viewBox; the icon may not scale correctly" in messages(report, "warning")


def test_human_output_lists_warnings_and_errors(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    add_svg(project_root, "mimetypes", "application-pdf", "<svg")

    assert main(["validate", str(project_root)]) == 1

    captured = capsys.readouterr()
    assert "✗ SVG files" in captured.out
    assert "✗ icons/mimetypes/scalable/application-pdf.svg" in captured.err
    assert "Validation failed:\n1 error\n0 warnings" in captured.err


def test_strict_mode_turns_warnings_into_errors(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    add_svg(project_root, "apps", "no-viewbox", '<svg xmlns="http://www.w3.org/2000/svg"/>')
    config = project_root / "data" / "pabrikon.toml"
    config.write_text(config.read_text(encoding="utf-8").replace("strict = false", "strict = true"), encoding="utf-8")

    code, report = run_json(project_root, capsys)

    assert code == 1
    assert report["warnings"] == 0
    assert any("missing viewBox" in m for m in messages(report, "error"))


def test_broken_alias_is_reported(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (project_root / "data" / "aliases.toml").write_text('[places]\nfolder-home = "user-home"\n', encoding="utf-8")

    code, report = run_json(project_root, capsys)

    assert code == 1
    assert any("target icon places/user-home does not exist" in m for m in messages(report, "error"))


def test_broken_and_escaping_symlinks_are_reported(project_root: Path, tmp_path: Path, capsys) -> None:
    scalable = project_root / "icons" / "apps" / "scalable"
    (scalable / "broken.svg").symlink_to(scalable / "missing.svg")
    outside = tmp_path / "outside.svg"
    outside.write_text("<svg/>", encoding="utf-8")
    (scalable / "escape.svg").symlink_to(outside)

    code, report = run_json(project_root, capsys)

    assert code == 1
    errors = messages(report, "error")
    assert "icons/apps/scalable/broken.svg: broken symbolic link" in errors
    assert "icons/apps/scalable/escape.svg: symbolic link points outside the project" in errors


def test_duplicate_names_and_orphans_are_warnings(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    add_svg(project_root, "apps", "computer")
    add_svg(project_root, "devices", "computer")
    (project_root / "icons" / "apps" / "loose.svg").write_text("<svg/>", encoding="utf-8")
    (project_root / "icons" / "unknown").mkdir()
    (project_root / "icons" / "unknown" / "x.svg").write_text("<svg/>", encoding="utf-8")

    code, report = run_json(project_root, capsys)

    assert code == 0
    warnings = messages(report, "warning")
    assert "computer: duplicate icon name in directories: apps, devices" in warnings
    assert any(m.startswith("icons/apps/loose.svg: orphaned file") for m in warnings)
    assert any(m.startswith("icons/unknown/x.svg: directory 'unknown' is not enabled") for m in warnings)


def test_invalid_theme_directory_declaration(project_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_config_sizes(project_root, [16, 20])

    code, report = run_json(project_root, capsys)

    assert code == 1
    assert any("'apps/20x20' is not declared" in m for m in messages(report, "error"))


def test_missing_raster_and_stale_output_are_warnings(
    project_root: Path, fake_renderer: FakeRenderer, capsys: pytest.CaptureFixture[str]
) -> None:
    add_svg(project_root, "apps", "firefox")
    removed = add_svg(project_root, "apps", "chrome")
    main(["build", str(project_root), "--size", "16"])
    removed.unlink()
    capsys.readouterr()

    code, report = run_json(project_root, capsys)

    assert code == 0
    warnings = messages(report, "warning")
    assert any(m.startswith("icons/apps/scalable/firefox.svg: missing generated size(s): 22x22") for m in warnings)
    assert any(m.startswith("build/apps/16x16/chrome.png: stale generated file") for m in warnings)
