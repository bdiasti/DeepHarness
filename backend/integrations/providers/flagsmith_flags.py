"""
Flagsmith feature flags integration — exposes feature flag operations as LangChain tools.

Config:
    {
        "url": "http://localhost:8001",
        "api_key": "",
        "project_id": "",
        "enabled": false
    }
"""

import os
import subprocess
import json
import urllib.request
import urllib.error

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR

# Module-level config defaults — overridden by integration instance at runtime.
_FLAGSMITH_URL = "http://localhost:8001"
_FLAGSMITH_API_KEY = ""
_FLAGSMITH_PROJECT_ID = ""


def _api_request(
    path: str,
    method: str = "GET",
    data: dict | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> dict | list | str:
    """Make an HTTP request to the Flagsmith API."""
    url = f"{base_url or _FLAGSMITH_URL}{path}"
    key = api_key or _FLAGSMITH_API_KEY

    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Token {key}"

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_text = ""
        try:
            body_text = exc.read().decode()[:500]
        except Exception:
            pass
        return f"Error (HTTP {exc.code}): {body_text}"
    except urllib.error.URLError as exc:
        return f"Error: could not reach Flagsmith at {url} — {exc.reason}"
    except Exception as exc:
        return f"Error: {exc}"


def _run_cmd(args: list[str]) -> str:
    """Run a subprocess command and return combined output."""
    try:
        result = subprocess.run(args, capture_output=True, text=True)
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


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

@tool
def flag_setup(project_name: str) -> str:
    """Start Flagsmith locally via Docker on port 8001.

    Returns the URL and instructions for initial setup.
    """
    # Check if already running
    check = _run_cmd(["docker", "ps", "--filter", "name=^/flagsmith$", "--format", "{{.ID}}"])
    if check and not check.startswith("Error") and check != "(no output)":
        return (
            "Flagsmith is already running.\n\n"
            "URL: http://localhost:8001\n\n"
            "If this is a fresh install, open the URL and:\n"
            "  1. Create an admin account\n"
            "  2. Create an organisation\n"
            "  3. Create a project\n"
            "  4. Copy the API key from Settings > Keys\n"
            "  5. Set the api_key and project_id in the integration config"
        )

    result = _run_cmd([
        "docker", "run", "-d",
        "--name", "flagsmith",
        "-p", "8001:8000",
        "flagsmith/flagsmith:latest",
    ])
    if result.startswith("Error"):
        return f"Failed to start Flagsmith: {result}"

    return (
        f"Flagsmith started (container id: {result[:12]}).\n\n"
        "URL: http://localhost:8001\n\n"
        "Initial setup steps:\n"
        "  1. Open http://localhost:8001 in your browser\n"
        "  2. Create an admin account\n"
        "  3. Create an organisation\n"
        "  4. Create a project\n"
        "  5. Copy the Server-side API key from Settings > Keys\n"
        "  6. Set the api_key and project_id in the integration config"
    )


@tool
def flag_create(
    project_name: str,
    flag_name: str,
    description: str = "",
    default_enabled: bool = False,
) -> str:
    """Create a feature flag in Flagsmith.

    Requires api_key and project_id to be set in the integration config.
    """
    if not _FLAGSMITH_API_KEY:
        return "Error: Flagsmith api_key is not configured. Run flag_setup first and set the api_key."
    if not _FLAGSMITH_PROJECT_ID:
        return "Error: Flagsmith project_id is not configured."

    payload = {
        "name": flag_name,
        "project": int(_FLAGSMITH_PROJECT_ID),
        "default_enabled": default_enabled,
    }
    if description:
        payload["description"] = description

    resp = _api_request("/api/v1/features/", method="POST", data=payload)
    if isinstance(resp, str):
        return resp

    flag_id = resp.get("id", "?")
    return (
        f"Feature flag '{flag_name}' created (id: {flag_id}).\n"
        f"  Default enabled: {default_enabled}\n"
        f"  Description: {description or '(none)'}"
    )


@tool
def flag_toggle(
    project_name: str,
    flag_name: str,
    enabled: bool = True,
    environment: str = "",
) -> str:
    """Toggle a feature flag on or off in Flagsmith.

    If environment is provided, toggles for that specific environment.
    Otherwise uses the default environment.
    """
    if not _FLAGSMITH_API_KEY:
        return "Error: Flagsmith api_key is not configured."

    # First, get the feature by name
    resp = _api_request(f"/api/v1/features/?search={flag_name}")
    if isinstance(resp, str):
        return resp

    results = resp.get("results", resp) if isinstance(resp, dict) else resp
    if not results:
        return f"Feature flag '{flag_name}' not found."

    feature = None
    for f in (results if isinstance(results, list) else [results]):
        if f.get("name") == flag_name:
            feature = f
            break
    if not feature:
        return f"Feature flag '{flag_name}' not found."

    feature_id = feature["id"]

    # Get feature states (environment-specific)
    env_filter = f"&environment__name={environment}" if environment else ""
    states_resp = _api_request(f"/api/v1/features/states/?feature={feature_id}{env_filter}")
    if isinstance(states_resp, str):
        return states_resp

    state_results = states_resp.get("results", states_resp) if isinstance(states_resp, dict) else states_resp
    if not state_results:
        # Try direct update on the feature
        update_resp = _api_request(
            f"/api/v1/features/{feature_id}/",
            method="PATCH",
            data={"default_enabled": enabled},
        )
        if isinstance(update_resp, str):
            return update_resp
        env_label = environment if environment else "default"
        return f"Feature flag '{flag_name}' {'enabled' if enabled else 'disabled'} (environment: {env_label})."

    state = state_results[0] if isinstance(state_results, list) else state_results
    state_id = state.get("id")

    update_resp = _api_request(
        f"/api/v1/features/states/{state_id}/",
        method="PATCH",
        data={"enabled": enabled},
    )
    if isinstance(update_resp, str):
        return update_resp

    env_label = environment if environment else "default"
    return f"Feature flag '{flag_name}' {'enabled' if enabled else 'disabled'} (environment: {env_label})."


@tool
def flag_list(project_name: str) -> str:
    """List all feature flags in the Flagsmith project."""
    if not _FLAGSMITH_API_KEY:
        return "Error: Flagsmith api_key is not configured."

    resp = _api_request("/api/v1/features/")
    if isinstance(resp, str):
        return resp

    results = resp.get("results", resp) if isinstance(resp, dict) else resp
    if not results:
        return "No feature flags found."

    lines = [f"Feature flags ({len(results)}):\n"]
    for f in (results if isinstance(results, list) else [results]):
        name = f.get("name", "?")
        enabled = f.get("default_enabled", False)
        desc = f.get("description", "")
        status = "ON" if enabled else "OFF"
        line = f"  [{status}] {name}"
        if desc:
            line += f" — {desc}"
        lines.append(line)

    return "\n".join(lines)


@tool
def flag_generate_sdk_code(project_name: str, language: str = "typescript") -> str:
    """Generate SDK initialization code for Flagsmith integration.

    Supports: typescript, python, java.
    Outputs the import statement and initialization snippet.
    """
    env_key = _FLAGSMITH_API_KEY or "<YOUR_ENVIRONMENT_KEY>"

    snippets = {
        "typescript": (
            "// Install: npm install flagsmith\n"
            "import flagsmith from 'flagsmith';\n"
            "\n"
            "flagsmith.init({\n"
            f"  environmentID: '{env_key}',\n"
            "  onChange: (oldFlags, params) => {\n"
            "    // Flags have been updated\n"
            "    console.log('Flags updated', flagsmith.getAllFlags());\n"
            "  },\n"
            "});\n"
            "\n"
            "// Check a flag\n"
            "if (flagsmith.hasFeature('my_feature')) {\n"
            "  // Feature is enabled\n"
            "}\n"
            "\n"
            "// Get a remote config value\n"
            "const value = flagsmith.getValue('my_config');\n"
        ),
        "python": (
            "# Install: pip install flagsmith\n"
            "from flagsmith import Flagsmith\n"
            "\n"
            "flagsmith = Flagsmith(\n"
            f"    environment_key='{env_key}',\n"
            ")\n"
            "\n"
            "# Get flags for an identity\n"
            "flags = flagsmith.get_environment_flags()\n"
            "\n"
            "# Check a flag\n"
            "if flags.is_feature_enabled('my_feature'):\n"
            "    # Feature is enabled\n"
            "    pass\n"
            "\n"
            "# Get a remote config value\n"
            "value = flags.get_feature_value('my_config')\n"
        ),
        "java": (
            "// Add to build.gradle: implementation 'com.flagsmith:flagsmith-java-client:5.+'\n"
            "import com.flagsmith.FlagsmithClient;\n"
            "import com.flagsmith.models.Flags;\n"
            "\n"
            "FlagsmithClient flagsmith = FlagsmithClient.newBuilder()\n"
            f"    .setApiKey(\"{env_key}\")\n"
            "    .build();\n"
            "\n"
            "// Get flags\n"
            "Flags flags = flagsmith.getEnvironmentFlags();\n"
            "\n"
            "// Check a flag\n"
            "boolean isEnabled = flags.isFeatureEnabled(\"my_feature\");\n"
            "\n"
            "// Get a remote config value\n"
            "Object value = flags.getFeatureValue(\"my_config\");\n"
        ),
    }

    lang = language.lower().strip()
    if lang not in snippets:
        supported = ", ".join(snippets.keys())
        return f"Unsupported language '{language}'. Supported: {supported}"

    # Optionally write to project directory
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    ext_map = {"typescript": "ts", "python": "py", "java": "java"}
    filename = f"flagsmith_init.{ext_map[lang]}"

    code = snippets[lang]

    if os.path.isdir(project_dir):
        filepath = os.path.join(project_dir, filename)
        try:
            with open(filepath, "w") as fh:
                fh.write(code)
            return f"Generated {filename} in {project_name}/:\n\n{code}"
        except OSError:
            pass

    return f"SDK initialization code ({language}):\n\n{code}"


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class FlagsmithFlagsIntegration(IntegrationBase):
    name = "flagsmith_flags"
    category = "feature_flags"
    icon = "flag"
    color = "#6633B9"

    def __init__(self, config: dict):
        super().__init__(config)
        self.url = config.get("url", "http://localhost:8001")
        self.api_key = config.get("api_key", "")
        self.project_id = config.get("project_id", "")

        # Update module-level config so tool functions can access it
        global _FLAGSMITH_URL, _FLAGSMITH_API_KEY, _FLAGSMITH_PROJECT_ID
        _FLAGSMITH_URL = self.url
        _FLAGSMITH_API_KEY = self.api_key
        _FLAGSMITH_PROJECT_ID = self.project_id

        if config.get("enabled"):
            self._status = IntegrationStatus.CONNECTED
        else:
            self._status = IntegrationStatus.DISCONNECTED

    def get_tools(self) -> list:
        """Return all Flagsmith feature flag tools for the agent."""
        return [
            flag_setup,
            flag_create,
            flag_toggle,
            flag_list,
            flag_generate_sdk_code,
        ]

    async def health_check(self) -> bool:
        """Verify Flagsmith is reachable via GET /api/v1/organisations/."""
        try:
            resp = _api_request("/api/v1/organisations/", base_url=self.url, api_key=self.api_key)
            healthy = not isinstance(resp, str)
            self._status = IntegrationStatus.CONNECTED if healthy else IntegrationStatus.ERROR
            return healthy
        except Exception:
            self._status = IntegrationStatus.ERROR
            return False
