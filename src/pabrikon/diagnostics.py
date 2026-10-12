from __future__ import annotations

from dataclasses import asdict, dataclass

ERROR = "error"
WARNING = "warning"


@dataclass(frozen=True)
class Diagnostic:
    level: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        """Return this diagnostic in the stable shape used by JSON output."""
        return asdict(self)


def error(path: str, message: str) -> Diagnostic:
    """Create an error diagnostic associated with a project-relative path."""
    return Diagnostic(ERROR, path, message)


def warning(path: str, message: str) -> Diagnostic:
    """Create a warning diagnostic associated with a project-relative path."""
    return Diagnostic(WARNING, path, message)
