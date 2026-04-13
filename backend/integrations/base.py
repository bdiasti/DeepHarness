"""
IntegrationBase — Interface that all integrations implement.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class IntegrationStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"


class IntegrationBase(ABC):
    """Base class for all integrations."""

    name: str = "unknown"
    category: str = "unknown"  # version_control, task_management, testing, deploy
    icon: str = "plug"
    color: str = "#6366f1"

    def __init__(self, config: dict):
        self.config = config
        self._status = IntegrationStatus.NOT_CONFIGURED

    @property
    def status(self) -> IntegrationStatus:
        return self._status

    @abstractmethod
    def get_tools(self) -> list:
        """Return list of @tool functions this integration provides to the agent."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the integration is reachable and working."""
        ...

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "icon": self.icon,
            "color": self.color,
            "status": self.status.value,
            "config": {k: v for k, v in self.config.items() if k not in ("token", "password", "api_key")},
        }
