#!/usr/bin/env bash

set -eu

fail() {
    printf 'Error: %s\n' "$1" >&2
    exit 1
}

SOURCE=${BASH_SOURCE[0]}
while [ -h "$SOURCE" ]; do
    SOURCE_DIR=$(CDPATH= cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)
    LINK=$(readlink "$SOURCE") || fail "cannot resolve installer symlink: $SOURCE"
    case $LINK in
        /*) SOURCE=$LINK ;;
        *) SOURCE=$SOURCE_DIR/$LINK ;;
    esac
done
PROJECT_DIR=$(CDPATH= cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)

[ -f "$PROJECT_DIR/pyproject.toml" ] || fail "pyproject.toml not found beside install.sh"
[ -d "$PROJECT_DIR/src/pabrikon" ] || fail "Pabrikon sources not found under src/pabrikon"
[ -n "${HOME:-}" ] || fail 'HOME is not set'

PYTHON=
for candidate in python3.12 python3; do
    if command -v "$candidate" >/dev/null 2>&1 \
        && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))' >/dev/null 2>&1; then
        PYTHON=$(command -v "$candidate")
        break
    fi
done
[ -n "$PYTHON" ] || fail 'Python 3.12 or newer is required (tried python3.12 and python3)'

INSTALL_ROOT=${PABRIKON_HOME:-$HOME/.local/share/pabrikon}
BIN_DIR=${PABRIKON_BIN_DIR:-$HOME/.local/bin}
case $INSTALL_ROOT in
    /*) ;;
    *) INSTALL_ROOT=$PWD/$INSTALL_ROOT ;;
esac
case $BIN_DIR in
    /*) ;;
    *) BIN_DIR=$PWD/$BIN_DIR ;;
esac
VENV_DIR=$INSTALL_ROOT/venv
LAUNCHER=$BIN_DIR/pabrikon
ENTRY_POINT=$VENV_DIR/bin/pabrikon

mkdir -p "$INSTALL_ROOT" "$BIN_DIR" || fail 'cannot create the installation directories'

if [ ! -x "$VENV_DIR/bin/python" ]; then
    "$PYTHON" -m venv "$VENV_DIR" || fail 'could not create the Pabrikon virtual environment'
fi
[ -x "$VENV_DIR/bin/python" ] \
    && "$VENV_DIR/bin/python" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))' >/dev/null 2>&1 \
    || fail 'the existing Pabrikon virtual environment must use Python 3.12 or newer'

"$VENV_DIR/bin/python" -m pip install --upgrade "$PROJECT_DIR" \
    || fail 'package installation failed; check your Python and network setup'
[ -x "$ENTRY_POINT" ] || fail "Pabrikon entry point was not created: $ENTRY_POINT"

if [ -L "$LAUNCHER" ]; then
    CURRENT_TARGET=$(readlink "$LAUNCHER") || fail "cannot inspect existing launcher: $LAUNCHER"
    [ "$CURRENT_TARGET" = "$ENTRY_POINT" ] \
        || fail "$LAUNCHER points to another installation; move or remove it before retrying"
elif [ -e "$LAUNCHER" ]; then
    fail "$LAUNCHER already exists and is not a Pabrikon installer link; move it before retrying"
else
    ln -s "$ENTRY_POINT" "$LAUNCHER" || fail "cannot create launcher at $LAUNCHER"
fi

printf 'Pabrikon installed successfully.\n'
"$LAUNCHER" --version

case :${PATH}: in
    *:"$BIN_DIR":*) ;;
    *)
        printf '\nAdd this directory to PATH to run pabrikon from any shell:\n'
        printf '    export PATH="%s:$PATH"\n' "$BIN_DIR"
        ;;
esac

if ! command -v rsvg-convert >/dev/null 2>&1; then
    printf '\nOptional: install librsvg (provides rsvg-convert) to build PNG icons.\n'
fi
if ! command -v svgcleaner >/dev/null 2>&1; then
    printf 'Optional: install svgcleaner to use `pabrikon optimize`.\n'
fi
