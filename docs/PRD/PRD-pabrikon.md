# Pabrikon — Product Requirements Document

**Status:** Draft / Ready for Implementation Planning
**Project:** Pabrikon
**Repository:** https://github.com/winardiaris/pabrikon
**Target:** Linux desktop icon theme development toolkit
**Primary language:** Python 3.12+
**License:** GPL-3.0
**Document purpose:** Source of truth for human developers and AI coding agents

---

## 1. Executive Summary

Pabrikon is a Linux icon-theme development toolkit originally created to help GNU/Linux distribution artwork teams create and manage icon themes.

The original Pabrikon implementation is a Bash-based CLI utility. It provides functionality for:

* converting SVG icons into PNG icons;
* managing scalable icons;
* generating symbolic links;
* managing icon mapping through CSV files;
* creating new icon projects;
* cleaning generated files;
* optimizing SVG files;
* listing project files;
* importing project sources;
* managing icon-theme directory structures.

Pabrikon v2 is treated as a new project with a new architecture and development workflow. The legacy implementation may inform product decisions, but v2 does not need to preserve its CLI, data formats, or implementation behavior.

The long-term goal is:

> **Pabrikon is a modern CLI toolkit and build system for creating, validating, optimizing, previewing, and packaging Linux icon themes.**

Pabrikon should not merely be an SVG-to-PNG converter.

It should become a reproducible build and development workflow for Linux icon-theme projects.

---

# 2. Problem Statement

Creating and maintaining Linux icon themes involves repetitive tasks:

1. Maintaining SVG source files.
2. Generating raster versions at multiple sizes.
3. Maintaining Linux icon-theme directory structures.
4. Managing symbolic icon aliases.
5. Maintaining `index.theme`.
6. Validating icon names and directories.
7. Optimizing SVG files.
8. Detecting broken links and missing assets.
9. Previewing icon themes.
10. Packaging themes for distribution.

These tasks are often performed manually or through project-specific scripts.

Pabrikon should provide one consistent developer workflow.

Example:

```bash
pabrikon init my-theme
cd my-theme

pabrikon build
pabrikon validate
pabrikon optimize
pabrikon preview
pabrikon package
```

---

# 3. Product Vision

## 3.1 Vision

Make Linux icon-theme development feel similar to a modern software build system.

A developer should be able to:

```text
source icons
    ↓
configure theme
    ↓
build
    ↓
validate
    ↓
optimize
    ↓
preview
    ↓
package
```

without manually managing generated files.

---

# 4. Goals

## 4.1 Primary Goals

Pabrikon must:

* provide a modern Python CLI;
* support Linux icon-theme development workflows;
* provide the icon-theme workflows selected for Pabrikon v2, regardless of whether they existed in the legacy implementation;
* convert scalable SVG assets into raster icon sizes;
* manage icon aliases/symbolic links;
* validate icon-theme projects;
* optimize SVG assets;
* generate/manage `index.theme`;
* provide project configuration;
* adopt existing local or explicitly selected remote icon-theme projects by generating `data/pabrikon.toml` and normalizing recognized icon assets into the configured v2 layout;
* provide useful CLI output;
* provide deterministic builds;
* provide automated tests;
* support CI;
* provide packaging/export functionality;
* be usable by humans and AI coding agents.

---

## 4.2 Secondary Goals

Future versions may provide:

* local browser-based preview;
* icon search;
* visual icon browser;
* graphical editor integration;
* theme comparison;
* icon coverage reports;
* package publishing;
* distro-specific packaging;
* plugin architecture.

---

# 5. Non-Goals

The following are explicitly outside the initial scope:

### 5.1 Full graphical editor

Pabrikon should not initially become an SVG editor.

Users can continue using tools such as:

* Inkscape
* Illustrator
* Figma
* other SVG editors

Pabrikon manages the build/development workflow.

### 5.2 Replacing Linux desktop icon specifications

Pabrikon should follow existing Linux icon-theme conventions rather than inventing a new icon standard.

### 5.3 Rewriting the entire legacy project immediately

The legacy project must first be understood and mapped before code is removed.

### 5.4 Cloud service

Pabrikon is primarily a local developer tool.

### 5.5 AI-generated icons

AI image/icon generation is not part of the initial product scope.

---

# 6. Legacy Project Context

The current repository is:

```text
https://github.com/winardiaris/pabrikon
```

The legacy implementation is primarily Bash-based.

The repository currently contains:

```text
bin/
config/
data/
man/
.gitignore
.travis.yml
INSTALL
LICENSE
README.md
install.sh
```

The README describes Pabrikon as a GNU/Linux icon-management tool and identifies dependencies including `librsvg2-bin` and `svgcleaner`.

The existing project supports icon directories including:

```text
actions/scalable/
animations/scalable/
apps/scalable/
categories/scalable/
devices/scalable/
emblems/scalable/
io/scalable/
mimetypes/scalable/
places/scalable/
status/scalable/
stock/scalable/
```

and:

```text
data/
```

for CSV-based symlink information.

Legacy CLI functionality includes concepts such as:

```text
--build
--clean
--makesvg
--makepng
--makesym
--makecsv
--newproject
--new
--list
--opencsv
--minizer
--vaccum
--update
--verbose
```

The legacy README also describes future GUI functionality.

Source:

https://github.com/winardiaris/pabrikon

---

# 7. Legacy Implementation as Product Reference

Pabrikon v2 is a new project, not a compatibility migration. Inspect legacy code or data only when it helps clarify a product decision or a behavior worth adopting.

When using the legacy repository as a reference, the implementation agent may:

1. inspect relevant scripts, configuration, data, or generated output;
2. determine whether the behavior is useful to the v2 product;
3. implement it according to v2 requirements when selected.

There is no requirement to preserve legacy behavior, keep legacy files executable, or document a migration mapping. Existing third-party icon-theme adoption is a separate v2 feature and is not a migration from legacy Pabrikon.

---

# 8. Target Architecture

Pabrikon should use a modern Python package structure.

Recommended structure:

```text
pabrikon/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── docs/
│   ├── architecture.md
│   ├── configuration.md
│   ├── icon-themes.md
│   └── commands/
├── src/
│   └── pabrikon/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── icon.py
│       │   ├── theme.py
│       │   └── project.py
│       ├── services/
│       │   ├── builder.py
│       │   ├── validator.py
│       │   ├── optimizer.py
│       │   ├── aliases.py
│       │   ├── theme.py
│       │   ├── preview.py
│       │   └── packager.py
│       ├── adapters/
│       │   ├── librsvg.py
│       │   ├── svgcleaner.py
│       │   └── filesystem.py
│       └── utils/
│           ├── logging.py
│           ├── paths.py
│           └── subprocess.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── examples/
```

This structure is a recommendation, not an absolute requirement.

The implementation agent may change the structure if there is a documented technical reason.

---

# 9. Technology Requirements

## 9.1 Python

Minimum:

```text
Python 3.12+
```

The project should use modern Python features.

Preferred:

* type hints;
* `pathlib`;
* dataclasses or Pydantic where appropriate;
* structured exceptions;
* context managers;
* modern packaging.

---

## 9.2 CLI

Recommended:

```text
Typer
```

Alternative CLI libraries may be used if technically justified.

CLI output should use:

```text
Rich
```

or equivalent.

---

## 9.3 Testing

Recommended:

```text
pytest
```

The project must have automated tests.

---

## 9.4 Packaging

Use:

```text
pyproject.toml
```

The project must be installable using standard Python packaging workflows.

Example:

```bash
pip install .
```

and preferably:

```bash
pipx install pabrikon
```

---

# 10. Project Configuration

Pabrikon should support a project configuration file.

Preferred format:

```text
data/pabrikon.toml
```

Keep this project configuration in `data/` alongside `aliases.toml`.
The project loader must use this canonical path. If only a root-level
`pabrikon.toml` is present, report the required move and do not silently create
a second configuration file.

Provide `pabrikon config edit [PATH] [--editor EDITOR]` to open an existing
`data/pabrikon.toml` in a terminal editor. Use the shared editor selection
(`--editor`, `$VISUAL`, `$EDITOR`, `vim`, then `nano`) and invoke it without a
shell. Do not parse the TOML before opening, so users can repair malformed
configuration. If the file is missing, report that `pabrikon init` creates it.

Example:

```toml
[project]
name = "my-theme"
version = "1.0.0"
description = "My Linux icon theme"
license = "GPL-3.0"

[theme]
name = "My Theme"
comment = "Custom Linux icon theme"
inherits = ["Adwaita"]

[build]
sizes = [16, 22, 24, 32, 48, 64, 128, 256]
formats = ["svg", "png"]

[build.directories]
enabled = [
    "actions",
    "apps",
    "categories",
    "devices",
    "emblems",
    "mimetypes",
    "places",
    "status"
]

[optimization]
enabled = true

[validation]
strict = false
```

The exact schema may evolve.

---

# 11. Core CLI

The primary CLI should use subcommands.

## 11.1 Init

```bash
pabrikon init my-theme
```

Creates a new project.

Recommended layout after adding an SVG and running a build:

```text
my-theme/
├── README.md
├── index.theme
├── icons/                         # Editable source assets only
│   ├── actions/
│   │   └── scalable/
│   ├── apps/
│   │   └── scalable/
│   │       └── accessories-calculator.svg  # Example source added by user
│   ├── categories/
│   │   └── scalable/
│   ├── devices/
│   │   └── scalable/
│   ├── places/
│   │   └── scalable/
│   └── status/
│       └── scalable/
├── data/
│   ├── pabrikon.toml              # Project and build configuration
│   └── aliases.toml               # Optional alias definitions
├── build/                         # Created by first build; safe to recreate
│   ├── index.theme
│   └── apps/
│       ├── scalable/
│       │   └── accessories-calculator.svg
│       └── 48x48/
│           └── accessories-calculator.png
└── dist/                          # Package archives only
```

This is the recommended v2 layout after a source icon has been added and a
build has run. `icons/` is the authoritative source tree, organized by icon
context with scalable SVG sources under `<context>/scalable/`. Enabled
contexts are declared in `build.directories.enabled`; initialization creates each enabled context and
its `scalable/` source directory. Pabrikon writes generated SVG/PNG variants
and a build-ready `index.theme` under `build/`. Generated output must not be
mixed into `icons/`. `data/aliases.toml` is optional and `dist/` stays empty
until packaging is requested. Files belonging to the theme's license or
upstream project remain at the project root and are preserved.

Acceptance criteria:

* project is created successfully;
* configuration file exists;
* the recommended source directories exist for configured contexts;
* generated output is isolated under `build/` after a build and can be recreated without changing source assets;
* project can immediately run `pabrikon validate`.

## 11.2 Adopt an existing icon project

Pabrikon must support adding v2 project configuration to an existing icon-theme repository, including repositories whose theme root is nested below the Git repository root. This project-adoption workflow is distinct from creating a blank project. It does not import legacy Pabrikon alias CSV files.

Proposed CLI:

```bash
# Inspect the current checkout and preview the generated config and file copies.
pabrikon init --from . --dry-run

# Apply the reviewed config and copy recognized SVGs into the v2 layout.
pabrikon init --from . --apply

# Explicitly clone and adopt a remote repository into a target directory.
pabrikon init --from https://github.com/BlankOn/tebu-flat.git \\
    --target ./tebu-flat --ref master --dry-run
```

When adopting a project, Pabrikon must:

* accept a local directory or an explicitly supplied Git URL; never fetch or clone a remote project implicitly;
* locate the icon-theme root by inspecting project metadata and icon directories, including nested roots; report ambiguity when more than one candidate theme root is found;
* inspect `index.theme`, recognized context/size directories, SVG and raster assets, and symbolic links to infer a proposed `data/pabrikon.toml`;
* detect safe icon-file symbolic links that represent aliases and propose corresponding entries in `data/aliases.toml`;
* derive only values supported by repository evidence. Show defaults or request user input for unknown project metadata instead of inventing it;
* produce a dry-run report containing the proposed TOML, detected theme root, recognized and ignored paths, and every planned copy or directory creation;
* on explicit apply, copy recognized assets to the configured v2 source layout (`icons/<context>/scalable/` for SVG source icons), creating required directories from `build.directories.enabled` while retaining upstream source files;
* on explicit apply, write the reviewed alias entries to `data/aliases.toml` when safe aliases were detected;
* preserve source assets and unrecognized files; never silently delete or overwrite them;
* report source assets that collide in the v2 layout, skip every colliding source and any alias targeting an ambiguous icon, and continue applying unambiguous assets; refuse unsafe write paths;
* refuse to overwrite an existing `data/pabrikon.toml` unless the user explicitly requests regeneration; retain a backup when regenerating it.

For symbolic-link aliases, use the link filename without its extension as the alias key. Resolve relative targets within the selected theme root and map them to canonical `context/name` targets, omitting the context when the target is in the same context. Preserve upstream links and source files. Import only links whose targets resolve to recognized, unambiguous adopted icon assets. Report broken links, links escaping the theme root, directory links, unsupported targets, cycles, and collisions with canonical icon names for manual review; do not turn them into aliases. The dry-run report must show every proposed alias and skipped link. If `data/aliases.toml` already exists, do not overwrite it; report the conflict and retain proposed aliases for review. Do not infer aliases from links that merely deduplicate size-specific assets or would collapse distinct variants to one Pabrikon source name.

The initial supported normalization should map clearly recognizable Linux icon-theme layouts using `index.theme` and context/size directory names. It must not guess the meaning of arbitrary directories. Files that cannot be mapped safely remain untouched and are listed in the report for manual review.

### Tebu-Flat adoption example

The public [BlankOn/tebu-flat repository](https://github.com/BlankOn/tebu-flat) has a `Tebu-Flat/` subdirectory at repository root and a `.gitmodules` file. The adopter must therefore search for the theme root instead of assuming the Git root is the icon-theme root, and it must report submodule contents separately. Submodules must not be initialized or fetched unless the user explicitly requests it. File-level layout mapping for this repository remains an acceptance-fixture task and must be confirmed against a checkout before compatibility is claimed.

### Additional adoption examples

Use these public repositories as further acceptance fixtures for projects with different layouts:

* [rudrab/Shadow](https://github.com/rudrab/Shadow) stores size directories such as `16x16/`, `22x22/`, and `128x128/` alongside `scalable/` at the repository root. It also contains several desktop-specific `index.theme` variants. Adoption must identify the actual theme root and report which metadata file it selects; it must not silently merge the alternate metadata files.
* [cbrnix/Newaita](https://github.com/cbrnix/Newaita) contains separate `Newaita/` and `Newaita-dark/` theme roots. Each root contains icon contexts and additional theme files, including variant-generation scripts and a bundled icon-theme cache. Adoption must identify multiple candidate roots and let the user select one, while preserving scripts and other unrecognized files. Its README identifies the theme as CC BY-NC-SA 3.0, so adoption reports must preserve the repository's license files and metadata rather than replacing them with a default license.
* [tinuxongit/citropy-kde-theme](https://github.com/tinuxongit/citropy-kde-theme/tree/main/icons/Citropy) has a nested `icons/Citropy/` theme root. Its `index.theme` declares context directories such as `apps`, `places`, and `devices` directly as scalable, without a `scalable/` path component. Adoption must use declared directory metadata to map these vectors.
* [KDE/breeze-icons](https://github.com/KDE/breeze-icons) keeps source icons under `icons/<context>/<size>/`; its theme index is assembled during the CMake build from `breeze.theme.in` and `commonthemeinfo.theme.in`. The metadata declares fixed-size and scalable size directories, as well as `ScaledDirectories` entries such as `apps/22@2x`. Adoption must distinguish these variants and account for the generated theme root rather than assuming a checked-out source tree already has `index.theme`.

These examples are acceptance-fixture candidates, not a claim of verified compatibility. Confirm their current layouts and expected mappings from pinned checkouts before marking adoption support complete.

---

# 12. Build

Command:

```bash
pabrikon build
```

Purpose:

Generate required icon variants from source SVG files.

Example:

```text
icons/apps/scalable/firefox.svg
```

may generate:

```text
build/apps/16x16/firefox.png
build/apps/22x22/firefox.png
build/apps/24x24/firefox.png
build/apps/32x32/firefox.png
build/apps/48x48/firefox.png
build/apps/64x64/firefox.png
build/apps/128x128/firefox.png
build/apps/256x256/firefox.png
```

The exact output directory structure must be defined before implementation.

---

## 12.1 Build options

Example:

```bash
pabrikon build --all
pabrikon build --size 48
pabrikon build --sizes 16,24,32,48
pabrikon build --directory apps
pabrikon build --icon firefox
```

---

## 12.2 Incremental build

Pabrikon should avoid rebuilding unchanged files where possible.

Example:

```text
3 icons changed
1,281 icons unchanged
```

A future build cache may be introduced.

---

# 13. Clean

Command:

```bash
pabrikon clean
```

Purpose:

Remove generated artifacts.

Supported:

```bash
pabrikon clean
pabrikon clean --type png
pabrikon clean --type symlink
pabrikon clean --type build
```

Safety requirement:

The clean operation must never delete source SVG files unless the user explicitly requests it.

---

# 14. Optimize

Command:

```bash
pabrikon optimize
```

Purpose:

Optimize SVG assets while preserving their visual output.

Example output:

```text
Optimizing icons...

apps/firefox.svg
42 KB → 17 KB (-59%)

apps/chrome.svg
38 KB → 15 KB (-60%)

Total:
102 KB → 43 KB
Saved: 59 KB
```

Requirements:

* preserve valid SVG;
* preserve viewBox;
* avoid destructive transformations by default;
* provide dry-run mode;
* report size changes.

Example:

```bash
pabrikon optimize --dry-run
```

---

# 15. Validate

Command:

```bash
pabrikon validate
```

This is a core feature.

Validation should detect:

### Project errors

* missing configuration;
* invalid configuration;
* missing directories;
* invalid file names.

### SVG errors

* invalid XML;
* invalid SVG;
* missing viewBox;
* unsupported structure where relevant.

### Theme errors

* missing `index.theme`;
* invalid theme metadata;
* invalid directory declarations.

### Icon errors

* duplicate icon names;
* missing expected sizes;
* broken aliases;
* invalid symbolic links;
* orphaned files.

Example:

```text
Pabrikon Icon Theme Validator

✓ Configuration
✓ Theme metadata
✓ SVG files
✓ Icon directories

Warnings:

⚠ apps/firefox.svg
  Missing raster size: 16x16

⚠ places/home.svg
  Alias target does not exist

Errors:

✗ mimetypes/application-pdf.svg
  Invalid SVG XML

Validation failed:
1 error
2 warnings
```

Exit codes must be machine-readable.

Suggested:

```text
0 = valid
1 = validation error
2 = invalid CLI/configuration
```

---

# 16. Symbolic Links and Aliases

Legacy Pabrikon uses CSV files to manage icon symlink data.

Pabrikon should support a structured alias configuration.

Possible format:

```toml
[aliases]
"folder-home" = "user-home"
"computer" = "computer-symbolic"
"application-x-executable" = "application-x-executable-symbolic"
```

Command:

```bash
pabrikon aliases edit
pabrikon aliases build
```

The edit command should open `data/aliases.toml` in the terminal editor chosen
by `--editor`, `$VISUAL`, `$EDITOR`, or an available `vim` or `nano`. When the
file is missing, create it with a commented example template without
overwriting existing content. Invoke editors with an argument array rather
than through a shell, and report missing editors or nonzero exits clearly.

Expected behavior:

* create aliases;
* validate targets;
* detect cycles;
* detect missing targets;
* avoid broken links;
* report generated aliases.

---

# 17. Legacy CSV Alias Format

Legacy CSV alias tables are superseded by `data/aliases.toml`. Pabrikon v2
uses TOML as the canonical alias configuration and generates relative links
for the configured scalable and raster outputs. The repository no longer
bundles the legacy CSV tables or the commands that created and consumed them.

An importer for CSV files supplied by an existing external project is not part
of the current scope. Users should declare aliases in `data/aliases.toml`;
Pabrikon must not claim that arbitrary legacy CSV files can be imported.

---

# 18. Theme Metadata

Pabrikon should understand and manage Linux icon-theme metadata.

Primary file:

```text
index.theme
```

The tool should support:

```bash
pabrikon theme init
pabrikon theme validate
pabrikon theme show
pabrikon theme edit
```

Potential configuration:

```toml
[theme]
name = "My Theme"
comment = "My Linux icon theme"
inherits = ["Adwaita"]
```

Pabrikon should generate or validate the corresponding `index.theme`.
The edit command should open the project root's `index.theme` in a terminal
editor selected by `--editor`, `$VISUAL`, `$EDITOR`, or an available `vim` or
`nano`. If the file is missing, it should be generated from `data/pabrikon.toml`
before the editor starts, without overwriting an existing file. Editor commands
must run without shell interpolation and report failures with an actionable
message.

### 18.1 Freedesktop Icon Theme 0.10 coverage

Pabrikon must document its supported subset of the [Freedesktop Icon Theme
Specification 0.10](https://specifications.freedesktop.org/icon-theme/0.10/).
The current implementation covers basic theme metadata and builds SVG/PNG
assets; it is not a complete implementation of the specification. These are
known gaps and future requirements, not claims about current behavior:

* [ ] Support the standard theme header fields `Hidden` and `Example`, plus
  localized `Name` and `Comment` values, in configuration, generation, and
  validation.
* [ ] Support the full per-directory metadata model: `Size`, `Context`, and
  `Type` (`Fixed`, `Scalable`, or `Threshold`), including relevant
  `MinSize`, `MaxSize`, and `Threshold` validation and generation.
* [ ] Review supported contexts against the specification and icon naming
  conventions. Define explicit mappings for filesystem-related contexts and
  other contexts instead of relying on title-casing unknown directory names.
* [ ] Support XPM assets if there is a concrete compatibility need. The
  specification lists PNG, XPM, and SVG; XPM is legacy and is not recommended
  for new themes.
* [ ] Decide whether to support per-icon `.icon` metadata files, including
  `DisplayName`, `EmbeddedTextRectangle`, and `AttachPoints`.
* [~] Use `Scale` declared in an adopted `index.theme` to preserve directory
  paths and render PNG pixels at the declared scale. Standalone scale
  configuration and compatibility fixtures for conventions such as
  `22x22@2x` remain open. This is separate from specification 0.10, which does
  not define a `Scale` key.
* [ ] Add compatibility fixtures and validation tests for supported metadata,
  output directories, SVG/PNG assets, and any adopted extensions.

Runtime icon lookup, desktop theme installation, cache handling, and fallback
search through inherited themes are responsibilities of desktop/toolkit
implementations in the specification and are not initially Pabrikon
requirements. Pabrikon may add optional inspection or packaging integrations
later, but must not claim to implement desktop icon lookup merely because it
writes `Inherits` into `index.theme`.

---

# 19. List / Inspect

Command:

```bash
pabrikon list
```

Examples:

```bash
pabrikon list icons
pabrikon list directories
pabrikon list aliases
pabrikon list generated
```

Output should be human-readable.

Machine-readable output should be considered:

```bash
pabrikon list --json
```

---

# 20. Project Information

Command:

```bash
pabrikon info
```

Example:

```text
Project: My Theme
Version: 1.0.0

Icons:
  SVG:       1,284
  PNG:       8,742
  Aliases:     328

Directories:
  apps
  actions
  places
  devices
  status

Build:
  Last build: 2026-10-03 15:30
```

---

# 21. Preview

Preview is a Phase 2/3 feature.

Command:

```bash
pabrikon preview
```

Expected behavior:

Start a local preview server.

Example:

```text
Pabrikon Preview
http://localhost:8765
```

The UI should allow:

* browse icon categories;
* search icons;
* inspect icon names;
* preview different sizes;
* inspect aliases;
* compare SVG/raster output.

The preview server should not require external network access.

---

# 22. Package

Command:

```bash
pabrikon package
```

Primary goal:

Create distributable icon-theme archives.

Example:

```text
dist/
└── my-theme-1.0.0.tar.gz
```

Potential formats:

```text
tar.gz
zip
```

Future:

```text
deb
rpm
```

Distro-specific packages are not part of MVP.

---

# 23. Dry Run

Destructive or large operations should support:

```bash
--dry-run
```

Example:

```bash
pabrikon clean --dry-run
pabrikon optimize --dry-run
pabrikon aliases build --dry-run
```

Output should clearly show intended actions without modifying files.

---

# 24. Verbose and Quiet Modes

Support:

```bash
-v
--verbose
```

and preferably:

```bash
-q
--quiet
```

The CLI should provide:

* human-readable default output;
* additional per-file operation details in verbose mode where available;
* no routine text in quiet mode, while keeping errors visible on standard error;
* proper exit codes.

---

# 25. JSON Output

Commands intended for automation support:

```bash
--json
```

Example:

```bash
pabrikon validate --json
```

The flag is accepted by every current command, including nested commands. Each
successful command emits one JSON value on standard output; command failures
emit a JSON error object and preserve the corresponding nonzero exit code.
JSON output takes precedence over quiet mode. Existing command-specific
success payloads are retained, including the validator's `valid`, `errors`,
`warnings`, and `diagnostics` fields.

Output:

```json
{
  "valid": false,
  "errors": 1,
  "warnings": 2
}
```

This is particularly important for CI and AI agents.

---

# 26. Error Handling

Errors must be actionable.

Bad:

```text
Error occurred.
```

Good:

```text
Error: icon source not found

Expected:
    icons/apps/scalable/firefox.svg

Hint:
    Run `pabrikon list icons`
```

Avoid leaking Python stack traces during normal CLI operation.

Stack traces may be enabled with:

```bash
--debug
```

---

# 27. External Tools

The legacy project depends on external tools such as:

```text
librsvg2-bin
svgcleaner
```

Pabrikon must clearly define external dependencies.

External commands should be wrapped through adapters.

Example:

```python
class SvgRenderer:
    def render(...):
        ...
```

rather than scattering `subprocess` calls throughout business logic.

This makes testing and future replacement easier.

---

# 28. Deterministic Builds

Given the same:

```text
source files
configuration
tool versions
```

Pabrikon should produce equivalent output.

Avoid:

* timestamps embedded into generated files;
* random filenames;
* non-deterministic ordering;
* machine-specific paths.

---

# 29. Performance

The tool should support large icon collections.

The implementation should avoid:

* repeatedly scanning the entire project;
* unnecessary SVG parsing;
* rebuilding unchanged assets;
* spawning excessive subprocesses.

Parallel build may be introduced after correctness is established.

Do not optimize prematurely.

---

# 30. Security Requirements

Pabrikon operates on local files.

Important requirements:

* do not execute arbitrary project files;
* validate paths;
* prevent path traversal;
* avoid shell string interpolation;
* use safe subprocess argument arrays;
* do not require root privileges for normal operations;
* do not download remote code automatically.

Remote source adoption is allowed only as an explicit user command. The user must choose the repository URL, target path, and (where relevant) ref. Do not execute scripts, hooks, or build instructions found in an adopted repository. Submodules are not fetched implicitly. Preview all local file changes before applying them.

---

# 31. New Project Boundary

Pabrikon v2 is a standalone project. It does not promise compatibility with legacy Pabrikon command syntax, configuration, CSV data, generated files, or installation paths. It does not require a migration guide or legacy-to-v2 command matrix.

Pabrikon's existing-project adoption feature applies to third-party icon-theme repositories. It analyzes their icon-theme metadata and assets; it is not a migration path for old Pabrikon projects.

---

# 32. Development Approach

Develop Pabrikon v2 in coherent, testable increments against the requirements in this PRD. The legacy implementation is optional reference material, not a parallel implementation or a compatibility target. Existing-project adoption is a separate feature for importing third-party icon-theme projects into the v2 layout.

---

# 33. MVP Definition

## Current implementation status (2026-10-17)

This status was checked against the current source tree, CLI, tests, CI
configuration, and documentation. It describes repository evidence, not release
approval:

**Release review (task 22): NOT READY for a stable v2 MVP release.** All
Required items have implementation or workflow evidence except existing-project
adoption. This feature is a Required MVP item and matches the planned workflow
for preparing third-party icon-theme repositories. A pre-release may be made
with this limitation stated, but it does not satisfy the current stable MVP
scope. Folder-layout references reviewed for adoption are listed under task 7a.

* `[x]` Implemented, with corresponding code and reasonable test or workflow evidence.
* `[~]` Partially implemented; the note identifies the remaining work.
* `[ ]` Not implemented, incomplete, or not verified in the repository.

The step-by-step checklist in Section 46 is the detailed status list. Items
that are absent from the current code remain unchecked even when described as
goals elsewhere in this PRD.

An Indonesian summary is maintained in [STATUS-IMPLEMENTASI.md](STATUS-IMPLEMENTASI.md).

Pabrikon MVP consists of:

### Required

* [x] Python 3.12+ package
* [x] `pyproject.toml`
* [x] CLI
* [x] `pabrikon init`
* [x] `pabrikon build`
* [x] `pabrikon clean`
* [x] `pabrikon validate`
* [x] `pabrikon optimize`
* [x] alias management
* [x] `data/pabrikon.toml`
* [ ] existing-project adoption: infer `data/pabrikon.toml` from local or explicitly cloned icon-theme sources, then safely normalize recognized assets to the configured v2 layout;
* [x] basic `index.theme` support (advanced specification coverage remains open; see Section 18.1)
* [x] unit tests
* [x] end-to-end acceptance test for the installed wheel and complete theme workflow
* [x] GitHub Actions
* [x] user documentation for the current v2 interface, manual existing-theme preparation, and end-to-end workflow

### Not required for MVP

* [ ] browser preview
* [ ] GUI
* [ ] Debian package
* [ ] RPM package
* [ ] remote project hosting or automatic background synchronization (explicit one-time Git clone for project adoption is in scope)
* [ ] icon editor
* [ ] AI icon generation

---

# 34. CLI UX Principles

Pabrikon CLI should be:

### Predictable

Users should be able to infer commands.

```bash
pabrikon build
pabrikon clean
pabrikon validate
pabrikon optimize
```

### Safe

Destructive operations should explain what they will do.

### Scriptable

Every important command should return meaningful exit codes.

### Human-readable

Output should be understandable without documentation.

### Machine-readable

Important commands should eventually support JSON.

---

# 35. Testing Strategy

## Unit tests

Test:

* configuration parsing;
* path handling;
* icon models;
* theme models;
* aliases;
* validators;
* build planning;
* command argument parsing.

## Integration tests

Test:

```text
project
  ↓
build
  ↓
generated assets
```

Test real SVG files.

## CLI tests

Test:

```bash
pabrikon init
pabrikon build
pabrikon validate
pabrikon clean
```

## Regression tests

Every discovered legacy bug should become a regression test.

---

# 36. CI/CD

GitHub Actions should run:

```text
lint
↓
type check
↓
unit tests
↓
integration tests
↓
build package
```

Potential tools:

```text
ruff
mypy / pyright
pytest
build
```

Exact tool selection can be decided during implementation.

---

# 37. Code Quality

Preferred characteristics:

* small modules;
* explicit interfaces;
* strong typing;
* dependency injection where useful;
* no global mutable state;
* testable services;
* minimal subprocess usage;
* clear exceptions;
* clear separation between CLI and business logic.

Avoid:

```python
# giant CLI function
# hundreds of lines of shell command handling
# hidden global state
# direct filesystem manipulation everywhere
```

---

# 38. Architecture Principle

The CLI should be a thin layer.

Preferred:

```text
CLI
 │
 ▼
Application Service
 │
 ├── Builder
 ├── Validator
 ├── Optimizer
 ├── Alias Manager
 ├── Theme Manager
 └── Packager
 │
 ▼
Adapters
 │
 ├── Filesystem
 ├── SVG Renderer
 └── External Tools
```

Not:

```text
CLI
 └── everything
```

---

# 39. AI Coding Agent Instructions

This section is mandatory for AI agents working on Pabrikon.

## 39.1 First step

Before modifying code:

```text
READ THE REPOSITORY.
```

Do not assume the implementation from this PRD matches the current code.

---

## 39.2 Required initial analysis

Create or update:

```text
docs/legacy-analysis.md
```

Document:

* repository structure;
* executable scripts;
* dependencies;
* CLI commands;
* data files;
* CSV formats;
* generated output;
* installation process;
* known limitations.

---

## 39.3 Treat v2 as a standalone implementation

The legacy implementation is not required to remain executable alongside v2. Keep legacy files only when they serve a concrete v2 purpose, such as reference material or selected test data.

---

## 39.4 Do not invent requirements

If behavior is unclear:

1. inspect source;
2. inspect documentation;
3. inspect tests;
4. inspect git history;
5. identify ambiguity;
6. document the assumption.

Do not silently invent user-facing behavior when the v2 requirements or input project evidence are unclear.

---

## 39.5 One feature at a time

Each implementation task should:

1. explain the change;
2. implement it;
3. add/update tests;
4. run tests;
5. update documentation;
6. report remaining issues.

---

## 39.6 Never skip tests

A feature is not complete if:

```text
code exists
```

but:

```text
tests do not exist
```

unless the change is purely documentation/configuration.

---

# 40. Definition of Done

A feature is considered complete only when:

* implementation exists;
* unit tests exist where applicable;
* integration tests exist where applicable;
* CLI behavior is documented;
* errors are handled;
* exit codes are defined;
* existing functionality is not unintentionally broken;
* lint/type checks pass;
* tests pass;
* documentation is updated.

---

# 41. Suggested Initial GitHub Issues

## Epic 1 — Pabrikon Foundation

### Issue #1

**Repository archaeology and legacy analysis**

Deliver:

```text
docs/legacy-analysis.md
```

### Issue #2

**Create Python packaging foundation**

Deliver:

```text
pyproject.toml
src/pabrikon/
tests/
```

### Issue #3

**Implement modern CLI foundation**

Deliver:

```bash
pabrikon --help
pabrikon --version
```

---

## Epic 2 — Project Management

### Issue #4

```bash
pabrikon init
```

### Issue #5

```text
data/pabrikon.toml
```

### Issue #6

```bash
pabrikon info
```

---

## Epic 3 — Build System

### Issue #7

```bash
pabrikon build
```

### Issue #8

Incremental build.

### Issue #9

Build size configuration.

---

## Epic 4 — Validation

### Issue #10

```bash
pabrikon validate
```

### Issue #11

SVG validation.

### Issue #12

Theme validation.

### Issue #13

Alias validation.

---

## Epic 5 — Optimization

### Issue #14

```bash
pabrikon optimize
```

### Issue #15

Optimization dry-run.

---

## Epic 6 — Alias System

### Issue #16

Alias configuration.

### Issue #17

Alias generation.

### Issue #18

Importing legacy Pabrikon CSV alias files is out of scope. Configure aliases in TOML.

---

## Epic 7 — Distribution

### Issue #19

```bash
pabrikon package
```

### Issue #20

Tarball packaging.

---

## Epic 8 — Preview

### Issue #21

Local preview server.

### Issue #22

Icon browser.

### Issue #23

Icon search.

---

# 42. Future Roadmap

## Pabrikon

Modern CLI and build engine.

## Pabrikon 1.1

Validation and optimization improvements.

## Pabrikon 1.2

Preview server.

## Pabrikon 1.3

Theme comparison and coverage reports.

## Pabrikon 2.0

Potential GUI / desktop application.

The roadmap is intentionally flexible.

---

# 43. Example End-to-End Workflow

A new developer should eventually be able to do:

```bash
# Create project
pabrikon init my-theme

cd my-theme

# Add SVG icons
cp ~/icons/*.svg icons/apps/scalable/

# Inspect project
pabrikon info

# Validate source
pabrikon validate

# Build all configured sizes
pabrikon build

# Optimize SVG
pabrikon optimize

# Revalidate
pabrikon validate

# Preview
pabrikon preview

# Package
pabrikon package
```

Result:

```text
my-theme/
├── README.md
├── index.theme
├── icons/
│   └── apps/scalable/*.svg
├── data/
│   ├── pabrikon.toml
│   └── aliases.toml
├── build/                         # Generated by `pabrikon build`
│   ├── index.theme
│   └── apps/
│       ├── scalable/*.svg
│       └── 48x48/*.png
└── dist/
    └── my-theme-1.0.0.tar.gz
```

---

# 44. Success Metrics

Technical success:

* project installs through standard Python tooling;
* core commands work on supported Linux environments;
* required v2 workflows work as specified;
* generated icons are correct;
* validation catches known invalid states;
* builds are reproducible;
* automated tests cover core functionality.

Developer experience success:

A developer unfamiliar with the legacy Pabrikon implementation should be able to:

1. install Pabrikon;
2. create a project;
3. add SVG icons;
4. build the theme;
5. validate it;
6. package it;

using only the README and CLI help.

---

# 45. Open Questions

These questions should be answered during implementation planning rather than guessed.

## Icon sizes

Which default sizes should Pabrikon support?

Candidate:

```text
16
22
24
32
48
64
128
256
```

Should users be able to define arbitrary sizes?

---

## Directory structure

Should generated files use:

```text
apps/16x16/
```

or:

```text
16x16/apps/
```

or another Linux-standard-compatible layout?

---

## SVG rendering

Should Pabrikon depend on:

```text
librsvg
```

or use a Python-native implementation?

---

## SVG optimization

Should:

```text
svgcleaner
```

remain a dependency?

Could optimization become an adapter system?

---

## Alias format

Should the canonical configuration be:

```text
TOML
```

or:

```text
CSV
```

or another format?

Recommendation:

Use TOML for v2 project and alias configuration. Legacy CSV import/export is not required.

---

## `index.theme`

Should Pabrikon generate it automatically from `data/pabrikon.toml`?

Likely yes, but the exact mapping should be defined.

---

# 46. Step-by-Step Pabrikon Implementation Tasks

Complete these tasks in order. The legacy implementation is reference material only and does not need to remain available. Each task is complete only when its deliverables and acceptance checks are satisfied. Status markers follow Section 33.

## Phase 1 — Establish Product Scope

- [~] **1. Resolve v2 product decisions.** The repository defines sizes, layout, tools, aliases, and basic `index.theme` mapping; remaining decisions are tracked in Section 45, including broader metadata/specification coverage.

**Gate:** MVP behavior and remaining product decisions are clear enough to implement and verify.

## Phase 2 — Establish the Python Project

- [x] **4. Add the Python package foundation.** `pyproject.toml`, `src/pabrikon/`, entry points, tests, and help/version behavior are present and covered by tests.
- [x] **5. Add the CLI and configuration foundations.** Command registration, actionable errors, exit codes, TOML parsing/validation, `pabrikon config edit`, and focused tests are present.
- [x] **6. Add baseline automation and contributor documentation.** GitHub Actions runs tests, builds a wheel, and checks Ruff and mypy. `CONTRIBUTING.md` documents prerequisites, equivalent local checks, pull-request expectations, and the Linux Docker workflow; macOS development is explicitly unverified.

**Gate:** A clean checkout installs, the CLI starts, configuration errors are understandable, and CI runs the baseline checks.

## Phase 3 — Create and Describe Icon Projects

- [x] **7. Implement `pabrikon init`.** Creates starter project files/directories without overwriting existing content; initialization behavior is covered by tests.
- [~] **7a. Implement existing-project adoption.** Local and explicitly cloned remote checkouts can be scanned for a unique or selected `index.theme` root. Dry-run reports inferred config, recognized SVG copies, proposed aliases from safe SVG symlinks, preserved/ignored paths, source collisions, alternate metadata, license files, and submodules; apply retains originals, skips ambiguous sources, writes aliases only when `data/aliases.toml` is absent, and backs up config only with `--regenerate-config`. Recognized SVGs are copied to `icons/<directory-declared-in-index.theme>/`; SVG outputs preserve those relative directories, while PNG outputs are rendered into matching declared fixed-size directories. Remaining: pinned acceptance fixtures for all eight repositories, metadata generation/root preparation for Breeze, explicit alternate metadata selection, and verified handling/reporting of HiDPI, symbolic, cursor, and other symlink cases. Do not claim full adoption compatibility until these checks pass.

#### Existing-theme folder schemas reviewed for adoption

These repositories show why adoption must inspect `index.theme` and actual paths
instead of assuming one universal directory layout. The layouts below describe
the repository trees, not a promise that Pabrikon already imports them:

| Repository | Observed tree shape | Adoption case to cover |
| --- | --- | --- |
| [BlankOn/tebu-flat](https://github.com/BlankOn/tebu-flat) | The repository root contains a nested `Tebu-Flat/` theme and `.gitmodules`; icon contexts use `icons` upstream under paths such as `devices/scalable/`. | Find the nested theme root; do not fetch submodules implicitly. |
| [rudrab/Shadow](https://github.com/rudrab/Shadow) | Theme root has `scalable/`, size-first directories from `8x8/` through `256x256/`, and several alternate `index.theme_*` files alongside `index.theme`. | Select metadata explicitly and map size-first context folders without treating alternate metadata as additional themes. |
| [cbrnix/Newaita](https://github.com/cbrnix/Newaita) | Repository contains sibling theme roots `Newaita/` and `Newaita-dark/`. Each has context directories, a root `index.theme`, hidden `.places-*` variants, scripts, and an `icon-theme.cache`. | Report multiple theme roots; ignore or preserve helper files, cache, and variant directories unless the user selects them. Preserve the theme's license. |
| [snwh/paper-icon-theme](https://github.com/snwh/paper-icon-theme/tree/master/Paper) | Repository contains `Paper/` and `Paper-Mono-Dark/`; the Paper theme includes `scalable/<context>/` SVG assets as well as fixed-size theme directories described by its metadata. The repository is archived and identifies separate licensing for icon assets and scripts. | Distinguish multiple theme roots, keep scalable source SVGs separate from rendered-size assets, and preserve attribution/license files. |
| [numixproject/numix-icon-theme](https://github.com/numixproject/numix-icon-theme/tree/master/Numix) | `Numix/` contains size-first directories (`16/`, `22/`, `24/`, `32/`, `48/`, `64/`), `scalable/`, `index.theme`, and HiDPI directories such as `16@2x/` and `22@2x/`. | Recognize `@2x` as a separate scale convention; do not silently collapse it into regular sizes. |
| [GNOME/adwaita-icon-theme](https://github.com/GNOME/adwaita-icon-theme/tree/master/Adwaita) | The repository has a nested `Adwaita/` asset tree with `16x16/`, `scalable/`, `symbolic/`, and `cursors/`; the repository-level `index.theme` and `src/` are outside that asset directory. The current `Adwaita/scalable/` tree uses context folders. | Allow metadata and assets to be located at different levels; preserve symbolic/cursor assets that are outside the current Pabrikon source model. |
| [tinuxongit/citropy-kde-theme](https://github.com/tinuxongit/citropy-kde-theme/tree/main/icons/Citropy) | Nested theme root `icons/Citropy/`; `index.theme` declares direct context folders (`apps`, `places`, `devices`, `actions`, `categories`, `mimetypes`) as scalable. | Use directory declarations and each section's `Context`/`Type`; do not require a literal `scalable/` component. |
| [KDE/breeze-icons](https://github.com/KDE/breeze-icons) | Source tree is under `icons/<context>/<size>/`; CMake assembles `index.theme` from `.theme.in` files. Metadata includes `ScaledDirectories` and `@2x`/`@3x` directories alongside fixed and scalable size-qualified directories. | Treat generated metadata as a prerequisite; preserve each declared source directory and output format, using directory type and size to plan raster outputs. |

The default Pabrikon v2 source layout is `icons/<context>/scalable/`; adoption
can preserve other directory layouts declared in `index.theme`. SVG outputs
retain each source's relative directory, and raster outputs follow declared
fixed-size directories. Adoption must use a dry-run to show each source-to-target mapping and report
unsupported formats, scale variants, duplicate names, and files it will leave
untouched. Do not flatten a tree when names collide. The reference repositories
are fixtures for structure discovery; tests should not vendor icon artwork
unless its license and attribution are retained.
- [x] **8. Implement basic theme metadata support.** Generate, show, edit, and validate core `index.theme` metadata; terminal editing supports `--editor`, `$VISUAL`, `$EDITOR`, `vim`, and `nano`, and is covered by CLI tests. Full specification coverage remains open in Section 18.1.
- [x] **9. Implement `pabrikon info` and basic listing.** Project metadata, source counts, and listing commands are implemented with tests.

**Gate:** A newly initialized project can be inspected and passes initial project/theme validation. An existing project can be analyzed in dry-run mode, then adopted without losing source assets or modifying unrelated files.

## Phase 4 — Build and Maintain Assets

- [x] **10. Implement build planning.** SVG discovery, output planning, and path mapping are implemented and tested.
- [x] **11. Implement `pabrikon build`.** Rendering, build options, renderer adapter, and fixture-based build tests are present.
- [x] **12. Make builds reproducible and incremental.** Stable outputs, incremental rebuilds, forced rebuilds, and repeat-build behavior are tested.
- [x] **13. Implement safe `pabrikon clean`.** Generated-only cleanup, dry-run, filters, and source/link safety are covered by tests.

**Gate:** Build and clean work end to end on fixture projects without modifying source files unexpectedly.

## Phase 5 — Validate and Optimize

- [x] **14. Implement `pabrikon validate`.** Configuration, paths, SVG/XML, basic theme metadata, icon names, aliases, exit behavior, and diagnostics are implemented and tested. Advanced specification validation remains open.
- [x] **15. Implement `pabrikon optimize`.** Uses an optimizer adapter, writes separate optimized copies by default, supports dry-run/explicit in-place mode, and validates optimized outputs.
- [x] **16. Implement aliases.** TOML aliases, `pabrikon aliases edit`, missing-target and cycle checks, safe relative links, and dry-run behavior are implemented and tested. The edit command supports `--editor`, `$VISUAL`, `$EDITOR`, `vim`, and `nano`.
- [x] **17. Replace bundled CSV alias management with TOML.** `data/aliases.toml` is canonical, the legacy mapping tables and CSV helper commands are removed, and alias generation is covered by tests. Importing external CSV files remains out of scope.

**Gate:** Validation catches known invalid states, and optimization and alias operations are testable and safe by default.

## Phase 6 — Package and Release the MVP

- [x] **18. Implement `pabrikon package`.** Deterministic tar.gz packaging, archive contents, alias links, dry-run, and temporary-file handling are tested.
- [x] **19. Complete CLI and automation behavior.** Shared verbose/quiet/JSON options work before and after commands, JSON is available across current commands with structured errors and preserved exit codes, and focused CLI tests cover the output modes.
- [x] **20. Run end-to-end acceptance tests.** A fresh virtual environment installs the built wheel and exercises init, validate, build, optimize, package, clean, rebuild, and deterministic repackaging. CI installs librsvg and svgcleaner, and runs the acceptance suite, unit/integration/CLI tests, Ruff, mypy, and wheel-build checks.
- [x] **21. Finish user documentation.** README and the man page cover installation, configuration, commands, layout, tools, limitations, manual preparation, and the new preview/apply adoption workflow. Adoption remains partial pending broader repository fixtures and layout validation in task 7a. Legacy Pabrikon CSV alias import is out of scope.
- [~] **22. Re-review MVP completion after adoption work.** Existing-project adoption now has a first implementation, but task 7a still lacks pinned acceptance fixtures for the eight reference repositories and verified mapping for every listed layout. Stable MVP release remains unready until those checks pass. Browser preview, GUI, distro packages, advanced specification coverage, and AI icon generation remain deferred or outside MVP scope. Complete this review after task 7a is finished.

**MVP acceptance:** The end-to-end workflow succeeds from a clean checkout and required checks pass in CI. No legacy migration or compatibility documentation is required.

## After MVP

- [ ] Implement the local preview server and icon browser as a separate milestone.
- [ ] Consider coverage reports, theme comparison, distro packages, and other roadmap items only after MVP feedback and stability.

---

# 46. Initial Implementation Order

AI agents should follow this order unless the human maintainer explicitly changes it.

```text
1. Confirm v2 product requirements
        ↓
2. Select acceptance fixtures
        ↓
3. Implement and test v2 behavior
        ↓
4. Python packaging
        ↓
5. CLI foundation
        ↓
6. Project configuration
        ↓
7. Build engine
        ↓
8. Validation
        ↓
9. Optimization
        ↓
10. Alias management
        ↓
11. Packaging
        ↓
12. Preview
```

Do not jump directly to preview/GUI before the build and validation foundations are stable.

---

# 47. Final Product Definition

Pabrikon should ultimately be understood as:

> **A developer toolkit and build system for Linux icon themes.**

Its core responsibilities are:

```text
CREATE
  ↓
CONFIGURE
  ↓
BUILD
  ↓
VALIDATE
  ↓
OPTIMIZE
  ↓
PREVIEW
  ↓
PACKAGE
```

The most important principle is:

> **Pabrikon should make Linux icon-theme development reproducible, predictable, and easy to automate.**

---

# Appendix B — Agent Working Contract

When an AI coding agent receives this PRD:

```text
1. Inspect.
2. Understand.
3. Document.
4. Test.
5. Implement incrementally.
6. Verify.
7. Document.
```

Never:

```text
1. Guess.
2. Rewrite everything.
3. Delete legacy code.
4. Assume tests pass.
```

When uncertain, prefer preserving existing behavior until the intended new behavior is explicitly documented.

**End of PRD**
