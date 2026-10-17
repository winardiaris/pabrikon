from __future__ import annotations

from pathlib import Path

import pytest

from pabrikon.project import init_project

VALID_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><rect width="16" height="16"/></svg>\n'


def add_svg(root: Path, context: str, name: str, content: str = VALID_SVG) -> Path:
    path = root / "icons" / context / "scalable" / f"{name}.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    root, _ = init_project(tmp_path / "demo-theme")
    return root


class FakeRenderer:
    """Stands in for rsvg-convert: writes deterministic bytes and records each call."""

    def __init__(self, fail_names: set[str] | None = None) -> None:
        """Configure the renderer double with icon names that should fail."""
        self.calls: list[tuple[str, int]] = []
        self.fail_names = fail_names or set()

    def ensure_available(self) -> str:
        """Pretend the test renderer is installed and return its marker path."""
        return "fake-rsvg"

    def render(self, source: Path, destination: Path, size: int) -> None:
        """Record a render request and write deterministic fixture PNG bytes."""
        from pabrikon.render import RenderError

        self.calls.append((source.stem, size))
        if source.stem in self.fail_names:
            raise RenderError("fake-rsvg failed: boom")
        destination.write_bytes(f"PNG {source.read_text(encoding='utf-8')} {size}".encode())


@pytest.fixture
def fake_renderer(monkeypatch: pytest.MonkeyPatch) -> FakeRenderer:
    renderer = FakeRenderer()
    monkeypatch.setattr("pabrikon.build.RsvgRenderer", lambda: renderer)
    return renderer


def write_config_sizes(root: Path, sizes: list[int], formats: list[str] | None = None) -> None:
    from pabrikon.config import load_config, write_config

    config = load_config(root / "data" / "pabrikon.toml")
    config.build.sizes = sizes
    if formats is not None:
        config.build.formats = formats
    write_config(root / "data" / "pabrikon.toml", config)
