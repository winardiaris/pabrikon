from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import venv
from pathlib import Path

import pytest


def _build_or_find_wheel(repo_root: Path, output_dir: Path) -> Path:
    """Return a CI-provided wheel or build one for a local acceptance run."""
    configured_dir = os.environ.get("PABRIKON_WHEEL_DIR")
    if configured_dir:
        wheels = sorted(Path(configured_dir).glob("pabrikon-*.whl"))
        assert wheels, f"No Pabrikon wheel found in {configured_dir}"
        return wheels[-1]

    output_dir.mkdir(parents=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(output_dir), str(repo_root)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = sorted(output_dir.glob("pabrikon-*.whl"))
    assert wheels, "Wheel build completed without producing a Pabrikon wheel"
    return wheels[-1]


def _run_cli(command: Path, *arguments: str) -> dict[str, object]:
    """Run Pabrikon in JSON mode and return its parsed report."""
    completed = subprocess.run(
        [str(command), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, f"Command failed: {completed.args}\n{completed.stderr}"
    return json.loads(completed.stdout)


@pytest.mark.skipif(
    not shutil.which("rsvg-convert") or not shutil.which("svgcleaner"),
    reason="end-to-end acceptance requires rsvg-convert and svgcleaner",
)
def test_installed_wheel_completes_icon_theme_workflow(tmp_path: Path) -> None:
    """Install the built wheel in a fresh venv and exercise the full CLI workflow."""
    repo_root = Path(__file__).resolve().parents[1]
    wheel = _build_or_find_wheel(repo_root, tmp_path / "wheelhouse")
    environment = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    command = environment / ("Scripts/pabrikon.exe" if os.name == "nt" else "bin/pabrikon")
    subprocess.run([str(python), "-m", "pip", "install", str(wheel)], check=True, capture_output=True, text=True)

    project = tmp_path / "sample-theme"
    initialized = _run_cli(command, "init", str(project), "--name", "sample-theme", "--json")
    assert initialized["ok"] is True
    source = project / "icons" / "apps" / "scalable" / "firefox.svg"
    source.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
        '<rect width="16" height="16" fill="#369"/></svg>\n',
        encoding="utf-8",
    )
    original_source = source.read_bytes()
    (project / "data" / "aliases.toml").write_text(
        '[apps]\nweb-browser = "firefox"\n',
        encoding="utf-8",
    )

    validation = _run_cli(command, "validate", str(project), "--json")
    assert validation["valid"] is True

    build = _run_cli(command, "build", str(project), "--json")
    assert build["ok"] is True
    assert build["sources"] == 1
    assert (project / "build" / "index.theme").is_file()
    assert (project / "build" / "apps" / "scalable" / "firefox.svg").is_file()
    assert (project / "build" / "apps" / "scalable" / "web-browser.svg").is_symlink()
    assert (project / "build" / "apps" / "16x16" / "firefox.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    optimization = _run_cli(command, "optimize", str(project), "--json")
    assert optimization["ok"] is True
    assert len(optimization["completed"]) == 1
    optimized = project / "dist" / "optimized" / "icons" / "apps" / "scalable" / "firefox.svg"
    assert optimized.is_file()
    assert source.read_bytes() == original_source

    package = _run_cli(command, "package", str(project), "--json")
    archive = project / str(package["output"])
    assert archive.is_file()
    with tarfile.open(archive, "r:gz") as bundle:
        assert "sample-theme/apps/16x16/firefox.png" in bundle.getnames()
        assert "sample-theme/apps/scalable/web-browser.svg" in bundle.getnames()
    first_archive = archive.read_bytes()

    cleaned = _run_cli(command, "clean", str(project), "--json")
    assert cleaned["ok"] is True
    assert not (project / "build").exists()
    assert source.is_file()
    assert archive.is_file()

    _run_cli(command, "build", str(project), "--json")
    _run_cli(command, "package", str(project), "--json")
    assert archive.read_bytes() == first_archive
