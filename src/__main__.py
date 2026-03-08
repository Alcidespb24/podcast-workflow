"""Package entry point: ``python -m src <command>``."""

from __future__ import annotations

import sys


def _usage() -> None:
    print("Usage: python -m src <command>")
    print()
    print("Commands:")
    print("  watch    Start the folder watcher (standalone, no web server)")


def main() -> None:
    if len(sys.argv) < 2:
        _usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "watch":
        from src.backend.cli.watch import main as watch_main

        watch_main()
    else:
        print(f"Unknown command: {command}")
        _usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
