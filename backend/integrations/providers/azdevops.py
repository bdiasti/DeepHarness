"""
Azure DevOps integration — task management via the Azure DevOps REST API.
"""

import os
import json
import base64
from datetime import datetime

import aiohttp
from langchain.tools import tool

from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


# ---------------------------------------------------------------------------
# Module-level config (populated by the integration class at init time)
# ---------------------------------------------------------------------------

_config: dict = {}

NOT_CONFIGURED_MSG = (
    "Azure DevOps not configured. "
    "Set token in integrations.json or use built-in task manager."
)


def _is_configured() -> bool:
    return bool(_config.get("token") and _config.get("organization") and _config.get("project"))


def _api_base() -> str:
    org = _config["organization"]
    project = _config["project"]
    return f"https://dev.azure.com/{org}/{project}/_apis"


def _auth_header() -> dict:
    token = _config["token"]
    b64 = base64.b64encode(f":{token}".encode()).decode()
    return {
        "Authorization": f"Basic {b64}",
        "Content-Type": "application/json-patch+json",
    }


def _json_header() -> dict:
    token = _config["token"]
    b64 = base64.b64encode(f":{token}".encode()).decode()
    return {
        "Authorization": f"Basic {b64}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def azdo_create_work_item(
    project_name: str,
    title: str,
    description: str,
    work_item_type: str = "Task",
    priority: str = "2",
) -> str:
    """Create a work item in Azure DevOps via the REST API."""
    if not _is_configured():
        return NOT_CONFIGURED_MSG

    import asyncio

    async def _create():
        url = f"{_api_base()}/wit/workitems/${work_item_type}?api-version=7.0"
        payload = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": description},
            {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": int(priority)},
        ]
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=_auth_header(), json=payload) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return f"Created work item #{data['id']}: {title}"
                text = await resp.text()
                return f"Error creating work item (HTTP {resp.status}): {text}"

    return asyncio.get_event_loop().run_until_complete(_create())


@tool
def azdo_list_work_items(
    project_name: str,
    sprint: str = "",
    state: str = "",
) -> str:
    """List work items in Azure DevOps using a WIQL query. Optionally filter by sprint or state."""
    if not _is_configured():
        return NOT_CONFIGURED_MSG

    import asyncio

    async def _list():
        conditions = ["[System.TeamProject] = @project"]
        if sprint:
            conditions.append(f"[System.IterationPath] UNDER '{_config['project']}\\{sprint}'")
        if state:
            conditions.append(f"[System.State] = '{state}'")

        wiql = "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE " + " AND ".join(conditions)
        url = f"{_api_base()}/wit/wiql?api-version=7.0"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=_json_header(), json={"query": wiql}) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return f"WIQL query failed (HTTP {resp.status}): {text}"
                data = await resp.json()

            work_items = data.get("workItems", [])
            if not work_items:
                return "No work items found."

            ids = [str(wi["id"]) for wi in work_items[:50]]
            details_url = f"{_api_base()}/wit/workitems?ids={','.join(ids)}&api-version=7.0"
            async with session.get(details_url, headers=_json_header()) as resp:
                if resp.status != 200:
                    return f"Failed to fetch work item details (HTTP {resp.status})."
                details = await resp.json()

        lines = []
        for wi in details.get("value", []):
            fields = wi.get("fields", {})
            lines.append(
                f"#{wi['id']}  {fields.get('System.Title', '?')}  "
                f"| state={fields.get('System.State', '?')}  "
                f"priority={fields.get('Microsoft.VSTS.Common.Priority', '?')}"
            )
        return "\n".join(lines) if lines else "No work items found."

    return asyncio.get_event_loop().run_until_complete(_list())


@tool
def azdo_update_work_item(
    project_name: str,
    item_id: str,
    state: str = "",
    assigned_to: str = "",
) -> str:
    """Update an Azure DevOps work item's state or assignment."""
    if not _is_configured():
        return NOT_CONFIGURED_MSG

    import asyncio

    async def _update():
        url = f"{_api_base()}/wit/workitems/{item_id}?api-version=7.0"
        payload = []
        if state:
            payload.append({"op": "add", "path": "/fields/System.State", "value": state})
        if assigned_to:
            payload.append({"op": "add", "path": "/fields/System.AssignedTo", "value": assigned_to})

        if not payload:
            return "Nothing to update — provide state or assigned_to."

        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=_auth_header(), json=payload) as resp:
                if resp.status == 200:
                    return f"Updated work item #{item_id}."
                text = await resp.text()
                return f"Error updating work item (HTTP {resp.status}): {text}"

    return asyncio.get_event_loop().run_until_complete(_update())


@tool
def azdo_get_sprints(project_name: str) -> str:
    """List sprints (iterations) from Azure DevOps."""
    if not _is_configured():
        return NOT_CONFIGURED_MSG

    import asyncio

    async def _sprints():
        team = f"{_config['project']} Team"
        url = f"{_api_base()}/work/teamsettings/iterations?api-version=7.0"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=_json_header()) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return f"Failed to fetch sprints (HTTP {resp.status}): {text}"
                data = await resp.json()

        lines = []
        for it in data.get("value", []):
            attrs = it.get("attributes", {})
            start = attrs.get("startDate", "?")
            end = attrs.get("finishDate", "?")
            lines.append(f"• {it['name']}  ({start} → {end})")
        return "\n".join(lines) if lines else "No sprints found."

    return asyncio.get_event_loop().run_until_complete(_sprints())


@tool
def azdo_get_board(project_name: str) -> str:
    """Get the board view from Azure DevOps."""
    if not _is_configured():
        return NOT_CONFIGURED_MSG

    import asyncio

    async def _board():
        url = f"{_api_base()}/work/boards?api-version=7.0"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=_json_header()) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return f"Failed to fetch boards (HTTP {resp.status}): {text}"
                data = await resp.json()

        boards = data.get("value", [])
        if not boards:
            return "No boards found."

        lines = []
        for b in boards:
            lines.append(f"• {b['name']}  (id: {b['id']})")
        return "Azure DevOps Boards:\n" + "\n".join(lines)

    return asyncio.get_event_loop().run_until_complete(_board())


@tool
def azdo_link_commit(
    project_name: str,
    item_id: str,
    commit_url: str,
) -> str:
    """Link a git commit to an Azure DevOps work item."""
    if not _is_configured():
        return NOT_CONFIGURED_MSG

    import asyncio

    async def _link():
        url = f"{_api_base()}/wit/workitems/{item_id}?api-version=7.0"
        payload = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "ArtifactLink",
                    "url": commit_url,
                    "attributes": {
                        "name": "Fixed in Commit",
                    },
                },
            }
        ]
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=_auth_header(), json=payload) as resp:
                if resp.status == 200:
                    return f"Linked commit to work item #{item_id}."
                text = await resp.text()
                return f"Error linking commit (HTTP {resp.status}): {text}"

    return asyncio.get_event_loop().run_until_complete(_link())


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class AzDevOpsIntegration(IntegrationBase):
    name = "azure_devops"
    category = "task_management"
    icon = "azure-devops"
    color = "#0078d4"

    def __init__(self, config: dict):
        super().__init__(config)
        global _config
        _config = config
        if _is_configured():
            self._status = IntegrationStatus.CONNECTED
        elif config.get("enabled", False):
            self._status = IntegrationStatus.NOT_CONFIGURED

    def get_tools(self) -> list:
        if not self.config.get("enabled", False):
            return []
        return [
            azdo_create_work_item,
            azdo_list_work_items,
            azdo_update_work_item,
            azdo_get_sprints,
            azdo_get_board,
            azdo_link_commit,
        ]

    async def health_check(self) -> bool:
        if not _is_configured():
            return False
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{_api_base()}/projects?api-version=7.0&$top=1"
                async with session.get(url, headers=_json_header()) as resp:
                    return resp.status == 200
        except Exception:
            return False
