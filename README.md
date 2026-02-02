# Cargo Disk Vacuum

A TUI tool to manage Cargo build cache disk usage.

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
