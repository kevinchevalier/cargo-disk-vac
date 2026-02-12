"""Main Textual application for Cargo Disk Vacuum."""

import subprocess
from pathlib import Path
from typing import ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import DataTable, Footer, Header, Static

from .scanner import CargoProject, find_cargo_projects, format_size

SELECTED_MARKER = "✓"
UNSELECTED_MARKER = " "


class TotalDisplay(Static):
    """Widget to display total cache size."""

    def update_total(self, total_bytes: int) -> None:
        """Update the total display."""
        self.update(f"Total: {format_size(total_bytes)}")


class StatusBar(Static):
    """Widget to display status messages."""

    pass


class CargoVacuumApp(App):
    """A TUI application to manage Cargo build cache disk usage."""

    CSS_PATH = "app.tcss"
    TITLE = "Cargo Disk Vacuum"

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("c", "clean", "Clean Selected"),
        Binding("space", "toggle_select", "Select"),
        Binding("a", "select_all", "Select All"),
    ]

    def __init__(self, scan_path: Path | None = None) -> None:
        super().__init__()
        self.scan_path = scan_path or Path.cwd()
        self.projects: list[CargoProject] = []
        self.selected_paths: set[str] = set()

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Container(
            DataTable(id="projects-table"),
            TotalDisplay(id="total-display"),
            StatusBar(id="status-bar"),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Set up the table and start initial scan."""
        table = self.query_one("#projects-table", DataTable)
        table.cursor_type = "row"
        table.add_columns(" ", "Name", "Path", "Branch", "Size")
        self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh the project list."""
        self.update_status("Scanning for Cargo projects...")
        self._scan_projects()

    @work(thread=True, exclusive=True)
    def _scan_projects(self) -> None:
        """Scan for Cargo projects in a background thread."""
        projects = find_cargo_projects(self.scan_path, 2)
        self.call_from_thread(self._update_projects, projects)

    def _update_projects(self, projects: list[CargoProject]) -> None:
        """Update projects list and refresh table (called from main thread)."""
        self.projects = projects
        self.populate_table()

    def populate_table(self) -> None:
        """Populate the table with projects."""
        table = self.query_one("#projects-table", DataTable)
        table.clear()

        total_size = 0
        for project in self.projects:
            path_key = str(project.path)
            marker = SELECTED_MARKER if path_key in self.selected_paths else UNSELECTED_MARKER
            table.add_row(
                marker,
                project.name,
                str(project.path),
                project.branch,
                project.cache_size_human,
                key=path_key,
            )
            total_size += project.cache_size

        total_display = self.query_one("#total-display", TotalDisplay)
        total_display.update_total(total_size)

        selected_count = len(self.selected_paths)
        if self.projects:
            msg = f"Found {len(self.projects)} Cargo project(s)"
            if selected_count:
                msg += f" | {selected_count} selected"
            self.update_status(msg)
        else:
            self.update_status("No Cargo projects with build caches found")

    def action_toggle_select(self) -> None:
        """Toggle selection of the currently highlighted project."""
        table = self.query_one("#projects-table", DataTable)
        if not self.projects:
            return

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key is None:
            return

        path_key = str(row_key.value)
        if path_key in self.selected_paths:
            self.selected_paths.discard(path_key)
        else:
            self.selected_paths.add(path_key)

        # Update the marker cell in-place
        marker = SELECTED_MARKER if path_key in self.selected_paths else UNSELECTED_MARKER
        row_idx = table.cursor_coordinate.row
        table.update_cell_at((row_idx, 0), marker)

        selected_count = len(self.selected_paths)
        self.update_status(
            f"Found {len(self.projects)} Cargo project(s) | {selected_count} selected"
            if selected_count
            else f"Found {len(self.projects)} Cargo project(s)"
        )

    def action_select_all(self) -> None:
        """Toggle selection of all projects."""
        if not self.projects:
            return

        all_paths = {str(p.path) for p in self.projects}
        if self.selected_paths == all_paths:
            self.selected_paths.clear()
        else:
            self.selected_paths = all_paths

        self.populate_table()

    def action_clean(self) -> None:
        """Clean all selected projects' caches, or the highlighted one if none selected."""
        if not self.projects:
            self.update_status("No projects to clean")
            return

        # Determine which projects to clean
        if self.selected_paths:
            to_clean = [p for p in self.projects if str(p.path) in self.selected_paths]
        else:
            table = self.query_one("#projects-table", DataTable)
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            if row_key is None:
                self.update_status("No project selected")
                return
            project_path = Path(str(row_key.value))
            to_clean = [p for p in self.projects if p.path == project_path]

        if not to_clean:
            self.update_status("No project selected")
            return

        names = ", ".join(p.name for p in to_clean)
        self.update_status(f"Cleaning {names}...")
        self._clean_projects(to_clean)

    @work(thread=True, exclusive=True)
    def _clean_projects(self, projects: list[CargoProject]) -> None:
        """Run cargo clean on multiple projects in a background thread."""
        succeeded: list[str] = []
        failed: list[str] = []
        for project in projects:
            if self._run_cargo_clean(project.path):
                succeeded.append(project.name)
            else:
                failed.append(project.name)

        parts: list[str] = []
        if succeeded:
            parts.append(f"Cleaned: {', '.join(succeeded)}")
        if failed:
            parts.append(f"Failed: {', '.join(failed)}")
        msg = " | ".join(parts)

        def _finish() -> None:
            self.selected_paths.clear()
            self.update_status(msg)
            self.action_refresh()

        self.call_from_thread(_finish)

    def _run_cargo_clean(self, project_path: Path) -> bool:
        """Execute cargo clean synchronously."""
        try:
            result = subprocess.run(
                ["cargo", "clean"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def update_status(self, message: str) -> None:
        """Update the status bar."""
        status = self.query_one("#status-bar", StatusBar)
        status.update(message)
