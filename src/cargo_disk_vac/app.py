"""Main Textual application for Cargo Disk Vacuum."""

import subprocess
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import DataTable, Footer, Header, Static

from .scanner import CargoProject, find_cargo_projects, format_size


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

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("c", "clean", "Clean"),
    ]

    def __init__(self, scan_path: Path | None = None) -> None:
        super().__init__()
        self.scan_path = scan_path or Path.cwd()
        self.projects: list[CargoProject] = []

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
        table.add_columns("Name", "Path", "Size")
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
            table.add_row(
                project.name,
                str(project.path),
                project.cache_size_human,
                key=str(project.path),
            )
            total_size += project.cache_size

        total_display = self.query_one("#total-display", TotalDisplay)
        total_display.update_total(total_size)

        if self.projects:
            self.update_status(f"Found {len(self.projects)} Cargo project(s)")
        else:
            self.update_status("No Cargo projects with build caches found")

    def action_clean(self) -> None:
        """Clean the selected project's cache."""
        table = self.query_one("#projects-table", DataTable)

        if not self.projects:
            self.update_status("No projects to clean")
            return

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key is None:
            self.update_status("No project selected")
            return

        project_path = Path(str(row_key.value))
        project = next((p for p in self.projects if p.path == project_path), None)

        if project:
            self.update_status(f"Cleaning {project.name}...")
            self._clean_project(project)

    @work(thread=True, exclusive=True)
    def _clean_project(self, project: CargoProject) -> None:
        """Run cargo clean on the project in a background thread."""
        success = self._run_cargo_clean(project.path)
        if success:
            self.call_from_thread(
                self.update_status, f"Cleaned {project.name} successfully"
            )
            self.call_from_thread(self.action_refresh)
        else:
            self.call_from_thread(
                self.update_status, f"Failed to clean {project.name}"
            )

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
