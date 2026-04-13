"""
SonarQube integration — quality gate scanning via Docker.

Config:
    {
        "url": "http://localhost:9000",
        "token": "",
        "enabled": false
    }
"""

import os
import subprocess
import json

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


def _sonar_url() -> str:
    return os.environ.get("SONARQUBE_URL", "http://localhost:9000")


def _sonar_token() -> str:
    return os.environ.get("SONARQUBE_TOKEN", "")


def _project_key(project_name: str, project_key: str = "") -> str:
    """Derive a SonarQube project key from the project name or explicit key."""
    if project_key:
        return project_key
    return project_name.replace(" ", "-").lower()


def _sonar_api_get(path: str) -> dict:
    """Make a GET request to the SonarQube API."""
    import urllib.request
    import urllib.error

    url = f"{_sonar_url()}{path}"
    req = urllib.request.Request(url, method="GET")
    token = _sonar_token()
    if token:
        import base64
        credentials = base64.b64encode(f"{token}:".encode()).decode()
        req.add_header("Authorization", f"Basic {credentials}")

    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

@tool
def sonar_scan(project_name: str, project_key: str = "") -> str:
    """Run a SonarQube scan on the project using Docker sonar-scanner-cli.

    Expects SonarQube server running at localhost:9000.
    Creates a default sonar-project.properties if one does not exist.
    """
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."

    key = _project_key(project_name, project_key)
    props_path = os.path.join(project_dir, "sonar-project.properties")

    # Create default properties file if missing
    if not os.path.isfile(props_path):
        props_content = (
            f"sonar.projectKey={key}\n"
            f"sonar.projectName={project_name}\n"
            f"sonar.sources=.\n"
            f"sonar.host.url={_sonar_url()}\n"
            f"sonar.sourceEncoding=UTF-8\n"
        )
        token = _sonar_token()
        if token:
            props_content += f"sonar.login={token}\n"
        with open(props_path, "w", encoding="utf-8") as f:
            f.write(props_content)

    # Run scanner via Docker
    cmd = [
        "docker", "run", "--rm",
        "--network", "host",
        "-v", f"{project_dir}:/usr/src",
        "sonarsource/sonar-scanner-cli",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode != 0:
            return f"Scan failed (exit {result.returncode}):\n{err or output}"
        # Extract summary lines
        lines = output.splitlines()
        summary = [l for l in lines if "ANALYSIS" in l.upper() or "INFO: " in l]
        return f"SonarQube scan completed for '{key}'.\n" + "\n".join(summary[-10:]) if summary else f"Scan completed for '{key}'.\n{output[-500:]}"
    except FileNotFoundError:
        return "Error: docker is not installed or not found on PATH."
    except subprocess.TimeoutExpired:
        return "Error: scan timed out after 5 minutes."
    except Exception as exc:
        return f"Error running scan: {exc}"


@tool
def sonar_quality_gate(project_name: str, project_key: str = "") -> str:
    """Check SonarQube quality gate status for the project. Returns PASS or FAIL with metrics."""
    key = _project_key(project_name, project_key)
    try:
        data = _sonar_api_get(f"/api/qualitygates/project_status?projectKey={key}")
        status = data.get("projectStatus", {})
        gate_status = status.get("status", "UNKNOWN")
        conditions = status.get("conditions", [])

        result_label = "PASS" if gate_status == "OK" else "FAIL"
        lines = [f"Quality Gate: {result_label} ({gate_status})"]

        for cond in conditions:
            metric = cond.get("metricKey", "?")
            actual = cond.get("actualValue", "?")
            threshold = cond.get("errorThreshold", "?")
            cond_status = cond.get("status", "?")
            icon = "OK" if cond_status == "OK" else "FAIL"
            lines.append(f"  [{icon}] {metric}: {actual} (threshold: {threshold})")

        return "\n".join(lines)
    except Exception as exc:
        return f"Error checking quality gate: {exc}"


@tool
def sonar_issues(project_name: str, project_key: str = "", severity: str = "") -> str:
    """List issues from SonarQube for the project.

    Optional severity filter: BLOCKER, CRITICAL, MAJOR, MINOR, INFO.
    """
    key = _project_key(project_name, project_key)
    path = f"/api/issues/search?projectKeys={key}"
    if severity:
        severity = severity.upper()
        if severity in ("BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"):
            path += f"&severities={severity}"
        else:
            return f"Error: invalid severity '{severity}'. Use: BLOCKER, CRITICAL, MAJOR, MINOR, INFO."

    try:
        data = _sonar_api_get(path)
        issues = data.get("issues", [])
        total = data.get("total", len(issues))

        if not issues:
            return f"No issues found for project '{key}'" + (f" with severity {severity}" if severity else "") + "."

        lines = [f"Found {total} issue(s) for '{key}'" + (f" (severity: {severity})" if severity else "") + ":"]
        for issue in issues[:25]:
            sev = issue.get("severity", "?")
            msg = issue.get("message", "?")
            component = issue.get("component", "?").split(":")[-1]
            line_num = issue.get("line", "?")
            issue_type = issue.get("type", "?")
            lines.append(f"  [{sev}] {component}:{line_num} — {msg} ({issue_type})")

        if total > 25:
            lines.append(f"  ... and {total - 25} more issues.")
        return "\n".join(lines)
    except Exception as exc:
        return f"Error fetching issues: {exc}"


@tool
def sonar_setup(project_name: str) -> str:
    """Generate sonar-project.properties and provide instructions to start SonarQube server."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."

    key = _project_key(project_name)
    props_path = os.path.join(project_dir, "sonar-project.properties")

    props_content = (
        f"sonar.projectKey={key}\n"
        f"sonar.projectName={project_name}\n"
        f"sonar.projectVersion=1.0\n"
        f"sonar.sources=.\n"
        f"sonar.host.url={_sonar_url()}\n"
        f"sonar.sourceEncoding=UTF-8\n"
        f"sonar.exclusions=**/node_modules/**,**/vendor/**,**/*.test.*,**/dist/**\n"
    )
    with open(props_path, "w", encoding="utf-8") as f:
        f.write(props_content)

    docker_cmd = "docker run -d --name sonarqube -p 9000:9000 sonarqube:community"

    return (
        f"Created sonar-project.properties in '{project_name}'.\n\n"
        f"To start SonarQube server (if not already running):\n"
        f"  {docker_cmd}\n\n"
        f"Wait ~1-2 minutes for SonarQube to boot, then access at {_sonar_url()}.\n"
        f"Default credentials: admin / admin\n"
        f"After login, generate a token and configure it in the integration settings."
    )


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class SonarQubeIntegration(IntegrationBase):
    name = "sonarqube"
    category = "quality"
    icon = "shield-check"
    color = "#4E9BCD"

    def __init__(self, config: dict):
        super().__init__(config)
        if config.get("url"):
            os.environ["SONARQUBE_URL"] = config["url"]
        if config.get("token"):
            os.environ["SONARQUBE_TOKEN"] = config["token"]

        if config.get("enabled"):
            self._status = IntegrationStatus.CONNECTED
        else:
            self._status = IntegrationStatus.DISCONNECTED

    def get_tools(self) -> list:
        """Return all SonarQube tools for the agent."""
        return [
            sonar_scan,
            sonar_quality_gate,
            sonar_issues,
            sonar_setup,
        ]

    async def health_check(self) -> bool:
        """Check if SonarQube server is reachable."""
        try:
            data = _sonar_api_get("/api/system/status")
            healthy = data.get("status") in ("UP", "STARTING")
            self._status = IntegrationStatus.CONNECTED if healthy else IntegrationStatus.ERROR
            return healthy
        except Exception:
            self._status = IntegrationStatus.ERROR
            return False
