import os
import shutil
from pathlib import Path

import pytest

from conftest import FakeRenderer, add_svg, write_config_sizes
from pabrikon.build import build_project, parse_size_values
from pabrikon.cli import main
from pabrikon.errors import PabrikonError, UsageError
from pabrikon.project import Project


def declare_theme_directories(root: Path, directories: list[tuple[str, int, str]]) -> None:
    """Replace a context's generated directories with a dynamic index.theme layout."""
    index = root / "index.theme"
    lines = index.read_text(encoding="utf-8").splitlines()
    declarations = ",".join(directory for directory, _, _ in directories)
    lines = [f"Directories={declarations}" if line.startswith("Directories=") else line for line in lines]
    for directory, size, directory_type in directories:
        lines.extend(["", f"[{directory}]", f"Size={size}", f"Type={directory_type}", "Context=Devices"])
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")


def snapshot(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): (b"->" + os.readlink(path).encode()) if path.is_symlink() else path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file() or path.is_symlink()
    }


def test_parse_size_values_accepts_single_and_comma_separated_values() -> None:
    assert parse_size_values(48, None) == [48]
    assert parse_size_values(None, "16, 24,32,48") == [16, 24, 32, 48]
    assert parse_size_values(24, "16,24,32") == [16, 24, 32]
    assert parse_size_values(None, None) == []


@pytest.mark.parametrize("sizes", ["16,abc", "0", "5000"])
def test_parse_size_values_rejects_invalid(sizes: str) -> None:
    with pytest.raises(UsageError):
        parse_size_values(None, sizes)


def test_build_renders_configured_sizes_and_copies_svg(project_root: Path, fake_renderer: FakeRenderer) -> None:
    write_config_sizes(project_root, [16, 24, 32, 48, 64, 128, 256])
    source = add_svg(project_root, "apps", "firefox")

    assert main(["build", str(project_root)]) == 0

    build = project_root / "build"
    for size in [16, 24, 32, 48, 64, 128, 256]:
        assert (build / "apps" / f"{size}x{size}" / "firefox.png").read_bytes().endswith(f" {size}".encode())
    assert (build / "apps" / "scalable" / "firefox.svg").read_bytes() == source.read_bytes()
    assert (build / "index.theme").read_text(encoding="utf-8") == (project_root / "index.theme").read_text(encoding="utf-8")
    assert not list(build.rglob(".*.tmp"))
    assert source.read_text(encoding="utf-8").startswith("<svg")


def test_fixed_size_svg_builds_only_its_matching_png(project_root: Path, fake_renderer: FakeRenderer) -> None:
    declare_theme_directories(project_root, [("devices/16", 16, "Fixed")])
    source = project_root / "icons" / "devices" / "16" / "auth-sim.svg"
    source.parent.mkdir(parents=True)
    source.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"/>', encoding="utf-8")

    assert main(["build", str(project_root), "--directory", "devices", "--icon", "auth-sim"]) == 0

    assert fake_renderer.calls == [("auth-sim", 16)]
    assert (project_root / "build/devices/16/auth-sim.png").is_file()
    assert (project_root / "build/devices/16/auth-sim.svg").is_file()
    assert not (project_root / "build/devices/22x22/auth-sim.png").exists()


def test_scaled_directory_uses_index_theme_scale_for_png_pixels(
    project_root: Path, fake_renderer: FakeRenderer
) -> None:
    declare_theme_directories(project_root, [("devices/16@2x", 16, "Fixed")])
    index = project_root / "index.theme"
    metadata = index.read_text(encoding="utf-8").replace(
        "[devices/16@2x]\nSize=16\nType=Fixed\nContext=Devices",
        "[devices/16@2x]\nSize=16\nScale=2\nType=Fixed\nContext=Devices",
    )
    index.write_text(metadata, encoding="utf-8")
    source = project_root / "icons" / "devices" / "16@2x" / "auth-sim.svg"
    source.parent.mkdir(parents=True)
    source.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"/>', encoding="utf-8")

    assert main(["build", str(project_root), "--directory", "devices", "--icon", "auth-sim"]) == 0

    assert fake_renderer.calls == [("auth-sim", 32)]
    assert (project_root / "build/devices/16@2x/auth-sim.png").is_file()
    assert (project_root / "build/devices/16@2x/auth-sim.svg").is_file()


def test_scaled_directory_uses_index_theme_scale_for_png_pixels(
    project_root: Path, fake_renderer: FakeRenderer
) -> None:
    declare_theme_directories(project_root, [("devices/16@2x", 16, "Fixed")])
    index = project_root / "index.theme"
    metadata = index.read_text(encoding="utf-8").replace(
        "[devices/16@2x]\nSize=16\nType=Fixed\nContext=Devices",
        "[devices/16@2x]\nSize=16\nScale=2\nType=Fixed\nContext=Devices",
    )
    index.write_text(metadata, encoding="utf-8")
    source = project_root / "icons" / "devices" / "16@2x" / "auth-sim.svg"
    source.parent.mkdir(parents=True)
    source.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"/>', encoding="utf-8")

    assert main(["build", str(project_root), "--directory", "devices", "--icon", "auth-sim"]) == 0

    assert fake_renderer.calls == [("auth-sim", 32)]
    assert (project_root / "build/devices/16@2x/auth-sim.png").is_file()
    assert (project_root / "build/devices/16@2x/auth-sim.svg").is_file()


def test_fixed_variant_takes_precedence_over_scalable_png_at_same_size(
    project_root: Path, fake_renderer: FakeRenderer
) -> None:
    declare_theme_directories(
        project_root,
        [("devices/16", 16, "Fixed"), ("devices/64", 64, "Scalable")],
    )
    scalable = project_root / "icons" / "devices" / "64" / "auth-sim.svg"
    scalable.parent.mkdir(parents=True)
    scalable.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><title>scalable</title></svg>', encoding="utf-8")
    fixed = project_root / "icons" / "devices" / "16" / "auth-sim.svg"
    fixed.parent.mkdir(parents=True)
    fixed.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><title>fixed</title></svg>', encoding="utf-8")

    assert main(["build", str(project_root), "--directory", "devices", "--icon", "auth-sim"]) == 0

    png = (project_root / "build/devices/16/auth-sim.png").read_bytes()
    assert b"fixed" in png
    assert b"scalable" not in png
    assert (project_root / "build/devices/64/auth-sim.svg").read_bytes() == scalable.read_bytes()
    assert fake_renderer.calls.count(("auth-sim", 16)) == 1


def test_build_generates_index_theme_when_project_has_none(project_root: Path, fake_renderer: FakeRenderer) -> None:
    (project_root / "index.theme").unlink()
    add_svg(project_root, "apps", "firefox")

    assert main(["build", str(project_root)]) == 0

    assert "apps/16x16" in (project_root / "build" / "index.theme").read_text(encoding="utf-8")


def test_build_specific_size_leaves_other_outputs_alone(project_root: Path, fake_renderer: FakeRenderer) -> None:
    add_svg(project_root, "apps", "firefox")

    assert main(["build", str(project_root), "--size", "48"]) == 0

    assert fake_renderer.calls == [("firefox", 48)]
    assert not (project_root / "build" / "apps" / "16x16").exists()


def test_build_size_not_in_config_is_usage_error(project_root: Path, fake_renderer: FakeRenderer) -> None:
    add_svg(project_root, "apps", "firefox")

    assert main(["build", str(project_root), "--size", "40"]) == 2
    assert fake_renderer.calls == []


def test_build_directory_filter(project_root: Path, fake_renderer: FakeRenderer) -> None:
    add_svg(project_root, "apps", "firefox")
    add_svg(project_root, "places", "user-home")

    assert main(["build", str(project_root), "--directory", "apps", "--size", "16"]) == 0

    assert fake_renderer.calls == [("firefox", 16)]


@pytest.mark.parametrize("directory", ["missing", "../.."])
def test_build_rejects_unknown_directory(project_root: Path, fake_renderer: FakeRenderer, directory: str) -> None:
    assert main(["build", str(project_root), "--directory", directory]) == 2


def test_build_missing_icon_is_reported(project_root: Path, fake_renderer: FakeRenderer, capsys) -> None:
    add_svg(project_root, "apps", "firefox")

    assert main(["build", str(project_root), "--icon", "chrome"]) == 1

    err = capsys.readouterr().err
    assert "icon source not found: chrome" in err
    assert "pabrikon list icons" in err
    assert fake_renderer.calls == []


def test_build_icon_matches_exact_name_only(project_root: Path, fake_renderer: FakeRenderer) -> None:
    add_svg(project_root, "apps", "firefox")
    add_svg(project_root, "apps", "firefox-nightly")

    assert main(["build", str(project_root), "--icon", "apps/firefox", "--size", "16"]) == 0

    assert fake_renderer.calls == [("firefox", 16)]


def test_invalid_svg_fails_without_output_and_other_icons_still_build(
    project_root: Path, fake_renderer: FakeRenderer, capsys
) -> None:
    add_svg(project_root, "apps", "broken", "<svg")
    add_svg(project_root, "apps", "firefox")

    assert main(["build", str(project_root), "--size", "16"]) == 1

    assert "icons/apps/scalable/broken.svg" in capsys.readouterr().err
    assert not list((project_root / "build").rglob("broken*"))
    assert (project_root / "build" / "apps" / "16x16" / "firefox.png").exists()


def test_renderer_failure_reports_icon_and_leaves_no_partial_file(project_root: Path) -> None:
    add_svg(project_root, "apps", "firefox")
    project = Project.load(project_root)

    report = build_project(project, renderer=FakeRenderer(fail_names={"firefox"}), sizes=[16])

    assert report.failures == [
        ("icons/apps/scalable/firefox.svg -> build/apps/16x16/firefox.png (16x16)", "fake-rsvg failed: boom")
    ]
    assert not list((project_root / "build").rglob("*.png"))
    assert not list((project_root / "build").rglob(".*.tmp"))


def test_missing_renderer_is_reported_before_writing(project_root: Path, monkeypatch, capsys) -> None:
    add_svg(project_root, "apps", "firefox")
    monkeypatch.setattr("pabrikon.render.shutil.which", lambda name: None)

    assert main(["build", str(project_root)]) == 1

    err = capsys.readouterr().err
    assert "rsvg-convert not found" in err
    assert "librsvg" in err
    assert "Traceback" not in err
    assert not (project_root / "build").exists()


def test_svg_only_build_does_not_need_renderer(project_root: Path, monkeypatch) -> None:
    write_config_sizes(project_root, [16], formats=["svg"])
    add_svg(project_root, "apps", "firefox")
    monkeypatch.setattr("pabrikon.render.shutil.which", lambda name: None)

    assert main(["build", str(project_root)]) == 0
    assert (project_root / "build" / "apps" / "scalable" / "firefox.svg").exists()


def test_dry_run_writes_nothing(project_root: Path, fake_renderer: FakeRenderer, capsys) -> None:
    add_svg(project_root, "apps", "firefox")

    assert main(["build", str(project_root), "--dry-run", "--size", "48"]) == 0

    assert "would build icons/apps/scalable/firefox.svg -> build/apps/48x48/firefox.png" in capsys.readouterr().out
    assert not (project_root / "build").exists()
    assert fake_renderer.calls == []


def test_second_build_skips_unchanged_outputs(project_root: Path, fake_renderer: FakeRenderer) -> None:
    add_svg(project_root, "apps", "firefox")
    add_svg(project_root, "apps", "chrome")
    main(["build", str(project_root), "--size", "16"])
    first = snapshot(project_root / "build")
    fake_renderer.calls.clear()

    assert main(["build", str(project_root), "--size", "16"]) == 0

    assert fake_renderer.calls == []
    assert snapshot(project_root / "build") == first


def test_changed_source_rebuilds_only_that_icon(project_root: Path, fake_renderer: FakeRenderer) -> None:
    add_svg(project_root, "apps", "firefox")
    chrome = add_svg(project_root, "apps", "chrome")
    main(["build", str(project_root), "--size", "16"])
    fake_renderer.calls.clear()
    future = chrome.stat().st_mtime + 10
    os.utime(chrome, (future, future))

    main(["build", str(project_root), "--size", "16"])

    assert fake_renderer.calls == [("chrome", 16)]


def test_added_size_builds_only_new_outputs(project_root: Path, fake_renderer: FakeRenderer) -> None:
    write_config_sizes(project_root, [48])
    add_svg(project_root, "apps", "firefox")
    main(["build", str(project_root)])
    fake_renderer.calls.clear()
    write_config_sizes(project_root, [48, 64])

    main(["build", str(project_root)])

    assert fake_renderer.calls == [("firefox", 64)]


def test_all_flag_rebuilds_everything(project_root: Path, fake_renderer: FakeRenderer) -> None:
    add_svg(project_root, "apps", "firefox")
    main(["build", str(project_root), "--size", "16"])
    fake_renderer.calls.clear()

    main(["build", str(project_root), "--size", "16", "--all"])

    assert fake_renderer.calls == [("firefox", 16)]


def test_rebuild_from_scratch_is_identical(project_root: Path, fake_renderer: FakeRenderer) -> None:
    add_svg(project_root, "apps", "firefox")
    add_svg(project_root, "places", "user-home")
    (project_root / "data" / "aliases.toml").write_text('[places]\nfolder-home = "user-home"\n', encoding="utf-8")
    main(["build", str(project_root)])
    first = snapshot(project_root / "build")
    shutil.rmtree(project_root / "build")

    main(["build", str(project_root)])

    assert snapshot(project_root / "build") == first


def test_shell_metacharacters_in_file_name_are_not_executed(project_root: Path, fake_renderer: FakeRenderer) -> None:
    add_svg(project_root, "apps", "icon;touch-malicious-file")

    assert main(["build", str(project_root)]) == 1  # rejected as an invalid icon name

    assert not list(project_root.rglob("malicious-file*"))
    assert fake_renderer.calls == []


def test_symlinked_build_dir_is_refused(project_root: Path, tmp_path: Path, fake_renderer: FakeRenderer) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (project_root / "build").symlink_to(outside)
    add_svg(project_root, "apps", "firefox")

    with pytest.raises(PabrikonError, match="symbolic link"):
        build_project(Project.load(project_root), renderer=fake_renderer)
    assert list(outside.iterdir()) == []


def test_symlinked_source_is_not_built(project_root: Path, tmp_path: Path, fake_renderer: FakeRenderer) -> None:
    outside = tmp_path / "outside.svg"
    outside.write_text("<svg/>", encoding="utf-8")
    link = project_root / "icons" / "apps" / "scalable" / "escape.svg"
    link.symlink_to(outside)

    main(["build", str(project_root)])

    assert fake_renderer.calls == []


@pytest.mark.skipif(shutil.which("rsvg-convert") is None, reason="rsvg-convert is not installed")
def test_real_rsvg_render_produces_png(project_root: Path) -> None:
    add_svg(project_root, "apps", "firefox")

    assert main(["build", str(project_root), "--size", "24"]) == 0

    png = (project_root / "build" / "apps" / "24x24" / "firefox.png").read_bytes()
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert int.from_bytes(png[16:20], "big") == 24  # IHDR width
    assert int.from_bytes(png[20:24], "big") == 24  # IHDR height
