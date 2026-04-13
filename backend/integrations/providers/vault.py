"""
HashiCorp Vault integration — secrets management via Vault in dev mode (Docker).

Config:
    {
        "url": "http://localhost:8200",   (or VAULT_ADDR env var)
        "token": "<from VAULT_TOKEN env>",
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


# Vault connection settings (from environment)
_VAULT_URL = os.environ.get("VAULT_ADDR", "http://localhost:8200")
_VAULT_TOKEN = os.environ.get("VAULT_TOKEN", "")


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


def _vault_request(method: str, path: str, data: dict | None = None,
                   vault_url: str = _VAULT_URL, token: str = _VAULT_TOKEN) -> dict | str:
    """Make an HTTP request to the Vault API."""
    url = f"{vault_url}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("X-Vault-Token", token)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return f"Error (HTTP {e.code}): {body}"
    except urllib.error.URLError as e:
        return f"Error: could not reach Vault — {e}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

@tool
def vault_setup(project_name: str) -> str:
    """Start HashiCorp Vault in dev mode via Docker and return connection instructions."""
    # Check if already running
    check = _run_cmd([
        "docker", "ps", "--filter", "name=vault",
        "--format", "{{.ID}}  {{.Status}}",
    ])
    if check and check != "(no output)" and not check.startswith("Error"):
        return (
            f"Vault is already running:\n{check}\n\n"
            f"URL:   {_VAULT_URL}\n"
            f"Token: {_VAULT_TOKEN}"
        )

    result = _run_cmd([
        "docker", "run", "-d",
        "--name", "vault",
        "-p", "8200:8200",
        "-e", f"VAULT_DEV_ROOT_TOKEN_ID={_VAULT_TOKEN}",
        "--cap-add=IPC_LOCK",
        "hashicorp/vault",
    ])

    if result.startswith("Error"):
        return f"Failed to start Vault: {result}"

    return (
        f"Vault started in dev mode for '{project_name}'.\n\n"
        f"  Container: {result[:12]}\n"
        f"  URL:       {_VAULT_URL}\n"
        f"  Root Token: {_VAULT_TOKEN}\n\n"
        f"  export VAULT_ADDR={_VAULT_URL}\n"
        f"  export VAULT_TOKEN={_VAULT_TOKEN}\n\n"
        "Note: Dev mode is NOT for production. All data is in-memory."
    )


@tool
def vault_store_secret(project_name: str, path: str, key: str, value: str) -> str:
    """Store a secret in Vault at the given path with the specified key and value."""
    result = _vault_request(
        "POST",
        f"/v1/secret/data/{path}",
        data={"data": {key: value}},
    )
    if isinstance(result, str) and result.startswith("Error"):
        return result
    return f"Secret stored at secret/data/{path} (key='{key}')."


@tool
def vault_get_secret(project_name: str, path: str, key: str) -> str:
    """Retrieve a secret from Vault. The value is returned but should be handled carefully."""
    result = _vault_request("GET", f"/v1/secret/data/{path}")
    if isinstance(result, str) and result.startswith("Error"):
        return result

    try:
        data = result["data"]["data"]
        value = data.get(key)
        if value is None:
            return f"Key '{key}' not found at path 'secret/data/{path}'. Available keys: {list(data.keys())}"
        # Mask in output for safety (show first/last char only)
        masked = value[0] + "*" * (len(value) - 2) + value[-1] if len(value) > 2 else "***"
        return f"Secret at secret/data/{path} key='{key}': {masked}"
    except (KeyError, TypeError) as e:
        return f"Error parsing Vault response: {e}"


@tool
def vault_list_secrets(project_name: str, path: str = "") -> str:
    """List all secret keys at the given Vault path."""
    result = _vault_request("LIST", f"/v1/secret/metadata/{path}")
    if isinstance(result, str) and result.startswith("Error"):
        return result

    try:
        keys = result.get("data", {}).get("keys", [])
        if not keys:
            return f"No secrets found at path 'secret/metadata/{path}'."
        lines = [f"[Vault Secrets] path=secret/metadata/{path} ({len(keys)} entries)"]
        for k in keys:
            lines.append(f"  - {k}")
        return "\n".join(lines)
    except (KeyError, TypeError) as e:
        return f"Error parsing Vault response: {e}"


@tool
def vault_generate_env(project_name: str, paths: list[str]) -> str:
    """Generate a .env file from Vault secrets. Reads each path and writes key=value pairs. Values are NEVER logged."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."

    env_lines = []
    errors = []

    for path in paths:
        result = _vault_request("GET", f"/v1/secret/data/{path}")
        if isinstance(result, str) and result.startswith("Error"):
            errors.append(f"  - {path}: {result}")
            continue
        try:
            data = result["data"]["data"]
            for k, v in data.items():
                env_lines.append(f"{k}={v}")
        except (KeyError, TypeError):
            errors.append(f"  - {path}: failed to parse response")

    env_path = os.path.join(project_dir, ".env")
    with open(env_path, "w") as f:
        f.write("\n".join(env_lines) + "\n")

    summary = [f".env file written to {env_path} with {len(env_lines)} variable(s)."]
    if errors:
        summary.append(f"Errors reading {len(errors)} path(s):")
        summary.extend(errors)
    # Never log actual values
    summary.append("(Secret values are written to file only, not logged.)")
    return "\n".join(summary)


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class VaultIntegration(IntegrationBase):
    name = "vault"
    category = "secrets"
    icon = "lock"
    color = "#FFCF25"

    DEFAULT_CONFIG = {
        "url": os.environ.get("VAULT_ADDR", "http://localhost:8200"),
        "token": os.environ.get("VAULT_TOKEN", ""),
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
            vault_setup,
            vault_store_secret,
            vault_get_secret,
            vault_list_secrets,
            vault_generate_env,
        ]

    async def health_check(self) -> bool:
        """Check if Vault is reachable via /v1/sys/health."""
        url = self.config.get("url", _VAULT_URL)
        try:
            req = urllib.request.Request(f"{url}/v1/sys/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                healthy = resp.status == 200
        except Exception:
            healthy = False

        self._status = IntegrationStatus.CONNECTED if healthy else IntegrationStatus.ERROR
        return healthy
