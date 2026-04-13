"""
Local Docker Registry integration — exposes registry operations as LangChain tools.

Config:
    {
        "url": "http://localhost:5000",
        "enabled": false
    }
"""

import os
import subprocess
import json
import urllib.request

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


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
        combined = output if output else err
        return combined if combined else "(no output)"
    except FileNotFoundError:
        return "Error: docker is not installed or not found on PATH."
    except Exception as exc:
        return f"Error: {exc}"


def _registry_api(path: str, base_url: str = "http://localhost:5000") -> dict | str:
    """Make a GET request to the registry API and return parsed JSON."""
    url = f"{base_url}{path}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        return f"Error: could not reach registry at {url} — {exc.reason}"
    except Exception as exc:
        return f"Error: {exc}"


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

@tool
def registry_setup(project_name: str) -> str:
    """Start a local Docker registry (registry:2) on port 5000.

    Returns instructions for using the registry.
    """
    # Check if already running
    check = _run_cmd(["docker", "ps", "--filter", "name=^/registry$", "--format", "{{.ID}}"])
    if check and not check.startswith("Error") and check != "(no output)":
        return (
            "Local Docker registry is already running.\n\n"
            "Push images with:\n"
            "  docker tag <image>:<tag> localhost:5000/<image>:<tag>\n"
            "  docker push localhost:5000/<image>:<tag>\n\n"
            "Browse catalog: http://localhost:5000/v2/_catalog"
        )

    result = _run_cmd(["docker", "run", "-d", "-p", "5000:5000", "--name", "registry", "registry:2"])
    if result.startswith("Error"):
        return f"Failed to start registry: {result}"

    return (
        f"Local Docker registry started (container id: {result[:12]}).\n\n"
        "Registry URL: http://localhost:5000\n\n"
        "Push images with:\n"
        "  docker tag <image>:<tag> localhost:5000/<image>:<tag>\n"
        "  docker push localhost:5000/<image>:<tag>\n\n"
        "Browse catalog: http://localhost:5000/v2/_catalog"
    )


@tool
def registry_push(project_name: str, image_name: str, tag: str = "latest") -> str:
    """Tag a local Docker image for the local registry and push it."""
    local_ref = f"{image_name}:{tag}"
    registry_ref = f"localhost:5000/{image_name}:{tag}"

    tag_result = _run_cmd(["docker", "tag", local_ref, registry_ref])
    if tag_result.startswith("Error"):
        return f"Failed to tag image: {tag_result}"

    push_result = _run_cmd(["docker", "push", registry_ref])
    if push_result.startswith("Error"):
        return f"Image tagged but push failed: {push_result}"

    return f"Successfully pushed {registry_ref}\n\n{push_result}"


@tool
def registry_list(project_name: str) -> str:
    """List all images and their tags in the local Docker registry."""
    catalog = _registry_api("/v2/_catalog")
    if isinstance(catalog, str):
        return catalog

    repos = catalog.get("repositories", [])
    if not repos:
        return "Registry is empty — no images found."

    lines = ["Images in local registry:\n"]
    for repo in repos:
        tags_resp = _registry_api(f"/v2/{repo}/tags/list")
        if isinstance(tags_resp, str):
            lines.append(f"  {repo}: (error fetching tags)")
        else:
            tags = tags_resp.get("tags") or []
            tags_str = ", ".join(tags) if tags else "(no tags)"
            lines.append(f"  {repo}: {tags_str}")

    return "\n".join(lines)


@tool
def registry_tag(project_name: str, image_name: str, current_tag: str, new_tag: str) -> str:
    """Retag an image in the local registry with a new tag.

    Pulls the image with the current tag, tags it with the new tag, and pushes it back.
    """
    current_ref = f"localhost:5000/{image_name}:{current_tag}"
    new_ref = f"localhost:5000/{image_name}:{new_tag}"

    pull_result = _run_cmd(["docker", "pull", current_ref])
    if pull_result.startswith("Error"):
        return f"Failed to pull {current_ref}: {pull_result}"

    tag_result = _run_cmd(["docker", "tag", current_ref, new_ref])
    if tag_result.startswith("Error"):
        return f"Failed to tag image: {tag_result}"

    push_result = _run_cmd(["docker", "push", new_ref])
    if push_result.startswith("Error"):
        return f"Image tagged locally but push failed: {push_result}"

    return f"Successfully retagged {image_name}:{current_tag} → {image_name}:{new_tag}"


@tool
def registry_status(project_name: str) -> str:
    """Check if the local Docker registry is running and accessible."""
    # Check docker process
    ps_result = _run_cmd([
        "docker", "ps",
        "--filter", "name=^/registry$",
        "--format", "{{.ID}}  {{.Status}}  {{.Ports}}",
    ])

    container_running = ps_result and not ps_result.startswith("Error") and ps_result != "(no output)"

    # Check API accessibility
    api_resp = _registry_api("/v2/")
    api_ok = isinstance(api_resp, dict)

    lines = []
    if container_running:
        lines.append(f"Container: running\n  {ps_result}")
    else:
        lines.append(f"Container: not running ({ps_result})")

    if api_ok:
        lines.append("API: accessible at http://localhost:5000/v2/")
    else:
        lines.append(f"API: not accessible — {api_resp}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class RegistryIntegration(IntegrationBase):
    name = "registry"
    category = "registry"
    icon = "box"
    color = "#1D63ED"

    def __init__(self, config: dict):
        super().__init__(config)
        self.url = config.get("url", "http://localhost:5000")

        if config.get("enabled"):
            self._status = IntegrationStatus.CONNECTED
        else:
            self._status = IntegrationStatus.DISCONNECTED

    def get_tools(self) -> list:
        """Return all registry tools for the agent."""
        return [
            registry_setup,
            registry_push,
            registry_list,
            registry_tag,
            registry_status,
        ]

    async def health_check(self) -> bool:
        """Verify the registry is reachable via GET /v2/."""
        try:
            resp = _registry_api("/v2/", base_url=self.url)
            healthy = isinstance(resp, dict)
            self._status = IntegrationStatus.CONNECTED if healthy else IntegrationStatus.ERROR
            return healthy
        except Exception:
            self._status = IntegrationStatus.ERROR
            return False
