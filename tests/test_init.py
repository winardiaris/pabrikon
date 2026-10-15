from pathlib import Path

import pytest

from pabrikon.cli import main
from pabrikon.config import load_config
from pabrikon.errors import ConfigError
from pabrikon.project import Project


def test_init_creates_project_layout(tmp_path: Path) -> None:
    assert main(["init", str(tmp_path / "my-theme")]) == 0

    root = tmp_path / "my-theme"
    config = load_config(root / "data" / "pabrikon.toml")
    assert config.name == "my-theme"
    for path in [
        "README.md", "index.theme", "data/pabrikon.toml", "data/aliases.toml", "dist", "icons/apps/scalable"
    ]:
        assert (root / path).exists(), path
    assert not (root / "pabrikon.toml").exists()
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
    assert load_config(root / "data" / "pabrikon.toml").name == "existing"


def test_init_refuses_existing_project(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "theme"
    assert main(["init", str(root)]) == 0
    config_path = root / "data" / "pabrikon.toml"
    config_before = config_path.read_text(encoding="utf-8")

    assert main(["init", str(root)]) == 1

    assert "already a Pabrikon project" in capsys.readouterr().err
    assert config_path.read_text(encoding="utf-8") == config_before


@pytest.mark.parametrize("name", ["bad name", "-leading-dash", "semi;colon", "..", "a/b"])
def test_init_rejects_invalid_name_without_partial_project(tmp_path: Path, name: str) -> None:
    target = tmp_path / "target"

    assert main(["init", str(target), "--name", name]) == 2

    assert not target.exists()


def test_initialized_project_validates_theme(tmp_path: Path) -> None:
    root = tmp_path / "theme"
    main(["init", str(root)])

    assert main(["theme", "validate", str(root)]) == 0


def test_project_config_defaults_name_from_project_root(tmp_path: Path) -> None:
    root = tmp_path / "custom-theme"
    (root / "data").mkdir(parents=True)
    (root / "data" / "pabrikon.toml").write_text("[theme]\nname = \"Custom Theme\"\n", encoding="utf-8")

    assert Project.load(root).config.name == "custom-theme"


def test_root_config_error_explains_new_location(tmp_path: Path) -> None:
    (tmp_path / "pabrikon.toml").write_text('[project]\nname = "old-layout"\n', encoding="utf-8")

    with pytest.raises(ConfigError, match="Pabrikon now expects") as exc_info:
        Project.load(tmp_path)

    assert "Move the file to data/pabrikon.toml" in exc_info.value.hint


def test_init_refuses_to_create_second_config_for_root_config(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "old-layout"
    root.mkdir()
    old_config = root / "pabrikon.toml"
    old_config.write_text('[project]\nname = "old-layout"\n', encoding="utf-8")

    assert main(["init", str(root)]) == 1

    assert "Move it to data/pabrikon.toml" in capsys.readouterr().err
    assert old_config.is_file()
    assert not (root / "data" / "pabrikon.toml").exists()
