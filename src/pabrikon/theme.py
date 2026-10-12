from __future__ import annotations

import configparser
from pathlib import Path

from .config import ProjectConfig
from .diagnostics import Diagnostic, error, warning

THEME_SECTION = "Icon Theme"
VALID_TYPES = {"Fixed", "Scalable", "Threshold"}

# Context names from the freedesktop Icon Naming Specification; legacy
# Pabrikon also used "Animations" and "Stock".
CONTEXTS = {
    "actions": "Actions",
    "animations": "Animations",
    "apps": "Applications",
    "categories": "Categories",
    "devices": "Devices",
    "emblems": "Emblems",
    "emotes": "Emotes",
    "mimetypes": "MimeTypes",
    "places": "Places",
    "status": "Status",
    "stock": "Stock",
}

SCALABLE_SIZE = 16
SCALABLE_MIN_SIZE = 8
SCALABLE_MAX_SIZE = 512


def size_dir(size: int) -> str:
    """Format a raster icon size as its conventional theme directory name."""
    return f"{size}x{size}"


def theme_directories(config: ProjectConfig) -> dict[str, dict[str, str]]:
    """Describe every configured output directory using index.theme metadata."""
    """Map each generated theme directory to its index.theme section, in a stable order."""
    sections: dict[str, dict[str, str]] = {}
    for ctx in config.build.directories:
        context = CONTEXTS.get(ctx, ctx.title())
        if "png" in config.build.formats:
            for size in config.build.sizes:
                sections[f"{ctx}/{size_dir(size)}"] = {"Size": str(size), "Context": context, "Type": "Fixed"}
        if "svg" in config.build.formats:
            sections[f"{ctx}/scalable"] = {
                "Size": str(SCALABLE_SIZE),
                "MinSize": str(SCALABLE_MIN_SIZE),
                "MaxSize": str(SCALABLE_MAX_SIZE),
                "Context": context,
                "Type": "Scalable",
            }
    return sections


def render_index_theme(config: ProjectConfig) -> str:
    """Render the project's basic icon theme metadata in stable INI format."""
    directories = theme_directories(config)
    lines = [
        f"[{THEME_SECTION}]",
        f"Name={config.theme.name}",
        f"Comment={config.theme.comment}",
    ]
    if config.theme.inherits:
        lines.append(f"Inherits={','.join(config.theme.inherits)}")
    lines.append(f"Directories={','.join(directories)}")
    for directory, keys in directories.items():
        lines.append("")
        lines.append(f"[{directory}]")
        lines.extend(f"{key}={value}" for key, value in keys.items())
    return "\n".join(lines) + "\n"


def parse_index_theme(text: str) -> configparser.ConfigParser:
    """Parse index.theme while preserving key case and disabling interpolation."""
    parser = configparser.ConfigParser(interpolation=None, strict=True, comment_prefixes=("#",), delimiters=("=",))
    parser.optionxform = str  # index.theme keys are case-sensitive
    parser.read_string(text)
    return parser


def validate_index_theme(path: Path, config: ProjectConfig, label: str = "index.theme") -> list[Diagnostic]:
    """Check required metadata and ensure configured build directories are declared."""
    if not path.is_file():
        return [warning(label, "missing; `pabrikon build` will generate one (run `pabrikon theme init` to customize)")]
    try:
        parser = parse_index_theme(path.read_text(encoding="utf-8"))
    except (configparser.Error, UnicodeDecodeError) as exc:
        return [error(label, f"cannot be parsed: {exc}")]

    if not parser.has_section(THEME_SECTION):
        return [error(label, f"missing [{THEME_SECTION}] section")]

    found: list[Diagnostic] = []
    header = parser[THEME_SECTION]
    for key in ("Name", "Comment", "Directories"):
        if not header.get(key, "").strip():
            found.append(error(label, f"[{THEME_SECTION}] is missing required key {key}"))

    declared = [item.strip() for item in header.get("Directories", "").split(",") if item.strip()]
    for directory in declared:
        if not parser.has_section(directory):
            found.append(error(label, f"directory {directory!r} is listed in Directories but has no section"))
            continue
        section = parser[directory]
        if not section.get("Size", "").isdigit():
            found.append(error(label, f"[{directory}] Size must be a positive integer"))
        directory_type = section.get("Type", "Threshold")
        if directory_type not in VALID_TYPES:
            found.append(error(label, f"[{directory}] has invalid Type {directory_type!r}"))

    expected = theme_directories(config)
    for directory in expected:
        if directory not in declared:
            found.append(
                error(
                    label,
                    f"build output directory {directory!r} is not declared; desktops will not find its icons",
                )
            )
    for directory in declared:
        if directory not in expected:
            found.append(warning(label, f"declared directory {directory!r} is not produced by the build configuration"))
    return found
