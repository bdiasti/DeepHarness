"""
GitLab / Git integration — exposes git operations as LangChain tools.

Config:
    {
        "url": "https://gitlab.com",
        "project": "team/repo",
        "token": "glpat-...",
        "enabled": true
    }
"""

import os
import subprocess
import json
from typing import Optional

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


def _run_git(project_name: str, *args: str) -> str:
    """Run a git command inside the project directory and return its output."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            err = result.stderr.strip()
            return f"Git error (exit {result.returncode}): {err}" if err else f"Git error (exit {result.returncode})"
        return output if output else "(no output)"
    except FileNotFoundError:
        return "Error: git is not installed or not found on PATH."
    except Exception as exc:
        return f"Error running git: {exc}"


# ---------------------------------------------------------------------------
# Tool functions (module-level so LangChain can serialise them)
# ---------------------------------------------------------------------------

@tool
def git_init(project_name: str) -> str:
    """Initialize a new git repository in the given project directory."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."
    try:
        result = subprocess.run(
            ["git", "init"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return f"Git init error: {result.stderr.strip()}"
        return f"Initialized git repository in {project_name}."
    except FileNotFoundError:
        return "Error: git is not installed or not found on PATH."
    except Exception as exc:
        return f"Error: {exc}"


@tool
def git_commit(project_name: str, message: str) -> str:
    """Stage all changes and create a commit with the given message."""
    add_out = _run_git(project_name, "add", "-A")
    if add_out.startswith("Error"):
        return add_out
    return _run_git(project_name, "commit", "-m", message)


@tool
def git_push(project_name: str, branch: str = "main") -> str:
    """Push the current branch to the remote origin."""
    return _run_git(project_name, "push", "origin", branch)


@tool
def git_create_branch(project_name: str, branch_name: str) -> str:
    """Create a new branch and switch to it."""
    return _run_git(project_name, "checkout", "-b", branch_name)


@tool
def git_diff(project_name: str) -> str:
    """Show the current unstaged diff for the project."""
    return _run_git(project_name, "diff")


@tool
def git_log(project_name: str, limit: int = 10) -> str:
    """Show the most recent git commits (default 10)."""
    return _run_git(project_name, "log", f"--oneline", f"-{limit}")


@tool
def git_status(project_name: str) -> str:
    """Show the current git status for the project."""
    return _run_git(project_name, "status", "--short")


@tool
def git_create_mr(
    project_name: str,
    title: str,
    source_branch: str,
    target_branch: str = "main",
) -> str:
    """Create a Merge Request on GitLab via the API.

    If no GitLab token is configured the tool returns manual instructions instead.
    """
    # Try to read config from environment / integration config.
    gitlab_url = os.environ.get("GITLAB_URL", "https://gitlab.com")
    gitlab_token = os.environ.get("GITLAB_TOKEN", "")
    gitlab_project = os.environ.get("GITLAB_PROJECT", "")

    if not gitlab_token or not gitlab_project:
        return (
            "GitLab token or project not configured. "
            "To create a merge request manually:\n"
            f"  1. Push branch '{source_branch}' to origin.\n"
            f"  2. Open your GitLab project and click 'New Merge Request'.\n"
            f"  3. Set source='{source_branch}', target='{target_branch}', title='{title}'."
        )

    import urllib.request
    import urllib.error

    api_url = (
        f"{gitlab_url.rstrip('/')}/api/v4/projects/"
        f"{urllib.request.quote(gitlab_project, safe='')}/merge_requests"
    )
    payload = json.dumps({
        "source_branch": source_branch,
        "target_branch": target_branch,
        "title": title,
    }).encode()

    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "PRIVATE-TOKEN": gitlab_token,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return f"Merge request created: {data.get('web_url', '(no URL returned)')}"
    except urllib.error.HTTPError as exc:
        body = exc.read().decode() if exc.fp else ""
        return f"GitLab API error ({exc.code}): {body}"
    except Exception as exc:
        return f"Error creating merge request: {exc}"


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class GitLabIntegration(IntegrationBase):
    name = "gitlab"
    category = "version_control"
    icon = "gitlab"
    color = "#FC6D26"

    def __init__(self, config: dict):
        super().__init__(config)
        # Push relevant config into env so the tool functions can pick it up.
        if config.get("url"):
            os.environ["GITLAB_URL"] = config["url"]
        if config.get("token"):
            os.environ["GITLAB_TOKEN"] = config["token"]
        if config.get("project"):
            os.environ["GITLAB_PROJECT"] = config["project"]

        if config.get("enabled"):
            self._status = IntegrationStatus.CONNECTED
        else:
            self._status = IntegrationStatus.DISCONNECTED

    def get_tools(self) -> list:
        """Return all git / GitLab tools for the agent."""
        return [
            git_init,
            git_commit,
            git_push,
            git_create_branch,
            git_diff,
            git_log,
            git_status,
            git_create_mr,
        ]

    async def health_check(self) -> bool:
        """Verify that git is available on the system."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
            )
            healthy = result.returncode == 0
            self._status = IntegrationStatus.CONNECTED if healthy else IntegrationStatus.ERROR
            return healthy
        except Exception:
            self._status = IntegrationStatus.ERROR
            return False
