"""Entry point for Cargo Disk Vacuum."""

import argparse
from pathlib import Path

from .app import CargoVacuumApp


def main() -> None:
    """Run the Cargo Disk Vacuum application."""
    parser = argparse.ArgumentParser(
        description="A TUI tool to manage Cargo build cache disk usage"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to scan for Cargo projects (default: current directory)",
    )
    args = parser.parse_args()

    scan_path = Path(args.path).resolve()
    if not scan_path.is_dir():
        print(f"Error: {scan_path} is not a directory")
        return

    app = CargoVacuumApp(scan_path=scan_path)
    app.run()


if __name__ == "__main__":
    main()
