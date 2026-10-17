from __future__ import annotations

import json
import subprocess
import tomllib
from pathlib import Path

import pytest

from pabrikon.adopt import analyze_adoption, apply_adoption, clone_repository
from pabrikon.cli import main
from pabrikon.config import load_config
from pabrikon.errors import PabrikonError

INDEX_THEME = """\
[Icon Theme]
Name = Sample Theme
Comment = Sample icon set
Inherits = Adwaita, hicolor
Directories = apps/scalable

[apps/scalable]
Size = 48
Type = Scalable
Context = Applications
"""
SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M0 0h16v16H0z"/></svg>\n'


def create_theme(root: Path, *, relative: str = "apps/scalable/firefox.svg") -> Path:
    """Create a tiny existing theme tree and return its theme root."""
    theme = root / "Theme"
    theme.mkdir(parents=True)
    (theme / "index.theme").write_text(INDEX_THEME, encoding="utf-8")
    source = theme / relative
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(SVG, encoding="utf-8")
    return theme


def test_adoption_dry_run_reports_config_and_preserves_checkout(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Preview a nested theme root without creating config or copying assets."""
    theme = create_theme(tmp_path)
    (theme / "README.md").write_text("Upstream documentation\n", encoding="utf-8")
    (theme / "LICENSE").write_text("Upstream terms\n", encoding="utf-8")
    (theme / "index.theme_dark").write_text("alternate metadata\n", encoding="utf-8")

    assert main(["init", "--from", str(tmp_path), "--json"]) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["dry_run"] is True
    assert report["theme_root"] == str(theme)
    assert report["contexts"] == ["apps"]
    assert report["copies"] == [{
        "source": "Theme/apps/scalable/firefox.svg",
        "destination": "icons/apps/scalable/firefox.svg",
    }]
    assert "Theme/README.md" in report["ignored"]
    assert report["alternate_metadata"] == ["index.theme_dark"]
    assert report["license_files"] == ["Theme/LICENSE"]
    assert "Sample Theme" in report["config"]
    assert not (theme / "data" / "pabrikon.toml").exists()
    assert not (theme / "icons").exists()


def test_adoption_apply_copies_assets_and_keeps_upstream_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Apply adoption while retaining the source SVG and upstream metadata."""
    theme = create_theme(tmp_path)
    source = theme / "apps/scalable/firefox.svg"
    metadata = (theme / "index.theme").read_bytes()
    (theme / "LICENSE").write_text("Do not replace", encoding="utf-8")

    assert main(["init", "--from", str(tmp_path), "--apply", "--json"]) == 0

    report = json.loads(capsys.readouterr().out)
    copied = theme / "icons/apps/scalable/firefox.svg"
    assert report["dry_run"] is False
    assert source.is_file()
    assert copied.read_bytes() == source.read_bytes()
    assert (theme / "index.theme").read_bytes() == metadata
    assert (theme / "LICENSE").read_text(encoding="utf-8") == "Do not replace"
    config = load_config(theme / "data/pabrikon.toml")
    assert config.name == "Theme"
    assert config.license == "UNKNOWN"
    assert config.theme.name == "Sample Theme"
    assert config.theme.inherits == ["Adwaita", "hicolor"]


def test_adoption_imports_safe_svg_symlinks_as_aliases(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Preview and write aliases for links to recognized scalable SVG sources."""
    theme = create_theme(tmp_path)
    alias = theme / "apps/scalable/org.example.svg"
    alias.symlink_to("firefox.svg")

    assert main(["init", "--from", str(tmp_path), "--json"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["aliases"] == [{"context": "apps", "name": "org.example", "target": "firefox"}]
    assert preview["aliases_file_conflict"] is False
    assert preview["aliases_toml"] == '[apps]\n"org.example" = "firefox"\n\n'
    assert tomllib.loads(preview["aliases_toml"]) == {"apps": {"org.example": "firefox"}}
    assert not (theme / "data/aliases.toml").exists()

    assert main(["init", "--from", str(tmp_path), "--apply", "--json"]) == 0
    applied = json.loads(capsys.readouterr().out)
    aliases_path = theme / "data/aliases.toml"
    assert aliases_path.read_text(encoding="utf-8") == '[apps]\n"org.example" = "firefox"\n\n'
    assert aliases_path.relative_to(theme).as_posix() in applied["created"]
    assert alias.is_symlink()


def test_adoption_reports_unsafe_or_ambiguous_symlinks(tmp_path: Path) -> None:
    """Keep unsafe and canonical-name-colliding links out of generated aliases."""
    theme = create_theme(tmp_path)
    index_theme = INDEX_THEME.replace(
        "Directories = apps/scalable",
        "Directories = apps/scalable, apps/48",
    ) + "\n[apps/48]\nSize = 48\nType = Scalable\nContext = Applications\n"
    (theme / "index.theme").write_text(index_theme, encoding="utf-8")
    (theme / "apps/scalable/web-browser.svg").write_text(SVG, encoding="utf-8")
    (theme / "apps/48").mkdir()
    (theme / "apps/48/web-browser.svg").symlink_to("../scalable/web-browser.svg")
    external = tmp_path / "outside.svg"
    external.write_text(SVG, encoding="utf-8")
    (theme / "apps/48/external.svg").symlink_to(external)
    (theme / "apps/48/broken.svg").symlink_to("missing.svg")

    plan = analyze_adoption(tmp_path)

    assert plan.aliases == ()
    reasons = {path: reason for path, reason in plan.skipped_links}
    assert reasons["Theme/apps/48/web-browser.svg"] == "alias name collides with a canonical icon"
    assert reasons["Theme/apps/48/external.svg"] == "target escapes the selected theme root"
    assert reasons["Theme/apps/48/broken.svg"] == "broken or cyclic symbolic-link target"


def test_adoption_does_not_overwrite_existing_alias_file(tmp_path: Path) -> None:
    """Preserve a pre-existing alias file and retain imported proposals for review."""
    theme = create_theme(tmp_path)
    (theme / "apps/scalable/web-browser.svg").symlink_to("firefox.svg")
    aliases_path = theme / "data/aliases.toml"
    aliases_path.parent.mkdir()
    aliases_path.write_text('[places]\nhome = "user-home"\n', encoding="utf-8")

    plan = analyze_adoption(tmp_path)
    created = apply_adoption(plan)

    assert plan.aliases_file_conflict is True
    assert plan.aliases[0].name == "web-browser"
    assert aliases_path.read_text(encoding="utf-8") == '[places]\nhome = "user-home"\n'
    assert "data/aliases.toml" not in created


def test_adoption_requires_selection_for_multiple_theme_roots(tmp_path: Path) -> None:
    """Reject an ambiguous checkout and accept an explicit root selection."""
    theme = create_theme(tmp_path)
    second = tmp_path / "dark"
    second.mkdir()
    (second / "index.theme").write_text(INDEX_THEME.replace("Sample Theme", "Dark Theme"), encoding="utf-8")
    (second / "apps/scalable").mkdir(parents=True)
    (second / "apps/scalable/dark.svg").write_text(SVG, encoding="utf-8")

    with pytest.raises(PabrikonError, match="multiple icon-theme roots"):
        analyze_adoption(tmp_path)

    plan = analyze_adoption(tmp_path, theme_root="Theme")
    assert plan.theme_root == theme


def test_adoption_ignores_files_outside_declared_theme_directories(tmp_path: Path) -> None:
    """Keep nested undeclared assets untouched instead of flattening them into a collision."""
    theme = create_theme(tmp_path)
    duplicate = theme / "apps/scalable/other/firefox.svg"
    duplicate.parent.mkdir(parents=True)
    duplicate.write_text("different icon\n", encoding="utf-8")

    plan = analyze_adoption(tmp_path)

    assert not plan.collisions
    assert [item.source.relative_to(theme).as_posix() for item in plan.copies] == ["apps/scalable/firefox.svg"]
    assert "Theme/apps/scalable/other/firefox.svg" in plan.ignored


def test_adoption_uses_index_theme_scalable_sections(tmp_path: Path) -> None:
    """Map direct and size-qualified directories declared scalable in metadata."""
    theme = create_theme(tmp_path, relative="apps/firefox.svg")
    index_theme = INDEX_THEME.replace(
        "Directories = apps/scalable",
        "Directories = apps, apps/48, apps/16\nScaledDirectories = apps/48@2x",
    ).replace(
        "[apps/scalable]\nSize = 48\nType = Scalable\nContext = Applications",
        "[apps]\nSize = 64\nType = Scalable\nContext = Applications\n\n"
        "[apps/48]\nSize = 48\nType = Scalable\nContext = Applications\n\n"
        "[apps/16]\nSize = 16\nType = Fixed\nContext = Applications\n\n"
        "[apps/48@2x]\nSize = 48\nScale = 2\nType = Scalable\nContext = Applications",
    )
    (theme / "index.theme").write_text(index_theme, encoding="utf-8")
    (theme / "apps/48").mkdir(parents=True)
    (theme / "apps/48/settings.svg").write_text(SVG, encoding="utf-8")
    (theme / "apps/48@2x").mkdir(parents=True)
    (theme / "apps/48@2x/settings-hidpi.svg").write_text(SVG, encoding="utf-8")
    (theme / "apps/16").mkdir(parents=True)
    (theme / "apps/16/fixed-only.svg").write_text(SVG, encoding="utf-8")

    plan = analyze_adoption(tmp_path)

    assert [item.source.relative_to(theme).as_posix() for item in plan.copies] == [
        "apps/16/fixed-only.svg",
        "apps/48/settings.svg",
        "apps/48@2x/settings-hidpi.svg",
        "apps/firefox.svg",
    ]
    assert [item.destination.relative_to(theme).as_posix() for item in plan.copies] == [
        "icons/apps/16/fixed-only.svg",
        "icons/apps/48/settings.svg",
        "icons/apps/48@2x/settings-hidpi.svg",
        "icons/apps/firefox.svg",
    ]
    assert ("Theme/apps/16/fixed-only.svg", "icons/apps/16/fixed-only.svg") in [
        (item.source.relative_to(theme.parent).as_posix(), item.destination.relative_to(theme).as_posix())
        for item in plan.copies
    ]
    assert 16 in plan.config.build.sizes
    assert plan.config.build.directories == ["apps"]


def test_adoption_refuses_symlinked_destination_tree(tmp_path: Path) -> None:
    """Reject writes that could be redirected outside the selected theme root."""
    theme = create_theme(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (theme / "icons").symlink_to(outside, target_is_directory=True)

    with pytest.raises(PabrikonError, match="symbolic-link directory"):
        analyze_adoption(tmp_path)


def test_adoption_config_regeneration_keeps_backup(tmp_path: Path) -> None:
    """Require explicit config regeneration and preserve the previous config."""
    theme = create_theme(tmp_path)
    config_path = theme / "data/pabrikon.toml"
    config_path.parent.mkdir()
    config_path.write_text("existing configuration\n", encoding="utf-8")

    with pytest.raises(PabrikonError, match="configuration already exists"):
        analyze_adoption(tmp_path)

    plan = analyze_adoption(tmp_path, regenerate_config=True)
    apply_adoption(plan)
    assert config_path.with_name("pabrikon.toml.bak").read_text(encoding="utf-8") == "existing configuration\n"
    assert load_config(config_path).license == "UNKNOWN"


def test_remote_clone_is_explicit_and_reusable_after_preview(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Clone only the requested URL without submodules and reuse it for apply."""
    target = tmp_path / "checkout"
    url = "https://example.test/icons/theme.git"
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        """Record the clone invocation and create a matching checkout marker."""
        calls.append(command)
        (target / ".git").mkdir(parents=True)
        (target / ".git/config").write_text(
            '[remote "origin"]\n\turl = https://example.test/icons/theme.git\n',
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("pabrikon.adopt.shutil.which", lambda command: "/usr/bin/git")
    monkeypatch.setattr("pabrikon.adopt.subprocess.run", fake_run)

    assert clone_repository(url, target, "main") == target
    assert clone_repository(url, target, "main") == target
    assert len(calls) == 1
    assert "--no-recurse-submodules" in calls[0]
    assert calls[0][-3:] == ["--", url, str(target)]
