import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from pabrikon import __version__
from pabrikon import cli
from pabrikon.cli import main
from pabrikon.project import init_project


def test_help_lists_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--help"]) == 0
    assert "init" in capsys.readouterr().out


def test_version_matches_package(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == f"pabrikon {__version__}"


def test_unknown_command_is_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["unknown-command"]) == 2
    assert "invalid choice" in capsys.readouterr().err


def test_config_error_exit_code_and_no_traceback(tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    config_path = tmp_path / "data" / "pabrikon.toml"
    config_path.parent.mkdir()
    config_path.write_text("[project\n", encoding="utf-8")

    assert main(["theme", "show", str(tmp_path)]) == 2

    err = capsys.readouterr().err
    assert "pabrikon.toml is not valid TOML" in err
    assert "Traceback" not in err


def test_config_edit_opens_invalid_toml_with_requested_editor(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project_root, _ = init_project(tmp_path / "theme")
    config_path = project_root / "data" / "pabrikon.toml"
    config_path.write_text("[project\n", encoding="utf-8")
    calls = []

    def fake_run(command: list[str], *, check: bool) -> SimpleNamespace:
        calls.append((command, check))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cli.shutil, "which", lambda executable: f"/fake/{executable}")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert main([
        "config", "edit", str(project_root), "--editor", "vim", "--json"
    ]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "command": "config edit",
        "ok": True,
        "path": "data/pabrikon.toml",
        "editor": "vim",
    }
    assert calls == [(["/fake/vim", str(config_path)], False)]
    assert config_path.read_text(encoding="utf-8") == "[project\n"


def test_module_entry_point_runs() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "pabrikon", "--version"], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0
    assert __version__ in completed.stdout


def test_theme_edit_opens_index_theme_with_requested_editor(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project_root, _ = init_project(tmp_path / "theme")
    index_theme = project_root / "index.theme"
    index_theme.unlink()
    calls = []

    def fake_run(command: list[str], *, check: bool) -> SimpleNamespace:
        calls.append((command, check))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cli.shutil, "which", lambda executable: f"/fake/{executable}")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert main([
        "theme", "edit", str(project_root), "--editor", "nano --wait", "--json"
    ]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "command": "theme edit",
        "ok": True,
        "path": "index.theme",
        "editor": "nano",
    }
    assert calls == [(["/fake/nano", "--wait", str(index_theme)], False)]
    assert index_theme.is_file()


def test_aliases_edit_creates_and_opens_alias_file(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project_root, _ = init_project(tmp_path / "theme")
    aliases_file = project_root / "data" / "aliases.toml"
    aliases_file.unlink()
    calls = []

    def fake_run(command: list[str], *, check: bool) -> SimpleNamespace:
        calls.append((command, check))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cli.shutil, "which", lambda executable: f"/fake/{executable}")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert main([
        "aliases", "edit", str(project_root), "--editor", "vim", "--json"
    ]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "command": "aliases edit",
        "ok": True,
        "path": "data/aliases.toml",
        "editor": "vim",
    }
    assert calls == [(["/fake/vim", str(aliases_file)], False)]
    assert "# Icon aliases" in aliases_file.read_text(encoding="utf-8")
