# PYTHON_ARGCOMPLETE_OK
from __future__ import annotations

import argparse
import argcomplete
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import __version__
from .errors import EXIT_FAILURE, EXIT_OK, ConfigError, PabrikonError
from .aliases import AliasLink, apply_alias_links, load_aliases, plan_alias_links, resolve_aliases
from .build import build_project, parse_size_values
from .clean import CLEAN_TYPES, apply_clean, plan_clean
from .config import CONFIG_FILE
from .info import LIST_KINDS, format_info, list_items, project_info
from .optimize import optimize_project
from .package import package_project
from .project import ALIASES_TEMPLATE, Project, init_project
from .theme import render_index_theme, validate_index_theme
from .validate import validate_project
from .diagnostics import ERROR, WARNING, Diagnostic


class Output:
    def __init__(self, *, verbose: bool = False, quiet: bool = False) -> None:
        """Configure concise CLI output with optional detail or quiet modes."""
        self.verbose = verbose
        self.quiet = quiet

    def info(self, message: str = "") -> None:
        """Write normal progress output unless quiet mode is active."""
        if not self.quiet:
            print(message)

    def detail(self, message: str) -> None:
        """Write supplemental output only when verbose mode is active."""
        if self.verbose and not self.quiet:
            print(message)

    def write(self, message: str) -> None:
        """Write primary command output unless quiet mode is active."""
        if not self.quiet:
            print(message, end="")

    def error(self, message: str, hint: str | None = None) -> None:
        """Write an error and optional next-step hint to standard error."""
        print(f"Error: {message}", file=sys.stderr)
        if hint:
            print(f"\nHint:\n    {hint}", file=sys.stderr)


def print_diagnostics(out: Output, diagnostics: list[Diagnostic]) -> None:
    """Render grouped validation diagnostics in human-readable form."""
    warnings = [item for item in diagnostics if item.level == WARNING]
    if warnings:
        out.info("\nWarnings:\n")
        for item in warnings:
            out.info(f"⚠ {item.path}\n  {item.message}")
    print_failures([(item.path, item.message) for item in diagnostics if item.level == ERROR])


def emit_json(report: object) -> None:
    """Write one machine-readable JSON value to standard output."""
    print(json.dumps(report, indent=2))


def json_error(args: argparse.Namespace, message: str, hint: str | None = None) -> None:
    """Write an expected command error in the JSON envelope used by automation."""
    command = args.command
    if command == "theme":
        command = f"theme {args.theme_command}"
    elif command == "config":
        command = f"config {args.config_command}"
    elif command == "aliases":
        command = f"aliases {args.alias_command}"
    error = {"message": message}
    if hint:
        error["hint"] = hint
    emit_json({"command": command, "ok": False, "error": error})


def resolve_editor_command(requested: str | None) -> list[str]:
    """Resolve a configured terminal editor without invoking a shell."""
    candidates = [requested] if requested else [os.environ.get("VISUAL"), os.environ.get("EDITOR"), "vim", "nano"]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            command = shlex.split(candidate)
        except ValueError as exc:
            raise PabrikonError(f"invalid editor command: {exc}") from exc
        if not command:
            continue
        executable = shutil.which(command[0])
        if executable:
            return [executable, *command[1:]]
        if requested:
            raise PabrikonError(
                f"editor not found: {command[0]}",
                hint="Install vim or nano, set EDITOR or VISUAL, or pass --editor.",
            )
    raise PabrikonError(
        "no terminal editor found",
        hint="Install vim or nano, set EDITOR or VISUAL, or pass --editor.",
    )


def cmd_init(args: argparse.Namespace, out: Output) -> int:
    """Initialize a project and report the created starter paths."""
    root, created = init_project(Path(args.target), name=args.name)
    if args.json:
        emit_json({
            "command": "init",
            "ok": True,
            "project": str(root),
            "created": [path.relative_to(root).as_posix() if path != root else "." for path in created],
        })
        return EXIT_OK
    for path in created:
        out.detail(f"created {path}")
    out.info(f"Initialized project at {root}")
    return EXIT_OK


def cmd_config_edit(args: argparse.Namespace, out: Output) -> int:
    """Open the existing project configuration without parsing its TOML."""
    root = Path(args.path).resolve()
    config_path = root / CONFIG_FILE
    data_dir = root / "data"
    if data_dir.is_symlink() or config_path.is_symlink():
        raise PabrikonError(f"refusing to edit symbolic link {config_path}")
    if config_path.exists() and not config_path.is_file():
        raise PabrikonError(f"cannot edit {config_path}: it is not a regular file")
    if not config_path.is_file():
        raise ConfigError(
            f"configuration file not found: {config_path}",
            hint="Run `pabrikon init` to create a project configuration.",
        )

    editor = resolve_editor_command(args.editor)
    if not args.json:
        out.info(f"Opening {config_path} with {Path(editor[0]).name}...")
    result = subprocess.run([*editor, str(config_path)], check=False)
    if result.returncode:
        raise PabrikonError(f"editor exited with status {result.returncode}")
    if args.json:
        emit_json({
            "command": "config edit",
            "ok": True,
            "path": CONFIG_FILE,
            "editor": Path(editor[0]).name,
        })
    return EXIT_OK


def cmd_theme(args: argparse.Namespace, out: Output) -> int:
    """Handle theme metadata generation, display, and validation commands."""
    project = Project.load(Path(args.path))
    if args.theme_command == "init":
        if project.index_theme.exists() and not args.force:
            raise PabrikonError(
                f"{project.index_theme.name} already exists",
                hint=f"Use `pabrikon theme init --force` to regenerate it from {CONFIG_FILE}.",
            )
        project.index_theme.write_text(render_index_theme(project.config), encoding="utf-8")
        if args.json:
            emit_json({"command": "theme init", "ok": True, "path": "index.theme"})
            return EXIT_OK
        out.info(f"Wrote {project.index_theme}")
        return EXIT_OK
    if args.theme_command == "show":
        content = (
            project.index_theme.read_text(encoding="utf-8")
            if project.index_theme.is_file()
            else render_index_theme(project.config)
        )
        if args.json:
            emit_json({"command": "theme show", "ok": True, "path": "index.theme", "content": content})
        else:
            out.write(content)
        return EXIT_OK
    if args.theme_command == "edit":
        editor = resolve_editor_command(args.editor)
        if project.index_theme.is_symlink():
            raise PabrikonError(f"refusing to edit symbolic link {project.index_theme}")
        if project.index_theme.exists() and not project.index_theme.is_file():
            raise PabrikonError(f"cannot edit {project.index_theme}: it is not a regular file")
        if not project.index_theme.exists():
            project.index_theme.write_text(render_index_theme(project.config), encoding="utf-8")
        if not args.json:
            out.info(f"Opening {project.index_theme} with {Path(editor[0]).name}...")
        result = subprocess.run([*editor, str(project.index_theme)], check=False)
        if result.returncode:
            raise PabrikonError(f"editor exited with status {result.returncode}")
        if args.json:
            emit_json({
                "command": "theme edit",
                "ok": True,
                "path": "index.theme",
                "editor": Path(editor[0]).name,
            })
        return EXIT_OK
    diagnostics = validate_index_theme(project.index_theme, project.config)
    if args.json:
        errors = sum(item.level == ERROR for item in diagnostics)
        warnings = sum(item.level == WARNING for item in diagnostics)
        emit_json({
            "valid": errors == 0,
            "errors": errors,
            "warnings": warnings,
            "diagnostics": [item.to_dict() for item in diagnostics],
        })
        return EXIT_FAILURE if errors else EXIT_OK
    print_diagnostics(out, diagnostics)
    if any(item.level == ERROR for item in diagnostics):
        return EXIT_FAILURE
    out.info("✓ Theme metadata")
    return EXIT_OK


def print_failures(failures: list[tuple[str, str]]) -> None:
    """Print build or processing failures with their affected paths."""
    if failures:
        print("\nErrors:\n", file=sys.stderr)
        for path, message in failures:
            print(f"✗ {path}\n  {message}", file=sys.stderr)


def print_alias_links(out: Output, build_dir: Path, links: list[AliasLink], dry_run: bool) -> None:
    """Summarize planned alias links and their actions for CLI users."""
    verbs = {"create": "link", "replace": "relink", "remove": "remove"}
    for item in links:
        if item.action in verbs:
            line = f"{verbs[item.action]} {item.link.relative_to(build_dir).as_posix()} -> {item.target}"
            if dry_run:
                out.info(f"  would {line}")
            else:
                out.detail(f"  {line}")


def cmd_build(args: argparse.Namespace, out: Output) -> int:
    """Run a project build and translate its report into CLI output and exit status."""
    started = time.monotonic()
    project = Project.load(Path(args.path))
    if not args.json:
        out.info("Planning build (dry run)...\n" if args.dry_run else "Building icon theme...\n")
    report = build_project(
        project,
        sizes=parse_size_values(args.size, args.sizes),
        directory=args.directory,
        icon=args.icon,
        rebuild_all=args.all,
        dry_run=args.dry_run,
    )
    if args.json:
        emit_json({
            "command": "build",
            "ok": not report.failures,
            "sources": report.sources,
            "rendered": report.rendered,
            "copied": report.copied,
            "up_to_date": report.up_to_date,
            "tasks": [
                {
                    "source": task.source.path.relative_to(project.root).as_posix(),
                    "output": task.output.relative_to(project.root).as_posix(),
                    "size": task.size,
                }
                for task in report.tasks
            ],
            "aliases": [
                {
                    "action": item.action,
                    "path": item.link.relative_to(project.build_dir).as_posix(),
                    "target": item.target,
                }
                for item in report.aliases
            ],
            "failures": [{"path": path, "message": message} for path, message in report.failures],
        })
        return EXIT_FAILURE if report.failures else EXIT_OK
    for task in report.tasks:
        if args.dry_run:
            out.info(f"  would build {task.describe(project.root)}")
        else:
            out.detail(f"  {task.describe(project.root)}")
    print_alias_links(out, project.build_dir, report.aliases, args.dry_run)
    links = sum(1 for item in report.aliases if item.action != "remove")
    verb = "to build" if args.dry_run else "built"
    out.info(f"✓ {report.sources:,} SVG sources")
    out.info(f"✓ {report.rendered:,} PNG {verb}, {report.copied:,} SVG {'to copy' if args.dry_run else 'copied'}, "
             f"{report.up_to_date:,} up to date")
    out.info(f"✓ {links:,} alias links")
    print_failures(report.failures)
    if report.failures:
        out.info(f"\nBuild finished with {len(report.failures)} error(s)")
        return EXIT_FAILURE
    if not args.dry_run:
        out.info(f"✓ Build completed in {time.monotonic() - started:.2f}s")
    return EXIT_OK


def cmd_aliases(args: argparse.Namespace, out: Output) -> int:
    """Resolve configured aliases and create or preview generated links."""
    project = Project.load(Path(args.path))
    if args.alias_command == "edit":
        editor = resolve_editor_command(args.editor)
        if project.data_dir.is_symlink() or project.aliases_file.is_symlink():
            raise PabrikonError(f"refusing to edit symbolic link {project.aliases_file}")
        if project.aliases_file.exists() and not project.aliases_file.is_file():
            raise PabrikonError(f"cannot edit {project.aliases_file}: it is not a regular file")
        if not project.aliases_file.exists():
            project.data_dir.mkdir(parents=True, exist_ok=True)
            project.aliases_file.write_text(ALIASES_TEMPLATE, encoding="utf-8")
        if not args.json:
            out.info(f"Opening {project.aliases_file} with {Path(editor[0]).name}...")
        result = subprocess.run([*editor, str(project.aliases_file)], check=False)
        if result.returncode:
            raise PabrikonError(f"editor exited with status {result.returncode}")
        if args.json:
            emit_json({
                "command": "aliases edit",
                "ok": True,
                "path": "data/aliases.toml",
                "editor": Path(editor[0]).name,
            })
        return EXIT_OK
    project.check_build_dir()
    resolved, problems = resolve_aliases(project, load_aliases(project))
    links = plan_alias_links(project, resolved)
    if not args.dry_run:
        apply_alias_links(links)
    if args.json:
        counts = {
            action: sum(item.action == action for item in links)
            for action in ("create", "replace", "unchanged", "remove")
        }
        emit_json({
            "command": "aliases build",
            "ok": not problems,
            "counts": counts,
            "links": [
                {
                    "action": item.action,
                    "path": item.link.relative_to(project.build_dir).as_posix(),
                    "target": item.target,
                }
                for item in links
            ],
            "problems": [item.to_dict() for item in problems],
        })
        return EXIT_FAILURE if problems else EXIT_OK
    print_alias_links(out, project.build_dir, links, args.dry_run)
    if not project.build_dir.is_dir():
        out.info("build/ does not exist yet; run `pabrikon build` to render alias targets first.")
    counts = {action: sum(1 for item in links if item.action == action) for action in ("create", "replace", "unchanged", "remove")}
    prefix = "Would apply" if args.dry_run else "Applied"
    out.info(f"{prefix}: {counts['create']} created, {counts['replace']} replaced, "
             f"{counts['unchanged']} unchanged, {counts['remove']} removed")
    print_failures([(problem.path, problem.message) for problem in problems])
    return EXIT_FAILURE if problems else EXIT_OK


def cmd_clean(args: argparse.Namespace, out: Output) -> int:
    """Remove selected generated files or display a dry-run plan."""
    project = Project.load(Path(args.path))
    paths = plan_clean(project, args.type)
    if args.json:
        if paths and not args.dry_run:
            apply_clean(project, args.type, paths)
        emit_json({
            "command": "clean",
            "ok": True,
            "type": args.type,
            "dry_run": args.dry_run,
            "count": len(paths),
            "paths": [path.relative_to(project.root).as_posix() for path in paths],
        })
        return EXIT_OK
    if not paths:
        out.info("Nothing to clean.")
        return EXIT_OK
    for path in paths:
        relative = path.relative_to(project.root).as_posix()
        if args.dry_run:
            out.info(f"would remove {relative}")
        else:
            out.detail(f"removed {relative}")
    if not args.dry_run:
        apply_clean(project, args.type, paths)
    out.info(f"{'Would remove' if args.dry_run else 'Removed'} {len(paths):,} generated file(s) ({args.type}).")
    return EXIT_OK


def cmd_optimize(args: argparse.Namespace, out: Output) -> int:
    """Optimize source SVGs and report saved space or task failures."""
    project = Project.load(Path(args.path))
    report = optimize_project(project, in_place=args.in_place, dry_run=args.dry_run)
    if args.json:
        emit_json({
            "command": "optimize",
            "ok": not report.failures,
            "dry_run": args.dry_run,
            "in_place": args.in_place,
            "tasks": [
                {
                    "source": task.source.relative_to(project.root).as_posix(),
                    "destination": task.destination.relative_to(project.root).as_posix(),
                    "original_size": task.original_size,
                }
                for task in report.tasks
            ],
            "completed": [
                {
                    "source": asset.task.source.relative_to(project.root).as_posix(),
                    "destination": asset.task.destination.relative_to(project.root).as_posix(),
                    "original_size": asset.task.original_size,
                    "optimized_size": asset.optimized_size,
                    "saved": asset.saved,
                }
                for asset in report.completed
            ],
            "bytes_saved": report.bytes_saved,
            "failures": [{"path": path, "message": message} for path, message in report.failures],
        })
        return EXIT_FAILURE if report.failures else EXIT_OK
    for task in report.tasks:
        source = task.source.relative_to(project.root).as_posix()
        destination = task.destination.relative_to(project.root).as_posix()
        if args.dry_run:
            out.info(f"would optimize {source} -> {destination}")
    for asset in report.completed:
        source = asset.task.source.relative_to(project.root).as_posix()
        out.detail(
            f"{source}: {asset.task.original_size:,} B -> {asset.optimized_size:,} B "
            f"({asset.saved:+,} B)"
        )
    print_failures(report.failures)
    if report.failures:
        out.info(f"\nOptimization finished with {len(report.failures)} error(s)")
        return EXIT_FAILURE

    original_size = sum(task.original_size for task in report.tasks)
    if args.dry_run:
        out.info(f"Would optimize {len(report.tasks):,} SVG file(s).")
    else:
        optimized_size = sum(asset.optimized_size for asset in report.completed)
        out.info(
            f"Optimized {len(report.completed):,} SVG file(s): "
            f"{original_size:,} B -> {optimized_size:,} B ({report.bytes_saved:+,} B)"
        )
    return EXIT_OK


def cmd_package(args: argparse.Namespace, out: Output) -> int:
    """Validate package inputs and create or preview a theme archive."""
    project = Project.load(Path(args.path))
    plan = package_project(project, dry_run=args.dry_run)
    output = plan.output.relative_to(project.root).as_posix()
    if args.json:
        emit_json({
            "command": "package",
            "ok": True,
            "dry_run": args.dry_run,
            "output": output,
            "file_count": len(plan.files),
            "files": [path.relative_to(project.build_dir).as_posix() for path in plan.files],
            "directories": plan.directories,
        })
        return EXIT_OK
    if args.dry_run:
        out.info(f"Would create {output} ({len(plan.files):,} files).")
        for path in plan.files:
            out.detail(f"  include {path.relative_to(project.build_dir).as_posix()}")
    else:
        out.info(f"Created {output} ({len(plan.files):,} files).")
    return EXIT_OK


def cmd_validate(args: argparse.Namespace, out: Output) -> int:
    """Validate project configuration, sources, aliases, metadata, and build output."""
    try:
        project = Project.load(Path(args.path))
        sections = validate_project(project)
    except ConfigError as exc:
        if not args.json:
            raise
        problem = Diagnostic(ERROR, "configuration", exc.message)
        emit_json({"valid": False, "errors": 1, "warnings": 0, "diagnostics": [problem.to_dict()]})
        return exc.exit_code

    diagnostics = [item for items in sections.values() for item in items]
    errors = sum(1 for item in diagnostics if item.level == ERROR)
    warnings = sum(1 for item in diagnostics if item.level == WARNING)
    if args.json:
        emit_json({"valid": errors == 0, "errors": errors, "warnings": warnings,
                   "diagnostics": [item.to_dict() for item in diagnostics]})
        return EXIT_FAILURE if errors else EXIT_OK

    out.info("Pabrikon Icon Theme Validator\n")
    for section, items in sections.items():
        symbol = "✗" if any(item.level == ERROR for item in items) else "⚠" if items else "✓"
        out.info(f"{symbol} {section}")
    print_diagnostics(out, diagnostics)
    summary = f"{errors} error{'s' * (errors != 1)}\n{warnings} warning{'s' * (warnings != 1)}"
    if errors:
        print(f"\nValidation failed:\n{summary}", file=sys.stderr)
        return EXIT_FAILURE
    out.info(f"\nValidation passed:\n{summary}")
    return EXIT_OK


def cmd_info(args: argparse.Namespace, out: Output) -> int:
    """Print project summary data as text or machine-readable JSON."""
    info = project_info(Project.load(Path(args.path)))
    if args.json:
        emit_json(info)
    else:
        for line in format_info(info):
            out.info(line)
    return EXIT_OK


def cmd_list(args: argparse.Namespace, out: Output) -> int:
    """List project icons, directories, aliases, or generated files."""
    items = list_items(Project.load(Path(args.path)), args.kind)
    if args.json:
        emit_json(items)
    else:
        for item in items:
            out.info(item)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser and register supported commands and options."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-v", "--verbose", action="store_true", default=argparse.SUPPRESS,
                        help="Show detailed output")
    common.add_argument("-q", "--quiet", action="store_true", default=argparse.SUPPRESS,
                        help="Only show errors")
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="Print machine-readable JSON output")
    common.add_argument("--debug", action="store_true", default=argparse.SUPPRESS,
                        help="Show tracebacks for unexpected errors")

    parser = argparse.ArgumentParser(
        prog="pabrikon", description="Linux icon-theme development toolkit", parents=[common]
    )
    parser.add_argument("--version", action="version", version=f"pabrikon {__version__}")
    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def add_command(name: str, help_text: str, *, path: bool = True) -> argparse.ArgumentParser:
        """Register a command with shared output options and optional project path."""
        command = commands.add_parser(name, help=help_text, description=help_text, parents=[common])
        if path:
            command.add_argument("path", nargs="?", default=".", help="Project directory (default: current)")
        return command

    init = add_command("init", "Create a new icon-theme project", path=False)
    init.add_argument("target", nargs="?", default=".", help="Directory to create or initialize (default: current)")
    init.add_argument("--name", help="Project name (default: target directory name)")
    init.set_defaults(handler=cmd_init)

    config = commands.add_parser("config", help="Manage project configuration", parents=[common])
    config_commands = config.add_subparsers(dest="config_command", required=True, metavar="ACTION")
    config_edit = config_commands.add_parser("edit", help="Open data/pabrikon.toml in a terminal editor",
                                             parents=[common])
    config_edit.add_argument("path", nargs="?", default=".", help="Project directory (default: current)")
    config_edit.add_argument("--editor", help="Editor command (default: VISUAL, EDITOR, vim, then nano)")
    config.set_defaults(handler=cmd_config_edit)

    validate = add_command("validate", "Check configuration, sources, theme metadata, aliases and build output")
    validate.set_defaults(handler=cmd_validate)

    build = add_command("build", "Render icons and assemble the theme in build/")
    build.add_argument("--all", action="store_true", help="Rebuild every output, even if it is up to date")
    build.add_argument("--size", type=int, help="Build only this size, for example 48")
    build.add_argument("--sizes", help="Build only these comma-separated sizes, for example 16,24,32")
    build.add_argument("--directory", help="Build only this icon directory, for example apps")
    build.add_argument("--icon", help="Build only this icon, by name or directory/name")
    build.add_argument("--dry-run", action="store_true", help="Show what would be built without writing files")
    build.set_defaults(handler=cmd_build)

    clean = add_command("clean", "Remove generated files from build/ (sources are never touched)")
    clean.add_argument("--type", choices=CLEAN_TYPES, default="build",
                       help="build: all of build/ (default); png/svg: generated files of that type; "
                            "symlink: alias links")
    clean.add_argument("--dry-run", action="store_true", help="List files that would be removed")
    clean.set_defaults(handler=cmd_clean)

    optimize = add_command("optimize", "Optimize SVG sources without overwriting them by default")
    optimize.add_argument("--dry-run", action="store_true", help="Show planned optimized output without writing files")
    optimize.add_argument("--in-place", action="store_true", help="Replace source SVGs after successful optimization")
    optimize.set_defaults(handler=cmd_optimize)

    package = add_command("package", "Create a deterministic tar.gz icon theme archive")
    package.add_argument("--dry-run", action="store_true", help="Validate and list package contents without writing")
    package.set_defaults(handler=cmd_package)

    aliases = commands.add_parser("aliases", help="Manage icon aliases", parents=[common])
    alias_commands = aliases.add_subparsers(dest="alias_command", required=True, metavar="ACTION")
    alias_edit = alias_commands.add_parser("edit", help="Open data/aliases.toml in a terminal editor",
                                           parents=[common])
    alias_edit.add_argument("path", nargs="?", default=".", help="Project directory (default: current)")
    alias_edit.add_argument("--editor", help="Editor command (default: VISUAL, EDITOR, vim, then nano)")
    alias_build = alias_commands.add_parser("build", help="Create alias symlinks in build/ from data/aliases.toml",
                                            parents=[common])
    alias_build.add_argument("path", nargs="?", default=".", help="Project directory (default: current)")
    alias_build.add_argument("--dry-run", action="store_true", help="Show changes without modifying build/")
    aliases.set_defaults(handler=cmd_aliases)

    info = add_command("info", "Show project summary")
    info.set_defaults(handler=cmd_info)

    list_command = commands.add_parser("list", help="List icons, directories, aliases or generated files",
                                       parents=[common])
    list_command.add_argument("kind", nargs="?", choices=LIST_KINDS, default="icons")
    list_command.add_argument("path", nargs="?", default=".", help="Project directory (default: current)")
    list_command.set_defaults(handler=cmd_list)

    theme = commands.add_parser("theme", help="Manage index.theme metadata", parents=[common])
    theme_commands = theme.add_subparsers(dest="theme_command", required=True, metavar="ACTION")
    theme_init = theme_commands.add_parser("init", help=f"Write index.theme from {CONFIG_FILE}", parents=[common])
    theme_init.add_argument("--force", action="store_true", help="Overwrite an existing index.theme")
    theme_commands.add_parser("show", help="Print the effective index.theme", parents=[common])
    theme_edit = theme_commands.add_parser("edit", help="Open index.theme in a terminal editor", parents=[common])
    theme_edit.add_argument("--editor", help="Editor command (default: VISUAL, EDITOR, vim, then nano)")
    theme_commands.add_parser("validate", help=f"Check index.theme against {CONFIG_FILE}", parents=[common])
    for action in theme_commands.choices.values():
        action.add_argument("path", nargs="?", default=".", help="Project directory (default: current)")
    theme.set_defaults(handler=cmd_theme)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run the selected command, and return its documented exit code."""
    parser = build_parser()
    argcomplete.autocomplete(parser)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits for --help, --version and usage errors
        return int(exc.code or 0)

    args.json = getattr(args, "json", False)
    out = Output(verbose=getattr(args, "verbose", False), quiet=getattr(args, "quiet", False))
    try:
        return args.handler(args, out)
    except PabrikonError as exc:
        if args.json:
            json_error(args, exc.message, exc.hint)
        else:
            out.error(exc.message, exc.hint)
        return exc.exit_code
    except OSError as exc:
        if getattr(args, "debug", False):
            raise
        location = f": {exc.filename}" if exc.filename else ""
        message = f"{exc.strerror or exc}{location}"
        hint = "Check that the path exists and you have permission to access it."
        if args.json:
            json_error(args, message, hint)
        else:
            out.error(message, hint)
        return EXIT_FAILURE
    except Exception as exc:
        if getattr(args, "debug", False):
            raise
        message = f"unexpected internal error: {exc!r}"
        hint = "Re-run with --debug to see the traceback and report it as a bug."
        if args.json:
            json_error(args, message, hint)
        else:
            out.error(message, hint)
        return EXIT_FAILURE
