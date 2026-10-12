import os
from pathlib import Path

import pytest

from conftest import FakeRenderer, add_svg
from pabrikon.aliases import load_aliases, resolve_aliases
from pabrikon.cli import main
from pabrikon.errors import ConfigError
from pabrikon.project import Project


def write_aliases(root: Path, content: str) -> None:
    (root / "data" / "aliases.toml").write_text(content, encoding="utf-8")


def resolve(root: Path) -> tuple[dict[str, str], list[str]]:
    project = Project.load(root)
    resolved, problems = resolve_aliases(project, load_aliases(project))
    return resolved, [problem.message for problem in problems]


@pytest.fixture
def icons(project_root: Path, fake_renderer: FakeRenderer) -> Path:
    add_svg(project_root, "places", "user-home")
    add_svg(project_root, "apps", "accessories-calculator")
    return project_root


def test_aliases_build_creates_relative_links(icons: Path) -> None:
    write_aliases(icons, '[places]\nfolder-home = "user-home"\n\n'
                         '[categories]\napplications-mathematics = "apps/accessories-calculator"\n')
    assert main(["build", str(icons), "--size", "16"]) == 0

    same = icons / "build" / "places" / "16x16" / "folder-home.png"
    cross = icons / "build" / "categories" / "scalable" / "applications-mathematics.svg"
    assert os.readlink(same) == "user-home.png"
    assert os.readlink(cross) == "../../apps/scalable/accessories-calculator.svg"
    assert same.resolve() == (icons / "build" / "places" / "16x16" / "user-home.png").resolve()
    assert cross.resolve().is_file()


def test_alias_chain_links_to_real_icon(icons: Path) -> None:
    write_aliases(icons, '[places]\nfolder-home = "user-home"\nhome = "folder-home"\n')

    resolved, problems = resolve(icons)

    assert problems == []
    assert resolved == {"places/folder-home": "places/user-home", "places/home": "places/user-home"}


def test_missing_target_is_reported_and_not_linked(icons: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_aliases(icons, '[places]\nfolder-home = "no-such-icon"\n')

    assert main(["build", str(icons), "--size", "16"]) == 1

    assert "target icon places/no-such-icon does not exist" in capsys.readouterr().err
    assert not list((icons / "build").rglob("folder-home*"))


def test_alias_cycle_is_detected(icons: Path) -> None:
    write_aliases(icons, '[places]\na = "b"\nb = "a"\n')

    _, problems = resolve(icons)

    assert "alias cycle: places/a -> places/b -> places/a" in problems


def test_alias_cannot_shadow_real_icon(icons: Path) -> None:
    write_aliases(icons, '[apps]\naccessories-calculator = "places/user-home"\n')

    _, problems = resolve(icons)

    assert problems == ["apps/accessories-calculator would replace the real icon apps/accessories-calculator.svg"]


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ('[unknown]\nx = "user-home"\n', "not enabled"),
        ('[places]\n"bad name" = "user-home"\n', "invalid icon name"),
        ('[places]\nx = "../../etc/passwd"\n', "not enabled"),
    ],
)
def test_invalid_alias_entries(icons: Path, content: str, expected: str) -> None:
    write_aliases(icons, content)

    _, problems = resolve(icons)

    assert len(problems) == 1 and expected in problems[0]


@pytest.mark.parametrize("content", ["[places\n", 'places = "x"\n', "[places]\nx = 1\n"])
def test_malformed_aliases_file_is_config_error(icons: Path, content: str) -> None:
    write_aliases(icons, content)

    with pytest.raises(ConfigError):
        load_aliases(Project.load(icons))
    assert main(["aliases", "build", str(icons)]) == 2


def test_aliases_dry_run_does_not_touch_build(icons: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["build", str(icons), "--size", "16"])
    write_aliases(icons, '[places]\nfolder-home = "user-home"\n')

    assert main(["aliases", "build", str(icons), "--dry-run"]) == 0

    assert "would link places/16x16/folder-home.png -> user-home.png" in capsys.readouterr().out
    assert not list((icons / "build").rglob("folder-home*"))


def test_removed_alias_link_is_pruned(icons: Path) -> None:
    write_aliases(icons, '[places]\nfolder-home = "user-home"\n')
    main(["build", str(icons), "--size", "16"])
    write_aliases(icons, "")

    assert main(["aliases", "build", str(icons)]) == 0

    assert not list((icons / "build").rglob("folder-home*"))
    assert (icons / "build" / "places" / "16x16" / "user-home.png").is_file()


def test_alias_does_not_overwrite_regular_file(icons: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["build", str(icons), "--size", "16"])
    (icons / "build" / "places" / "16x16" / "folder-home.png").write_bytes(b"real")
    write_aliases(icons, '[places]\nfolder-home = "user-home"\n')

    assert main(["aliases", "build", str(icons)]) == 1

    assert "a regular file already exists" in capsys.readouterr().err
    assert (icons / "build" / "places" / "16x16" / "folder-home.png").read_bytes() == b"real"
