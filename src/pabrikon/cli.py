from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import __version__
from .errors import EXIT_FAILURE, EXIT_OK, ConfigError, PabrikonError
from .aliases import AliasLink, apply_alias_links, load_aliases, plan_alias_links, resolve_aliases
from .build import build_project, parse_size_values
from .clean import CLEAN_TYPES, apply_clean, plan_clean
from .info import LIST_KINDS, format_info, list_items, project_info
from .optimize import optimize_project
from .package import package_project
from .project import Project, init_project
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


def cmd_init(args: argparse.Namespace, out: Output) -> int:
    """Initialize a project and report the created starter paths."""
    root, created = init_project(Path(args.target), name=args.name)
    for path in created:
        out.detail(f"created {path}")
    out.info(f"Initialized project at {root}")
    return EXIT_OK


def cmd_theme(args: argparse.Namespace, out: Output) -> int:
    """Handle theme metadata generation, display, and validation commands."""
    project = Project.load(Path(args.path))
    if args.theme_command == "init":
        if project.index_theme.exists() and not args.force:
            raise PabrikonError(
                f"{project.index_theme.name} already exists",
                hint="Use `pabrikon theme init --force` to regenerate it from pabrikon.toml.",
            )
        project.index_theme.write_text(render_index_theme(project.config), encoding="utf-8")
        out.info(f"Wrote {project.index_theme}")
        return EXIT_OK
    if args.theme_command == "show":
        if project.index_theme.is_file():
            print(project.index_theme.read_text(encoding="utf-8"), end="")
        else:
            print(render_index_theme(project.config), end="")
        return EXIT_OK
    diagnostics = validate_index_theme(project.index_theme, project.config)
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
    out.info("Planning build (dry run)...\n" if args.dry_run else "Building icon theme...\n")
    report = build_project(
        project,
        sizes=parse_size_values(args.size, args.sizes),
        directory=args.directory,
        icon=args.icon,
        rebuild_all=args.all,
        dry_run=args.dry_run,
    )
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
    project.check_build_dir()
    resolved, problems = resolve_aliases(project, load_aliases(project))
    links = plan_alias_links(project, resolved)
    if not args.dry_run:
        apply_alias_links(links)
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
    for task in report.tasks:
        source = task.source.relative_to(project.root).as_posix()
        destination = task.destination.relative_to(project.root).as_posix()
        if args.dry_run:
            out.info(f"would optimize {source} -> {destination}")
    for asset in report.completed:
        source = asset.task.source.relative_to(project.root).as_posix()
        out.info(
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
        print(json.dumps({"valid": False, "errors": 1, "warnings": 0, "diagnostics": [problem.to_dict()]}, indent=2))
        return exc.exit_code

    diagnostics = [item for items in sections.values() for item in items]
    errors = sum(1 for item in diagnostics if item.level == ERROR)
    warnings = sum(1 for item in diagnostics if item.level == WARNING)
    if args.json:
        print(json.dumps({"valid": errors == 0, "errors": errors, "warnings": warnings,
                          "diagnostics": [item.to_dict() for item in diagnostics]}, indent=2))
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
        print(json.dumps(info, indent=2))
    else:
        for line in format_info(info):
            print(line)
    return EXIT_OK


def cmd_list(args: argparse.Namespace, out: Output) -> int:
    """List project icons, directories, aliases, or generated files."""
    items = list_items(Project.load(Path(args.path)), args.kind)
    if args.json:
        print(json.dumps(items, indent=2))
    else:
        for item in items:
            print(item)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser and register supported commands and options."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-v", "--verbose", action="store_true", default=argparse.SUPPRESS,
                        help="Show detailed output")
    common.add_argument("-q", "--quiet", action="store_true", default=argparse.SUPPRESS,
                        help="Only show errors")
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

    validate = add_command("validate", "Check configuration, sources, theme metadata, aliases and build output")
    validate.add_argument("--json", action="store_true", help="Print machine-readable JSON")
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
    alias_build = alias_commands.add_parser("build", help="Create alias symlinks in build/ from data/aliases.toml",
                                            parents=[common])
    alias_build.add_argument("path", nargs="?", default=".", help="Project directory (default: current)")
    alias_build.add_argument("--dry-run", action="store_true", help="Show changes without modifying build/")
    aliases.set_defaults(handler=cmd_aliases)

    info = add_command("info", "Show project summary")
    info.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    info.set_defaults(handler=cmd_info)

    list_command = commands.add_parser("list", help="List icons, directories, aliases or generated files",
                                       parents=[common])
    list_command.add_argument("kind", nargs="?", choices=LIST_KINDS, default="icons")
    list_command.add_argument("path", nargs="?", default=".", help="Project directory (default: current)")
    list_command.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    list_command.set_defaults(handler=cmd_list)

    theme = commands.add_parser("theme", help="Manage index.theme metadata", parents=[common])
    theme_commands = theme.add_subparsers(dest="theme_command", required=True, metavar="ACTION")
    theme_init = theme_commands.add_parser("init", help="Write index.theme from pabrikon.toml", parents=[common])
    theme_init.add_argument("--force", action="store_true", help="Overwrite an existing index.theme")
    theme_commands.add_parser("show", help="Print the effective index.theme", parents=[common])
    theme_commands.add_parser("validate", help="Check index.theme against pabrikon.toml", parents=[common])
    for action in theme_commands.choices.values():
        action.add_argument("path", nargs="?", default=".", help="Project directory (default: current)")
    theme.set_defaults(handler=cmd_theme)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run the selected command, and return its documented exit code."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits for --help, --version and usage errors
        return int(exc.code or 0)

    out = Output(verbose=getattr(args, "verbose", False), quiet=getattr(args, "quiet", False))
    try:
        return args.handler(args, out)
    except PabrikonError as exc:
        out.error(exc.message, exc.hint)
        return exc.exit_code
    except OSError as exc:
        if getattr(args, "debug", False):
            raise
        location = f": {exc.filename}" if exc.filename else ""
        out.error(f"{exc.strerror or exc}{location}", "Check that the path exists and you have permission to access it.")
        return EXIT_FAILURE
    except Exception as exc:
        if getattr(args, "debug", False):
            raise
        out.error(f"unexpected internal error: {exc!r}", "Re-run with --debug to see the traceback and report it as a bug.")
        return EXIT_FAILURE
