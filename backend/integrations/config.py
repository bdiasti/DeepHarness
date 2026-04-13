"""
Integration Config — Loads integrations.json from a project directory.
"""

import json
import os
from typing import Optional

from tools import OUTPUT_DIR


DEFAULT_CONFIG = {
    "version_control": {
        "provider": "gitlab",
        "enabled": False,
    },
    "task_management": {
        "provider": "builtin",
        "enabled": True,
    },
    "testing": {
        "provider": "playwright",
        "enabled": False,
    },
    "deploy": {
        "local": {"provider": "docker", "enabled": False},
        "staging": {"provider": "k3s", "enabled": False},
        "production": {"provider": "k8s", "enabled": False},
    },
}


def load_project_integrations(project_name: str) -> dict:
    """Load integrations config from a project's integrations.json."""
    config_path = os.path.join(OUTPUT_DIR, project_name, "integrations.json")
    if os.path.isfile(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def save_project_integrations(project_name: str, config: dict):
    """Save integrations config to a project."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    os.makedirs(project_dir, exist_ok=True)
    config_path = os.path.join(project_dir, "integrations.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
