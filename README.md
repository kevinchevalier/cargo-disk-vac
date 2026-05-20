# Cargo Disk Vacuum

A TUI tool to manage Cargo build cache disk usage.
<img width="1324" height="930" alt="Screenshot 2026-02-03 at 8 54 27 AM" src="https://github.com/user-attachments/assets/6cd21907-afa4-408a-a451-ddf65bf54e40" />



## Features

- Scans directories for Cargo projects with build caches
- Displays cache sizes in an interactive table
- Clean individual project caches with a single keypress

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Scan current directory
cargo-disk-vac

# Scan a specific directory
cargo-disk-vac /path/to/projects
```

## Key Bindings

| Key | Action |
|-----|--------|
| `r` | Refresh project list and sizes |
| `c` | Clean selected project's cache |
| `q` | Quit |
