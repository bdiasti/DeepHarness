"""
Docker integration — exposes Docker and docker-compose operations as LangChain tools.

Config:
    {
        "compose_file": "docker-compose.yml",
        "enabled": true
    }
"""

import os
import subprocess
import json

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


def _container_name(project_name: str) -> str:
    """Derive a deterministic container name from the project name."""
    return project_name.replace(" ", "-").lower()


def _run_cmd(args: list[str], cwd: str | None = None) -> str:
    """Run a subprocess command and return combined output."""
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode != 0:
            return f"Error (exit {result.returncode}): {err}" if err else f"Error (exit {result.returncode})"
        # Some docker commands write to stderr even on success (e.g. build progress)
        combined = output if output else err
        return combined if combined else "(no output)"
    except FileNotFoundError:
        return "Error: docker is not installed or not found on PATH."
    except Exception as exc:
        return f"Error: {exc}"


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

@tool
def docker_build(project_name: str, tag: str = "latest") -> str:
    """Build a Docker image from the Dockerfile in the project directory."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."
    image_name = f"{_container_name(project_name)}:{tag}"
    return _run_cmd(["docker", "build", "-t", image_name, "."], cwd=project_dir)


@tool
def docker_run(project_name: str, tag: str = "latest", port_mapping: str = "8080:8080") -> str:
    """Run a Docker container from the project image.

    The container is started in detached mode with the given port mapping.
    """
    container = _container_name(project_name)
    image_name = f"{container}:{tag}"
    return _run_cmd([
        "docker", "run", "-d",
        "--name", container,
        "-p", port_mapping,
        image_name,
    ])


@tool
def docker_stop(project_name: str) -> str:
    """Stop and remove the running container for the project."""
    container = _container_name(project_name)
    stop_out = _run_cmd(["docker", "stop", container])
    if stop_out.startswith("Error"):
        return stop_out
    rm_out = _run_cmd(["docker", "rm", container])
    if rm_out.startswith("Error"):
        return f"Container stopped but removal failed: {rm_out}"
    return f"Container '{container}' stopped and removed."


@tool
def docker_logs(project_name: str, tail: int = 50) -> str:
    """Retrieve the most recent logs from the project container."""
    container = _container_name(project_name)
    return _run_cmd(["docker", "logs", "--tail", str(tail), container])


@tool
def docker_status(project_name: str) -> str:
    """Check whether the project container is currently running."""
    container = _container_name(project_name)
    result = _run_cmd([
        "docker", "ps",
        "--filter", f"name=^/{container}$",
        "--format", "{{.ID}}  {{.Status}}  {{.Ports}}",
    ])
    if result.startswith("Error"):
        return result
    if not result or result == "(no output)":
        return f"Container '{container}' is not running."
    return f"Container '{container}' is running:\n{result}"


@tool
def docker_compose_up(project_name: str) -> str:
    """Run docker-compose up -d in the project directory."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."
    return _run_cmd(["docker", "compose", "up", "-d"], cwd=project_dir)


@tool
def docker_compose_down(project_name: str) -> str:
    """Run docker-compose down in the project directory."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."
    return _run_cmd(["docker", "compose", "down"], cwd=project_dir)


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class DockerIntegration(IntegrationBase):
    name = "docker"
    category = "deploy"
    icon = "docker"
    color = "#2496ED"

    def __init__(self, config: dict):
        super().__init__(config)
        self.compose_file = config.get("compose_file", "docker-compose.yml")

        if config.get("enabled"):
            self._status = IntegrationStatus.CONNECTED
        else:
            self._status = IntegrationStatus.DISCONNECTED

    def get_tools(self) -> list:
        """Return all Docker tools for the agent."""
        return [
            docker_build,
            docker_run,
            docker_stop,
            docker_logs,
            docker_status,
            docker_compose_up,
            docker_compose_down,
        ]

    async def health_check(self) -> bool:
        """Verify that docker is available and the daemon is running."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
            )
            healthy = result.returncode == 0
            self._status = IntegrationStatus.CONNECTED if healthy else IntegrationStatus.ERROR
            return healthy
        except Exception:
            self._status = IntegrationStatus.ERROR
            return False
