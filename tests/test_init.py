from pathlib import Path

import pytest

from pabrikon.cli import main
from pabrikon.config import load_config


def test_init_creates_project_layout(tmp_path: Path) -> None:
    assert main(["init", str(tmp_path / "my-theme")]) == 0

    root = tmp_path / "my-theme"
    config = load_config(root / "pabrikon.toml")
    assert config.name == "my-theme"
    for path in ["README.md", "index.theme", "data/aliases.toml", "dist", "icons/apps/scalable"]:
        assert (root / path).exists(), path
    assert not (root / "build").exists()


def test_init_current_directory_preserves_existing_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "existing"
    root.mkdir()
    (root / "README.md").write_text("mine\n", encoding="utf-8")
    (root / "notes.txt").write_text("keep\n", encoding="utf-8")
    monkeypatch.chdir(root)

    assert main(["init", "."]) == 0

    assert (root / "README.md").read_text(encoding="utf-8") == "mine\n"
    assert (root / "notes.txt").read_text(encoding="utf-8") == "keep\n"
    assert load_config(root / "pabrikon.toml").name == "existing"


def test_init_refuses_existing_project(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "theme"
    assert main(["init", str(root)]) == 0
    config_before = (root / "pabrikon.toml").read_text(encoding="utf-8")

    assert main(["init", str(root)]) == 1

    assert "already a Pabrikon project" in capsys.readouterr().err
    assert (root / "pabrikon.toml").read_text(encoding="utf-8") == config_before


@pytest.mark.parametrize("name", ["bad name", "-leading-dash", "semi;colon", "..", "a/b"])
def test_init_rejects_invalid_name_without_partial_project(tmp_path: Path, name: str) -> None:
    target = tmp_path / "target"

    assert main(["init", str(target), "--name", name]) == 2

    assert not target.exists()


def test_initialized_project_validates_theme(tmp_path: Path) -> None:
    root = tmp_path / "theme"
    main(["init", str(root)])

    assert main(["theme", "validate", str(root)]) == 0
