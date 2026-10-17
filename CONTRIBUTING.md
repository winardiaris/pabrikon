# Contributing to Pabrikon

Thanks for helping improve Pabrikon. This guide covers the supported CI
environment, local checks, and the Docker development environment.

## Development requirements

Pabrikon requires Python 3.12 or newer. The full test suite also uses
`rsvg-convert` from librsvg and `svgcleaner` 0.9.5. CI currently runs on
Ubuntu with Python 3.12.

macOS development has not been verified. Docker Desktop can provide the
Linux development environment described below.

## Set up on Ubuntu

Install the system tools and create a virtual environment:

```bash
sudo apt-get update
sudo apt-get install -y build-essential cargo librsvg2-bin python3.12 python3.12-venv
svgcleaner_root="$(mktemp -d)"
cargo install svgcleaner --version 0.9.5 --locked --root "$svgcleaner_root"
export PATH="$svgcleaner_root/bin:$PATH"
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the same checks used by GitHub Actions from the repository root:

```bash
wheel_dir="$(mktemp -d)"
python -m pip wheel --no-deps . --wheel-dir "$wheel_dir"
python -m ruff check src tests
python -m mypy
PABRIKON_WHEEL_DIR="$wheel_dir" python -m pytest
```

The acceptance test installs the built wheel into a fresh virtual environment
and exercises the end-to-end CLI workflow. Build the wheel before running
pytest so the test uses that artifact, as CI does.

## Use Docker on macOS or Linux

To run the full CI checks in a Linux container, build the test image from the
repository root:

```bash
docker build -f Dockerfile.test -t pabrikon-tests .
```

Then run the same checks against the mounted checkout:

```bash
docker run --rm -v "$PWD:/workspace" -w /workspace pabrikon-tests sh -c '
  set -eu
  wheel_dir=$(mktemp -d)
  python -m pip wheel --no-deps . --wheel-dir "$wheel_dir"
  python -m ruff check src tests
  python -m mypy
  PABRIKON_WHEEL_DIR="$wheel_dir" python -m pytest
'
```

The test image includes Python 3.12, librsvg, svgcleaner, pytest, Ruff, and
mypy. Use Docker Desktop to run it on macOS.

## Pull requests

- Create a focused branch for each change.
- Add or update tests for behavior changes and bug fixes.
- Update the README or relevant docs when user-facing behavior changes.
- Run the checks above before opening a pull request.
- Include a concise summary and the checks you ran in the pull request.

GitHub Actions runs the same wheel build, Ruff, mypy, and pytest checks on
pushes and pull requests using Ubuntu and Python 3.12.
