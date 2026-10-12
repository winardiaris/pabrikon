from pathlib import Path

import pytest

from pabrikon.config import ProjectConfig, load_config, write_config
from pabrikon.errors import ConfigError


def test_default_config_has_expected_values() -> None:
    config = ProjectConfig.default("my-theme")

    assert config.name == "my-theme"
    assert config.build.sizes == [16, 22, 24, 32, 48, 64, 96, 128, 256]
    assert "apps" in config.build.directories
    assert "emotes" in config.build.directories
    assert "io" in config.build.directories
    assert config.theme.name == "My Theme"


def test_write_and_load_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / "pabrikon.toml"
    config = ProjectConfig.default("demo-theme")
    config.theme.comment = 'Quotes "and" back\\slashes'

    write_config(config_path, config)
    loaded = load_config(config_path)

    assert loaded == config


def test_missing_keys_use_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "pabrikon.toml"
    config_path.write_text('[project]\nname = "demo"\n', encoding="utf-8")

    loaded = load_config(config_path)

    assert loaded.build.sizes == [16, 22, 24, 32, 48, 64, 96, 128, 256]
    assert loaded.validation.strict is False


def test_sizes_are_sorted_and_deduplicated(tmp_path: Path) -> None:
    config_path = tmp_path / "pabrikon.toml"
    config_path.write_text("[build]\nsizes = [48, 16, 48]\n", encoding="utf-8")

    assert load_config(config_path).build.sizes == [16, 48]


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("[project\n", "not valid TOML"),
        ("[build]\nsizes = []\n", "build.sizes"),
        ("[build]\nsizes = [0]\n", "between 1 and"),
        ('[build]\nsizes = ["16"]\n', "build.sizes"),
        ("[build]\nsizes = [true]\n", "build.sizes"),
        ('[build]\nformats = ["jpg"]\n', "unsupported format"),
        ('[build.directories]\nenabled = ["../escape"]\n', "invalid directory name"),
        ('[build.directories]\nenabled = ["apps", "apps"]\n', "duplicate"),
        ('[project]\nname = "bad name"\n', "project.name"),
        ('[validation]\nstrict = "yes"\n', "validation.strict"),
        ('theme = "x"\n', "[theme] must be a table"),
    ],
)
def test_invalid_configuration_is_reported(tmp_path: Path, content: str, expected: str) -> None:
    config_path = tmp_path / "pabrikon.toml"
    config_path.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigError, match=expected.replace("[", r"\[")):
        load_config(config_path)


def test_missing_configuration_is_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "pabrikon.toml")
