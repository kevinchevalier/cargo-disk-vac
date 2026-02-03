# Cargo Disk Vacuum

A TUI tool to manage Cargo build cache disk usage.

<img width="1023" height="766" alt="Screenshot 2025-12-17 at 3 12 25 PM" src="https://github.com/user-attachments/assets/acc93898-5aa8-4303-a6ce-fc1ad0dccad9" />

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
