from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import ConfigError

CONFIG_FILE = "data/pabrikon.toml"

DEFAULT_DIRECTORIES = [
    "actions",
    "animations",
    "apps",
    "categories",
    "devices",
    "emblems",
    "emotes",
    "io",
    "mimetypes",
    "places",
    "status",
    "stock",
]

DEFAULT_BUILD_SIZES = [16, 22, 24, 32, 48, 64, 96, 128, 256]
SUPPORTED_FORMATS = ("svg", "png")
MAX_ICON_SIZE = 1024

# Project and directory names become path components and archive names, so
# they are limited to characters that are safe in both.
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass
class BuildSettings:
    sizes: list[int] = field(default_factory=lambda: DEFAULT_BUILD_SIZES.copy())
    directories: list[str] = field(default_factory=lambda: DEFAULT_DIRECTORIES.copy())
    formats: list[str] = field(default_factory=lambda: list(SUPPORTED_FORMATS))


@dataclass
class ThemeSettings:
    name: str = "My Theme"
    comment: str = "Custom Linux icon theme"
    inherits: list[str] = field(default_factory=lambda: ["Adwaita"])


@dataclass
class ValidationSettings:
    strict: bool = False


@dataclass
class ProjectConfig:
    name: str
    version: str = "0.1.0"
    description: str = "Custom Linux icon theme"
    license: str = "GPL-3.0"
    theme: ThemeSettings = field(default_factory=ThemeSettings)
    build: BuildSettings = field(default_factory=BuildSettings)
    validation: ValidationSettings = field(default_factory=ValidationSettings)

    @classmethod
    def default(cls, project_name: str) -> "ProjectConfig":
        """Create project defaults with a display name derived from the directory name."""
        return cls(
            name=project_name,
            description=f"{project_name} Linux icon theme",
            theme=ThemeSettings(name=project_name.replace("-", " ").title()),
        )


def is_valid_name(name: str) -> bool:
    """Return whether a project or theme directory name is a safe path component."""
    return bool(NAME_PATTERN.match(name)) and name not in {".", ".."}


def _table(data: dict, key: str) -> dict:
    """Read a TOML table, treating an omitted table as empty and rejecting other values."""
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ConfigError(f"[{key}] must be a table")
    return value


def _string(table: dict, key: str, label: str, default: str) -> str:
    """Read a required non-empty string from a parsed TOML table."""
    value = table.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{label} must be a non-empty string")
    return value


def _string_list(table: dict, key: str, label: str, default: list[str]) -> list[str]:
    """Read a list of non-empty strings while preserving its configured order."""
    value = table.get(key, default)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ConfigError(f"{label} must be a list of non-empty strings")
    return list(value)


def _parse_sizes(value: object) -> list[int]:
    """Validate raster dimensions and return unique sizes in ascending order."""
    if (
        not isinstance(value, list)
        or not value
        # bool is a subclass of int; `true` is not a size.
        or not all(isinstance(item, int) and not isinstance(item, bool) for item in value)
    ):
        raise ConfigError("build.sizes must be a non-empty list of integers")
    for size in value:
        if not 1 <= size <= MAX_ICON_SIZE:
            raise ConfigError(f"build.sizes contains {size}; sizes must be between 1 and {MAX_ICON_SIZE}")
    return sorted(set(value))


def parse_config(data: dict, default_name: str) -> ProjectConfig:
    """Validate parsed TOML data and populate omitted settings from project defaults."""
    project = _table(data, "project")
    theme = _table(data, "theme")
    build = _table(data, "build")
    validation = _table(data, "validation")

    name = _string(project, "name", "project.name", default_name)
    if not is_valid_name(name):
        raise ConfigError(
            f"project.name {name!r} is invalid",
            hint="Use letters, digits, '.', '_' or '-', starting with a letter or digit.",
        )

    directories = _string_list(_table(build, "directories"), "enabled", "build.directories.enabled", DEFAULT_DIRECTORIES)
    for directory in directories:
        if not is_valid_name(directory):
            raise ConfigError(f"build.directories.enabled contains invalid directory name {directory!r}")
    if len(set(directories)) != len(directories):
        raise ConfigError("build.directories.enabled contains duplicate entries")

    formats = _string_list(build, "formats", "build.formats", list(SUPPORTED_FORMATS))
    unknown = sorted(set(formats) - set(SUPPORTED_FORMATS))
    if unknown:
        raise ConfigError(
            f"build.formats contains unsupported format(s): {', '.join(unknown)}",
            hint=f"Supported formats: {', '.join(SUPPORTED_FORMATS)}",
        )

    strict = validation.get("strict", False)
    if not isinstance(strict, bool):
        raise ConfigError("validation.strict must be true or false")

    return ProjectConfig(
        name=name,
        version=_string(project, "version", "project.version", "0.1.0"),
        description=_string(project, "description", "project.description", "Custom Linux icon theme"),
        license=_string(project, "license", "project.license", "GPL-3.0"),
        theme=ThemeSettings(
            name=_string(theme, "name", "theme.name", "My Theme"),
            comment=_string(theme, "comment", "theme.comment", "Custom Linux icon theme"),
            inherits=_string_list(theme, "inherits", "theme.inherits", ["Adwaita"]),
        ),
        build=BuildSettings(
            sizes=_parse_sizes(build.get("sizes", DEFAULT_BUILD_SIZES)),
            directories=directories,
            formats=formats,
        ),
        validation=ValidationSettings(strict=strict),
    )


def load_config(path: Path, *, default_name: str | None = None) -> ProjectConfig:
    """Load a project's TOML configuration and translate parse errors into actionable errors."""
    if not path.is_file():
        raise ConfigError(
            f"configuration file not found: {path}",
            hint="Run `pabrikon init` to create a project, or pass the project directory as PATH.",
        )
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path.name} is not valid TOML: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc.strerror}") from exc
    try:
        if default_name is None:
            project_root = path.parent.parent if path.parent.name == "data" else path.parent
            default_name = project_root.resolve().name
        return parse_config(data, default_name)
    except ConfigError as exc:
        exc.message = f"{path.name}: {exc.message}"
        raise


def format_toml_value(value: str | int | bool | list) -> str:
    """Serialize supported configuration values as TOML-compatible literals."""
    if isinstance(value, list):
        return "[" + ", ".join(format_toml_value(item) for item in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    # JSON string escapes are a subset of TOML basic-string escapes.
    return json.dumps(value, ensure_ascii=False)


def render_config(config: ProjectConfig) -> str:
    """Return the project's canonical TOML representation."""
    v = format_toml_value
    lines = [
        "[project]",
        f"name = {v(config.name)}",
        f"version = {v(config.version)}",
        f"description = {v(config.description)}",
        f"license = {v(config.license)}",
        "",
        "[theme]",
        f"name = {v(config.theme.name)}",
        f"comment = {v(config.theme.comment)}",
        f"inherits = {v(config.theme.inherits)}",
        "",
        "[build]",
        f"sizes = {v(config.build.sizes)}",
        f"formats = {v(config.build.formats)}",
        "",
        "[build.directories]",
        f"enabled = {v(config.build.directories)}",
        "",
        "[validation]",
        f"strict = {v(config.validation.strict)}",
    ]
    return "\n".join(lines) + "\n"


def write_config(path: Path, config: ProjectConfig) -> Path:
    """Write the project's canonical TOML representation and return its path."""
    path.write_text(render_config(config), encoding="utf-8")
    return path
