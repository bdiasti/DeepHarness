# Constitution — CLI Tool

IMMUTABLE rules.

## Stack (FIXED)
1. Language: Python 3.11+ (or Go if explicitly chosen).
2. CLI framework: Typer (preferred) OR Click.
3. Packaging: pyproject.toml + pip-installable.
4. Config: env vars + TOML file (no YAML for CLI config).

## UX
5. `--help` MUST be informative and clear.
6. Errors MUST have actionable messages (what went wrong + how to fix).
7. Long operations MUST show progress (Rich progress bars).
8. Colors MUST respect NO_COLOR env var.

## Quality
9. Every command MUST have at least one test.
10. Exit codes MUST be meaningful: 0=success, 1=error, 2=misuse.
11. stdin/stdout MUST be usable in pipes (logs to stderr).
12. MUST support --version and --help.

## Distribution
13. MUST publish to PyPI (or include installation via pipx).
14. MUST include a Dockerfile for containerized usage.

## What's NOT allowed
- Do NOT use argparse directly (use Typer/Click).
- Do NOT write to stdout for logs (use stderr).
- Do NOT require interactive input in pipes.
