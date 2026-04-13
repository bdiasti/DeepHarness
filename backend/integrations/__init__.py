"""
Integrations Module — Decoupled external service connections via MCP pattern.

Each integration:
1. Implements IntegrationBase
2. Registers tools the agent can call
3. Emits events visible in Mission Control
4. Is configured per-project via integrations.json

Registry manages all integrations and provides them to the agent as tools.
"""

from integrations.base import IntegrationBase, IntegrationStatus
from integrations.registry import IntegrationRegistry
from integrations.config import load_project_integrations

__all__ = [
    "IntegrationBase",
    "IntegrationStatus",
    "IntegrationRegistry",
    "load_project_integrations",
]
