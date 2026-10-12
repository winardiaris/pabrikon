from __future__ import annotations

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2


class PabrikonError(Exception):
    """An expected failure reported to the user without a traceback."""

    exit_code = EXIT_FAILURE

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        """Store a user-facing failure message and optional corrective hint."""
        super().__init__(message)
        self.message = message
        self.hint = hint


class ConfigError(PabrikonError):
    exit_code = EXIT_USAGE


class UsageError(PabrikonError):
    exit_code = EXIT_USAGE


class ToolNotFoundError(PabrikonError):
    pass
