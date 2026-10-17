from __future__ import annotations

import configparser
import re
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath

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
    "io": "Io",
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


class CaseSensitiveConfigParser(configparser.ConfigParser):
    """Preserve the case-sensitive metadata keys required by index.theme."""

    def optionxform(self, optionstr: str) -> str:
        """Keep option spelling unchanged instead of normalizing keys to lowercase."""
        return optionstr


def parse_index_theme(text: str) -> configparser.ConfigParser:
    """Parse index.theme while preserving key case and disabling interpolation."""
    parser = CaseSensitiveConfigParser(interpolation=None, strict=True, comment_prefixes=("#",), delimiters=("=",))
    parser.read_string(text)
    return parser


@dataclass(frozen=True)
class ThemeDirectory:
    """Metadata needed to map an icon directory to its context and size behavior."""

    path: str
    context: str
    directory_type: str
    size: int
    scale: int = 1


def read_theme_directories(path: Path, config: ProjectConfig) -> list[ThemeDirectory]:
    """Read safe icon directory declarations from index.theme, using generated defaults if absent."""
    if not path.is_file():
        parser = parse_index_theme(render_index_theme(config))
    else:
        parser = parse_index_theme(path.read_text(encoding="utf-8"))
    if not parser.has_section(THEME_SECTION):
        return []
    header = parser[THEME_SECTION]
    context_names = {value: key for key, value in CONTEXTS.items()}
    found: list[ThemeDirectory] = []
    directory_names = header.get("Directories", "").split(",")
    directory_names.extend(header.get("ScaledDirectories", "").split(","))
    for directory in (item.strip() for item in directory_names):
        candidate = PurePosixPath(directory)
        if not directory or candidate.is_absolute() or any(part in {".", ".."} for part in candidate.parts):
            continue
        if not parser.has_section(directory):
            continue
        section = parser[directory]
        context = context_names.get(section.get("Context", ""))
        try:
            size = int(section.get("Size", ""))
        except ValueError:
            continue
        inferred_scale = re.search(r"@(\d+)x$", directory)
        try:
            scale = int(section.get("Scale", inferred_scale.group(1) if inferred_scale else "1"))
        except ValueError:
            continue
        directory_type = section.get("Type", "Threshold")
        if context and size > 0 and scale > 0 and directory_type in VALID_TYPES:
            found.append(ThemeDirectory(directory, context, directory_type, size, scale))
    return found


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
    declared.extend(item.strip() for item in header.get("ScaledDirectories", "").split(",") if item.strip())
    for directory in declared:
        if not parser.has_section(directory):
            found.append(error(label, f"directory {directory!r} is listed in Directories but has no section"))
            continue
        section = parser[directory]
        if not section.get("Size", "").isdigit():
            found.append(error(label, f"[{directory}] Size must be a positive integer"))
        if not section.get("Scale", "1").isdigit() or int(section.get("Scale", "1")) < 1:
            found.append(error(label, f"[{directory}] Scale must be a positive integer"))
        directory_type = section.get("Type", "Threshold")
        if directory_type not in VALID_TYPES:
            found.append(error(label, f"[{directory}] has invalid Type {directory_type!r}"))

    expected = theme_directories(config)
    def is_standard_directory(directory: str) -> bool:
        parts = PurePosixPath(directory).parts
        return len(parts) == 2 and parts[0] in CONTEXTS and (
            parts[1] == "scalable" or re.fullmatch(r"(\d+)x\1", parts[1]) is not None
        )

    dynamic_layout = any(not is_standard_directory(directory) for directory in declared)
    if not dynamic_layout:
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
    else:
        declared_specs = read_theme_directories(path, config)
        if not declared_specs:
            found.append(error(label, "no usable directories with a supported Context, Type, and Size were declared"))
    return found
