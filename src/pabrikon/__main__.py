"""Enable running the command line with ``python -m pabrikon``."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
