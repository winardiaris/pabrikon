from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .errors import PabrikonError, ToolNotFoundError

RENDER_TIMEOUT_SECONDS = 60


class RenderError(PabrikonError):
    pass


class RsvgRenderer:
    """Render SVG to PNG with librsvg's ``rsvg-convert``."""

    executable = "rsvg-convert"

    def __init__(self) -> None:
        """Initialize the librsvg adapter with lazy executable lookup."""
        self._path: str | None = None

    def ensure_available(self) -> str:
        """Return the rsvg-convert path or raise an actionable dependency error."""
        if self._path is not None:
            return self._path
        path = shutil.which(self.executable)
        if path is None:
            raise ToolNotFoundError(
                f"{self.executable} not found; it is required to render PNG icons",
                hint=(
                    "Install librsvg: `sudo apt install librsvg2-bin` (Debian/Ubuntu), "
                    "`sudo dnf install librsvg2-tools` (Fedora) or `brew install librsvg` (macOS). "
                    'To build SVG only, set build.formats = ["svg"].'
                ),
            )
        self._path = path
        return path

    def render(self, source: Path, destination: Path, size: int) -> None:
        """Render one SVG to a square PNG of the requested pixel size."""
        # Absolute paths keep names starting with "-" from being read as options.
        command = [
            self.ensure_available(),
            "--width", str(size),
            "--height", str(size),
            "--format", "png",
            "--output", str(destination.absolute()),
            str(source.absolute()),
        ]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=RENDER_TIMEOUT_SECONDS, check=False)
        except subprocess.TimeoutExpired as exc:
            raise RenderError(f"{self.executable} timed out after {RENDER_TIMEOUT_SECONDS}s") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or f"exit status {completed.returncode}"
            raise RenderError(f"{self.executable} failed: {detail}")
