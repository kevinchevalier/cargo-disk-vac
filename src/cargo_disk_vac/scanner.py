"""Scanner module for finding Cargo projects and calculating cache sizes."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


def get_git_branch(project_path: Path) -> str:
    """Get the current git branch for a project directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


@dataclass
class CargoProject:
    """Represents a Cargo project with its cache information."""

    name: str
    path: Path
    cache_size: int  # Size in bytes
    branch: str = ""

    @property
    def cache_size_human(self) -> str:
        """Return human-readable cache size."""
        return format_size(self.cache_size)


def format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def get_directory_size(path: Path) -> int:
    """Calculate the total size of a directory in bytes."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += get_directory_size(Path(entry.path))
    except PermissionError:
        pass  # Skip directories we can't access
    return total


def find_cargo_projects(root: Path, max_depth: int = 2) -> list[CargoProject]:
    """
    Find all Cargo projects with target directories under the given root.

    Args:
        root: The root directory to search from.
        max_depth: Maximum directory depth to search (default: 2).

    Returns:
        List of CargoProject instances.
    """
    projects = []
    root = root.resolve()

    def scan_directory(current: Path, depth: int) -> None:
        if depth > max_depth:
            return

        try:
            entries = list(os.scandir(current))
        except PermissionError:
            return

        # Check if this directory is a Cargo project with a target folder
        has_cargo_toml = False
        has_target = False
        target_path = None

        for entry in entries:
            if entry.name == "Cargo.toml" and entry.is_file():
                has_cargo_toml = True
            elif entry.name == "target" and entry.is_dir():
                has_target = True
                target_path = Path(entry.path)

        if has_cargo_toml and has_target and target_path:
            cache_size = get_directory_size(target_path)
            branch = get_git_branch(current)
            projects.append(
                CargoProject(
                    name=current.name,
                    path=current,
                    cache_size=cache_size,
                    branch=branch,
                )
            )

        # Continue scanning subdirectories
        for entry in entries:
            if entry.is_dir(follow_symlinks=False) and not entry.name.startswith("."):
                # Skip target directories and hidden folders
                if entry.name != "target":
                    scan_directory(Path(entry.path), depth + 1)

    scan_directory(root, 0)
    return sorted(projects, key=lambda p: p.cache_size, reverse=True)
