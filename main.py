"""Backward-compatible shim for the CLI entrypoint."""

from apps.cli import run


if __name__ == "__main__":
    run()
