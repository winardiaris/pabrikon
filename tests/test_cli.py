import subprocess
import sys

import pytest

from pabrikon import __version__
from pabrikon.cli import main


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
    (tmp_path / "pabrikon.toml").write_text("[project\n", encoding="utf-8")

    assert main(["theme", "show", str(tmp_path)]) == 2

    err = capsys.readouterr().err
    assert "pabrikon.toml is not valid TOML" in err
    assert "Traceback" not in err


def test_module_entry_point_runs() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "pabrikon", "--version"], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0
    assert __version__ in completed.stdout
