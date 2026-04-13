"""
Notifications integration — send notifications via webhook (Slack, Teams, Ntfy, generic).

Config:
    {
        "provider": "ntfy",
        "webhook_url": "",
        "topic": "harness-notifications",
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


def _load_notify_config(project_name: str) -> dict:
    """Load notification config from the project's integrations.json."""
    config_path = os.path.join(OUTPUT_DIR, project_name, "integrations.json")
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("notifications", {})
        except Exception:
            pass

    # Fall back to environment-based config
    return {
        "provider": os.environ.get("NOTIFY_PROVIDER", "ntfy"),
        "webhook_url": os.environ.get("NOTIFY_WEBHOOK_URL", ""),
        "topic": os.environ.get("NOTIFY_TOPIC", "harness-notifications"),
    }


def _save_notify_config(project_name: str, config: dict) -> str:
    """Save notification config into the project's integrations.json."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."

    config_path = os.path.join(project_dir, "integrations.json")

    # Load existing config or create new
    existing = {}
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass

    existing["notifications"] = config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

    return config_path


def _send_notification(config: dict, message: str, level: str = "info") -> str:
    """Send a notification using the configured provider."""
    provider = config.get("provider", "ntfy")
    webhook_url = config.get("webhook_url", "")
    topic = config.get("topic", "harness-notifications")

    level_prefix = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅",
    }.get(level, "")

    formatted_msg = f"{level_prefix} {message}" if level_prefix else message

    try:
        if provider == "slack":
            if not webhook_url:
                return "Error: Slack webhook_url not configured."
            payload = json.dumps({"text": formatted_msg}).encode()
            req = urllib.request.Request(
                webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return f"Slack notification sent ({resp.status})."

        elif provider == "teams":
            if not webhook_url:
                return "Error: Teams webhook_url not configured."
            payload = json.dumps({"text": formatted_msg}).encode()
            req = urllib.request.Request(
                webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return f"Teams notification sent ({resp.status})."

        elif provider == "ntfy":
            # Determine ntfy URL
            if webhook_url:
                url = f"{webhook_url.rstrip('/')}/{topic}"
            else:
                url = f"http://localhost:8080/{topic}"
            payload = formatted_msg.encode()
            req = urllib.request.Request(url, data=payload, method="POST")
            req.add_header("Title", f"Harness [{level.upper()}]")
            req.add_header("Priority", "high" if level in ("error", "warning") else "default")
            if level == "error":
                req.add_header("Tags", "rotating_light")
            elif level == "success":
                req.add_header("Tags", "white_check_mark")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return f"Ntfy notification sent to '{topic}' ({resp.status})."

        elif provider == "webhook":
            if not webhook_url:
                return "Error: webhook_url not configured."
            payload = json.dumps({"message": formatted_msg, "level": level}).encode()
            req = urllib.request.Request(
                webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return f"Webhook notification sent ({resp.status})."

        else:
            return f"Error: unknown notification provider '{provider}'. Use: slack, teams, ntfy, webhook."

    except urllib.error.URLError as exc:
        return f"Error sending notification: {exc.reason}"
    except Exception as exc:
        return f"Error sending notification: {exc}"


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

@tool
def notify_send(
    project_name: str,
    message: str,
    channel: str = "default",
    level: str = "info",
) -> str:
    """Send a notification. Level: info, warning, error, success.

    Reads webhook config from the project's integrations.json.
    Supports providers: slack, teams, ntfy, webhook.
    """
    if level not in ("info", "warning", "error", "success"):
        return f"Error: invalid level '{level}'. Use: info, warning, error, success."

    config = _load_notify_config(project_name)
    if not config:
        return "Error: notification config not found. Run notify_setup first."

    # Override topic/channel if specified
    if channel != "default":
        config["topic"] = channel

    return _send_notification(config, message, level)


@tool
def notify_setup(
    project_name: str,
    provider: str = "ntfy",
    webhook_url: str = "",
    topic: str = "",
) -> str:
    """Configure notification provider for the project.

    Providers: ntfy (default), slack, teams, webhook.
    For ntfy: defaults to http://localhost:8080/{topic} or https://ntfy.sh/{topic}.
    Saves config to the project's integrations.json.
    """
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."

    if provider not in ("slack", "teams", "ntfy", "webhook"):
        return f"Error: unsupported provider '{provider}'. Use: slack, teams, ntfy, webhook."

    config = {
        "provider": provider,
        "webhook_url": webhook_url,
        "topic": topic or "harness-notifications",
        "enabled": True,
    }

    # Set sensible defaults for ntfy
    if provider == "ntfy" and not webhook_url:
        config["webhook_url"] = "http://localhost:8080"

    saved_path = _save_notify_config(project_name, config)
    if saved_path.startswith("Error"):
        return saved_path

    url_display = webhook_url or config.get("webhook_url", "(not set)")
    return (
        f"Notifications configured for '{project_name}':\n"
        f"  Provider: {provider}\n"
        f"  URL: {url_display}\n"
        f"  Topic: {config['topic']}\n"
        f"  Config saved to: {saved_path}\n\n"
        f"Run notify_test to verify the configuration."
    )


@tool
def notify_test(project_name: str) -> str:
    """Send a test notification to verify the current configuration works."""
    config = _load_notify_config(project_name)
    if not config:
        return "Error: notification config not found. Run notify_setup first."

    provider = config.get("provider", "unknown")
    return _send_notification(
        config,
        f"Test notification from project '{project_name}'. Configuration is working.",
        level="info",
    )


@tool
def notify_on_deploy(project_name: str, environment: str, status: str) -> str:
    """Send a formatted deployment notification.

    Args:
        environment: Target environment (e.g. staging, production).
        status: Deployment status (e.g. success, failed, rolling_back).
    """
    config = _load_notify_config(project_name)
    if not config:
        return "Error: notification config not found. Run notify_setup first."

    level = "success" if status.lower() in ("success", "completed") else "error"
    message = (
        f"Deploy [{project_name}] to {environment.upper()}: {status.upper()}\n"
        f"Project: {project_name}\n"
        f"Environment: {environment}\n"
        f"Status: {status}"
    )
    return _send_notification(config, message, level)


@tool
def notify_on_test_fail(project_name: str, test_count: int, fail_count: int) -> str:
    """Send a formatted test failure notification.

    Args:
        test_count: Total number of tests executed.
        fail_count: Number of tests that failed.
    """
    config = _load_notify_config(project_name)
    if not config:
        return "Error: notification config not found. Run notify_setup first."

    pass_count = test_count - fail_count
    pass_rate = (pass_count / test_count * 100) if test_count > 0 else 0

    if fail_count == 0:
        level = "success"
        message = (
            f"All tests passing for '{project_name}'!\n"
            f"  {test_count} tests — 100% pass rate"
        )
    else:
        level = "error"
        message = (
            f"Test failures detected in '{project_name}'!\n"
            f"  Total: {test_count} | Passed: {pass_count} | Failed: {fail_count}\n"
            f"  Pass rate: {pass_rate:.1f}%"
        )

    return _send_notification(config, message, level)


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class NotificationsIntegration(IntegrationBase):
    name = "notifications"
    category = "notifications"
    icon = "bell"
    color = "#F59E0B"

    def __init__(self, config: dict):
        super().__init__(config)
        # Push config into environment for tool functions
        if config.get("provider"):
            os.environ["NOTIFY_PROVIDER"] = config["provider"]
        if config.get("webhook_url"):
            os.environ["NOTIFY_WEBHOOK_URL"] = config["webhook_url"]
        if config.get("topic"):
            os.environ["NOTIFY_TOPIC"] = config["topic"]

        if config.get("enabled"):
            self._status = IntegrationStatus.CONNECTED
        else:
            self._status = IntegrationStatus.DISCONNECTED

    def get_tools(self) -> list:
        """Return all notification tools for the agent."""
        return [
            notify_send,
            notify_setup,
            notify_test,
            notify_on_deploy,
            notify_on_test_fail,
        ]

    async def health_check(self) -> bool:
        """Check if the configured notification endpoint is reachable."""
        provider = self.config.get("provider", "ntfy")
        webhook_url = self.config.get("webhook_url", "")
        topic = self.config.get("topic", "harness-notifications")

        try:
            if provider == "ntfy":
                url = f"{webhook_url.rstrip('/')}/{topic}" if webhook_url else f"http://localhost:8080/{topic}"
                # HEAD request to check if ntfy topic endpoint is reachable
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    healthy = resp.status == 200
            elif provider in ("slack", "teams", "webhook"):
                if not webhook_url:
                    self._status = IntegrationStatus.NOT_CONFIGURED
                    return False
                # Just check the URL is reachable with a HEAD-like request
                req = urllib.request.Request(webhook_url, method="HEAD")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    healthy = resp.status < 500
            else:
                self._status = IntegrationStatus.NOT_CONFIGURED
                return False

            self._status = IntegrationStatus.CONNECTED if healthy else IntegrationStatus.ERROR
            return healthy
        except Exception:
            self._status = IntegrationStatus.ERROR
            return False
