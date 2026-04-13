"""
Integration Registry — Manages all available integrations and provides tools to agents.
"""

from typing import Optional
from integrations.base import IntegrationBase, IntegrationStatus


class IntegrationRegistry:
    """Central registry for all integrations."""

    def __init__(self):
        self._integrations: dict[str, IntegrationBase] = {}

    def register(self, integration: IntegrationBase):
        """Register an integration instance."""
        key = f"{integration.category}:{integration.name}"
        self._integrations[key] = integration

    def get(self, category: str, name: str) -> Optional[IntegrationBase]:
        return self._integrations.get(f"{category}:{name}")

    def get_all(self) -> list[IntegrationBase]:
        return list(self._integrations.values())

    def get_by_category(self, category: str) -> list[IntegrationBase]:
        return [i for i in self._integrations.values() if i.category == category]

    def get_tools(self) -> list:
        """Get all tools from all registered integrations."""
        tools = []
        for integration in self._integrations.values():
            if integration.status in (IntegrationStatus.CONNECTED, IntegrationStatus.NOT_CONFIGURED):
                tools.extend(integration.get_tools())
        return tools

    def to_dict(self) -> list[dict]:
        return [i.to_dict() for i in self._integrations.values()]
