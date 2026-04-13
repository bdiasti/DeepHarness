"""
Flyway database migration integration — manages SQL migrations via Flyway in Docker.

Config:
    {
        "jdbc_url": "jdbc:postgresql://localhost:5432/app",
        "user": "app",
        "password": "app",
        "enabled": false
    }
"""

import os
import subprocess
import json
import re
import glob as globmod

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


def _run_cmd(args: list[str], cwd: str | None = None) -> str:
    """Run a subprocess command and return combined output."""
    try:
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
        output = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode != 0:
            return f"Error (exit {result.returncode}): {err}" if err else f"Error (exit {result.returncode})"
        combined = output if output else err
        return combined if combined else "(no output)"
    except FileNotFoundError:
        return "Error: docker is not installed or not found on PATH."
    except Exception as exc:
        return f"Error: {exc}"


def _migrations_dir(project_name: str) -> str:
    """Return the migrations directory path for a project."""
    return os.path.join(OUTPUT_DIR, project_name, "db", "migrations")


def _next_version(migrations_dir: str) -> int:
    """Scan existing V{n}__*.sql files and return the next version number."""
    if not os.path.isdir(migrations_dir):
        return 1
    pattern = os.path.join(migrations_dir, "V*__*.sql")
    files = globmod.glob(pattern)
    versions = []
    for f in files:
        basename = os.path.basename(f)
        match = re.match(r"V(\d+)__", basename)
        if match:
            versions.append(int(match.group(1)))
    return max(versions) + 1 if versions else 1


def _flyway_docker_cmd(migrations_dir: str, jdbc_url: str, user: str, password: str,
                       command: str) -> list[str]:
    """Build a Flyway Docker run command."""
    # Convert Windows path to Docker-compatible mount path
    mount_dir = migrations_dir.replace("\\", "/")
    return [
        "docker", "run", "--rm",
        "--network", "host",
        "-v", f"{mount_dir}:/flyway/sql",
        "flyway/flyway",
        f"-url={jdbc_url}",
        f"-user={user}",
        f"-password={password}",
        command,
    ]


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

@tool
def db_create_migration(project_name: str, name: str, sql_content: str) -> str:
    """Create a new Flyway migration file with auto-incremented version number."""
    mig_dir = _migrations_dir(project_name)
    os.makedirs(mig_dir, exist_ok=True)

    version = _next_version(mig_dir)
    # Sanitize migration name: replace spaces/special chars with underscores
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    filename = f"V{version}__{safe_name}.sql"
    filepath = os.path.join(mig_dir, filename)

    with open(filepath, "w") as f:
        f.write(sql_content)

    return f"Migration created: {filepath}\nVersion: V{version}, Name: {safe_name}"


@tool
def db_migrate(project_name: str,
               jdbc_url: str = "jdbc:postgresql://localhost:5432/app",
               user: str = "app",
               password: str = "app") -> str:
    """Run Flyway migrate to apply all pending migrations to the database."""
    mig_dir = _migrations_dir(project_name)
    if not os.path.isdir(mig_dir):
        return f"Error: migrations directory not found at {mig_dir}. Create a migration first."

    cmd = _flyway_docker_cmd(mig_dir, jdbc_url, user, password, "migrate")
    result = _run_cmd(cmd)
    return f"[Flyway Migrate] project={project_name}\n{result}"


@tool
def db_status(project_name: str,
              jdbc_url: str = "jdbc:postgresql://localhost:5432/app",
              user: str = "app",
              password: str = "app") -> str:
    """Show Flyway migration status (which migrations have been applied)."""
    mig_dir = _migrations_dir(project_name)
    if not os.path.isdir(mig_dir):
        return f"Error: migrations directory not found at {mig_dir}. Create a migration first."

    cmd = _flyway_docker_cmd(mig_dir, jdbc_url, user, password, "info")
    result = _run_cmd(cmd)
    return f"[Flyway Info] project={project_name}\n{result}"


@tool
def db_rollback(project_name: str,
                jdbc_url: str = "jdbc:postgresql://localhost:5432/app",
                user: str = "app",
                password: str = "app") -> str:
    """Attempt Flyway undo (requires Flyway Teams edition). Falls back to guidance on creating a manual rollback migration."""
    mig_dir = _migrations_dir(project_name)
    if not os.path.isdir(mig_dir):
        return f"Error: migrations directory not found at {mig_dir}. Create a migration first."

    cmd = _flyway_docker_cmd(mig_dir, jdbc_url, user, password, "undo")
    result = _run_cmd(cmd)

    if "undo" in result.lower() and "error" in result.lower():
        version = _next_version(mig_dir)
        return (
            f"[Flyway Undo] Flyway 'undo' requires the Teams edition and is not available in the community image.\n\n"
            f"Alternative: create a manual rollback migration using db_create_migration with version V{version}.\n"
            f"For example, use ALTER TABLE / DROP TABLE statements to reverse the last migration."
        )

    return f"[Flyway Undo] project={project_name}\n{result}"


@tool
def db_list_migrations(project_name: str) -> str:
    """List all migration files in db/migrations/ sorted by version number."""
    mig_dir = _migrations_dir(project_name)
    if not os.path.isdir(mig_dir):
        return f"No migrations directory found at {mig_dir}."

    pattern = os.path.join(mig_dir, "V*__*.sql")
    files = sorted(globmod.glob(pattern))

    if not files:
        return f"No migration files found in {mig_dir}."

    lines = [f"[Migrations] project={project_name} ({len(files)} files)"]
    for f in files:
        basename = os.path.basename(f)
        size = os.path.getsize(f)
        lines.append(f"  - {basename}  ({size} bytes)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class FlywayIntegration(IntegrationBase):
    name = "flyway"
    category = "database"
    icon = "database"
    color = "#CC0200"

    DEFAULT_CONFIG = {
        "jdbc_url": "jdbc:postgresql://localhost:5432/app",
        "user": "app",
        "password": "app",
        "enabled": False,
    }

    def __init__(self, config: dict):
        merged = {**self.DEFAULT_CONFIG, **config}
        super().__init__(merged)

        if merged.get("enabled"):
            self._status = IntegrationStatus.CONNECTED
        else:
            self._status = IntegrationStatus.DISCONNECTED

    def get_tools(self) -> list:
        return [
            db_create_migration,
            db_migrate,
            db_status,
            db_rollback,
            db_list_migrations,
        ]

    async def health_check(self) -> bool:
        """Check if Docker is available and the Flyway image exists locally."""
        try:
            # Check docker is running
            docker_check = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, timeout=10
            )
            if docker_check.returncode != 0:
                self._status = IntegrationStatus.ERROR
                return False

            # Check if flyway image exists
            image_check = subprocess.run(
                ["docker", "image", "inspect", "flyway/flyway"],
                capture_output=True, text=True, timeout=10,
            )
            if image_check.returncode != 0:
                # Image not pulled yet, but Docker works — still consider it "connected"
                self._status = IntegrationStatus.CONNECTED
                return True

            self._status = IntegrationStatus.CONNECTED
            return True
        except FileNotFoundError:
            self._status = IntegrationStatus.DISCONNECTED
            return False
        except Exception:
            self._status = IntegrationStatus.ERROR
            return False
