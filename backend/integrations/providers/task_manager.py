"""
Task Manager Integration — Connects to the Task Manager microservice API.

The Task Manager runs as a standalone service at http://localhost:8100
with PostgreSQL storage. If the service is not available, tools return
helpful error messages.
"""

import json
import urllib.request
import urllib.error
from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus

TASK_MANAGER_URL = "http://localhost:8100"


def _api(method: str, path: str, body: dict = None) -> dict:
    """Call the Task Manager API."""
    url = f"{TASK_MANAGER_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return {"error": f"HTTP {e.code}: {error_body[:200]}"}
    except urllib.error.URLError:
        return {"error": f"Task Manager not available at {TASK_MANAGER_URL}. Start it with: docker compose -f docker-compose.infra.yml up task-manager -d"}
    except Exception as e:
        return {"error": str(e)[:200]}


@tool
def task_create_item(
    project_name: str,
    title: str,
    description: str = "",
    item_type: str = "task",
    priority: str = "P2",
    assigned_to: str = "",
    sprint_id: str = "",
) -> str:
    """Create a work item in the Task Manager.

    Args:
        project_name: Project identifier
        title: Item title
        description: Detailed description
        item_type: Type: task, bug, story, epic
        priority: Priority: P0 (critical), P1 (high), P2 (medium), P3 (low)
        assigned_to: Person assigned to this item
        sprint_id: UUID of the sprint (optional)
    """
    body = {
        "project": project_name,
        "title": title,
        "description": description,
        "item_type": item_type,
        "priority": priority,
        "assigned_to": assigned_to,
    }
    if sprint_id:
        body["sprint_id"] = sprint_id

    result = _api("POST", "/api/items", body)
    if "error" in result:
        return f"ERROR: {result['error']}"
    return f"ITEM CREATED: [{result['priority']}] {result['title']} (ID: {result['id']}, status: {result['status']})"


@tool
def task_list_items(
    project_name: str,
    status: str = "",
    priority: str = "",
    sprint_id: str = "",
    assigned_to: str = "",
) -> str:
    """List work items from the Task Manager with optional filters.

    Args:
        project_name: Project identifier
        status: Filter by status (todo, in_progress, review, done)
        priority: Filter by priority (P0, P1, P2, P3)
        sprint_id: Filter by sprint UUID
        assigned_to: Filter by assignee
    """
    params = f"?project={project_name}"
    if status:
        params += f"&status={status}"
    if priority:
        params += f"&priority={priority}"
    if sprint_id:
        params += f"&sprint_id={sprint_id}"
    if assigned_to:
        params += f"&assigned_to={assigned_to}"

    result = _api("GET", f"/api/items{params}")
    if isinstance(result, dict) and "error" in result:
        return f"ERROR: {result['error']}"

    if not result:
        return f"No items found for project '{project_name}' with the given filters."

    lines = [f"ITEMS for {project_name} ({len(result)} found):\n"]
    for item in result:
        icon = {"todo": "⬜", "in_progress": "🔵", "review": "🟡", "done": "✅"}.get(item["status"], "⬜")
        lines.append(f"  {icon} [{item['priority']}] {item['title']} — {item['status']} (ID: {item['id'][:8]})")
    return "\n".join(lines)


@tool
def task_update_item(
    project_name: str,
    item_id: str,
    status: str = "",
    assigned_to: str = "",
    priority: str = "",
    title: str = "",
) -> str:
    """Update a work item's status, assignment, or priority.

    Args:
        project_name: Project identifier
        item_id: UUID of the item to update
        status: New status: todo, in_progress, review, done
        assigned_to: New assignee
        priority: New priority: P0, P1, P2, P3
        title: New title
    """
    body = {}
    if status:
        body["status"] = status
    if assigned_to:
        body["assigned_to"] = assigned_to
    if priority:
        body["priority"] = priority
    if title:
        body["title"] = title

    if not body:
        return "No fields to update."

    result = _api("PATCH", f"/api/items/{item_id}", body)
    if "error" in result:
        return f"ERROR: {result['error']}"
    return f"ITEM UPDATED: [{result['priority']}] {result['title']} → {result['status']}"


@tool
def task_create_sprint(
    project_name: str,
    name: str,
    goal: str = "",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """Create a sprint in the Task Manager.

    Args:
        project_name: Project identifier
        name: Sprint name (e.g. "Sprint 1")
        goal: Sprint goal
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    body = {"project": project_name, "name": name, "goal": goal}
    if start_date:
        body["start_date"] = start_date
    if end_date:
        body["end_date"] = end_date

    result = _api("POST", "/api/sprints", body)
    if "error" in result:
        return f"ERROR: {result['error']}"
    return f"SPRINT CREATED: {result['name']} (ID: {result['id']}, status: {result['status']})"


@tool
def task_list_sprints(project_name: str) -> str:
    """List all sprints for a project.

    Args:
        project_name: Project identifier
    """
    result = _api("GET", f"/api/sprints?project={project_name}")
    if isinstance(result, dict) and "error" in result:
        return f"ERROR: {result['error']}"

    if not result:
        return f"No sprints found for '{project_name}'."

    lines = [f"SPRINTS for {project_name}:\n"]
    for s in result:
        dates = f" ({s['start_date']} → {s.get('end_date', '?')})" if s.get("start_date") else ""
        lines.append(f"  [{s['status']}] {s['name']}{dates} — {s['item_count']} items (ID: {s['id'][:8]})")
    return "\n".join(lines)


@tool
def task_board(project_name: str, sprint_id: str = "") -> str:
    """Show the kanban board — columns: todo, in_progress, review, done.

    Args:
        project_name: Project identifier
        sprint_id: Optional sprint UUID to filter
    """
    params = f"?project={project_name}"
    if sprint_id:
        params += f"&sprint_id={sprint_id}"

    result = _api("GET", f"/api/board{params}")
    if "error" in result:
        return f"ERROR: {result['error']}"

    lines = [f"BOARD for {project_name} ({result['total']} items):\n"]
    headers = {"todo": "⬜ TODO", "in_progress": "🔵 IN PROGRESS", "review": "🟡 REVIEW", "done": "✅ DONE"}

    for col in result["columns"]:
        lines.append(f"  {headers.get(col['status'], col['status'])} ({col['count']})")
        for item in col["items"]:
            lines.append(f"    [{item['priority']}] {item['title']}")
        if not col["items"]:
            lines.append("    (empty)")
        lines.append("")
    return "\n".join(lines)


@tool
def task_link_commit(
    project_name: str,
    item_id: str,
    commit_hash: str,
    message: str = "",
    branch: str = "",
) -> str:
    """Link a git commit to a work item for traceability.

    Args:
        project_name: Project identifier
        item_id: UUID of the work item
        commit_hash: Git commit hash
        message: Commit message
        branch: Branch name
    """
    body = {
        "work_item_id": item_id,
        "commit_hash": commit_hash,
        "message": message,
        "branch": branch,
    }
    result = _api("POST", "/api/commits", body)
    if "error" in result:
        return f"ERROR: {result['error']}"
    return f"COMMIT LINKED: {commit_hash[:8]} → item {item_id[:8]}"


class TaskManagerIntegration(IntegrationBase):
    name = "task-manager"
    category = "task_management"
    icon = "clipboard-list"
    color = "#f59e0b"

    def __init__(self, config: dict):
        super().__init__(config)
        self._status = IntegrationStatus.CONNECTED

    def get_tools(self) -> list:
        return [
            task_create_item,
            task_list_items,
            task_update_item,
            task_create_sprint,
            task_list_sprints,
            task_board,
            task_link_commit,
        ]

    async def health_check(self) -> bool:
        result = _api("GET", "/health")
        if "error" not in result and result.get("status") == "ok":
            self._status = IntegrationStatus.CONNECTED
            return True
        self._status = IntegrationStatus.DISCONNECTED
        return False
