"""
DeepHarness — Engineering Platform Server

FastAPI server with SSE streaming and template switching.
Start with: python server.py
"""

import json
import uuid
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage, AIMessage

from agent import get_agent, list_templates, list_personas, list_stacks, list_skills_library, list_project_types
from tools import AVAILABLE_MODELS, AVAILABLE_TOOL_TEMPLATES, MIDDLEWARE_OPTIONS, OUTPUT_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    print()
    print("=" * 50)
    print("  DeepHarness — Engineering Platform")
    print("  http://localhost:8000")
    print("=" * 50)
    print()
    yield

app = FastAPI(title="DeepHarness", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Template endpoints ---

@app.get("/api/templates")
async def get_templates():
    """Legacy: list personas as templates."""
    return {"templates": list_templates()}


@app.get("/api/personas")
async def get_personas():
    """List all available personas (behaviors)."""
    return {"personas": list_personas()}


@app.get("/api/stacks")
async def get_stacks():
    """Legacy: replaced by skills library."""
    return {"stacks": list_stacks()}


@app.get("/api/project-types")
async def get_project_types():
    """List all project types with their constitutions."""
    return {"project_types": list_project_types()}


@app.get("/api/skills-library")
async def get_skills_library():
    """List all skills available in the library, organized by category."""
    skills = list_skills_library()
    # Group by category
    by_category: dict[str, list[dict]] = {}
    for s in skills:
        by_category.setdefault(s["category"], []).append(s)
    return {"skills": skills, "by_category": by_category}


# --- Harness metrics (in-memory) ---

_harness_metrics = {
    "total_sensor_runs": 0,
    "sensor_passes": 0,
    "sensor_fails": 0,
    "corrections_made": 0,
    "tools_by_name": {},
    "sensor_by_name": {},
}


def _track_tool(tool_name: str, category: str, sensor_status: str = None):
    """Track tool/sensor usage for metrics."""
    _harness_metrics["tools_by_name"][tool_name] = _harness_metrics["tools_by_name"].get(tool_name, 0) + 1
    if category == "sensor":
        _harness_metrics["total_sensor_runs"] += 1
        _harness_metrics["sensor_by_name"][tool_name] = _harness_metrics["sensor_by_name"].get(tool_name, 0) + 1
        if sensor_status == "pass":
            _harness_metrics["sensor_passes"] += 1
        elif sensor_status == "fail":
            _harness_metrics["sensor_fails"] += 1


# --- Chat endpoint with SSE streaming ---

FILE_TOOLS = {"write_file", "edit_file", "generate_agent_code"}
SENSOR_TOOLS = {"run_linter", "validate_structure", "check_directives", "review_code", "harness_status", "read_harness_rules", "update_harness_rules", "read_agents_md", "update_agents_md", "scan_drift", "validate_before_write", "create_sdd", "get_sdd"}
INTEGRATION_TOOLS = {
    # Git
    "git_init", "git_commit", "git_push", "git_create_branch", "git_diff", "git_log", "git_status", "git_create_mr",
    # Docker
    "docker_build", "docker_run", "docker_stop", "docker_logs", "docker_status", "docker_compose_up", "docker_compose_down",
    # Task Manager
    "task_create_item", "task_list_items", "task_update_item", "task_create_sprint", "task_list_sprints", "task_board", "task_link_commit",
    # Azure DevOps
    "azdo_create_work_item", "azdo_list_work_items", "azdo_update_work_item", "azdo_get_sprints", "azdo_get_board", "azdo_link_commit",
    # Playwright
    "e2e_run_tests", "e2e_run_single_test", "e2e_show_report", "e2e_list_tests", "e2e_init",
    # K3s / K8s
    "k3s_deploy", "k3s_status", "k3s_logs", "k3s_rollback",
    "k8s_deploy", "k8s_status", "k8s_logs", "k8s_scale", "k8s_rollback",
    # SonarQube
    "sonar_scan", "sonar_quality_gate", "sonar_issues", "sonar_setup",
    # CI/CD
    "cicd_generate_pipeline", "cicd_validate_pipeline", "cicd_add_stage", "cicd_show_pipeline",
    # Notifications
    "notify_send", "notify_setup", "notify_test", "notify_on_deploy", "notify_on_test_fail",
    # Monitoring
    "monitoring_setup", "monitoring_status", "monitoring_start", "monitoring_stop", "monitoring_check_alerts", "monitoring_add_dashboard",
    # Vault
    "vault_setup", "vault_store_secret", "vault_get_secret", "vault_list_secrets", "vault_generate_env",
    # Flyway
    "db_create_migration", "db_migrate", "db_status", "db_rollback", "db_list_migrations",
    # Registry
    "registry_setup", "registry_push", "registry_list", "registry_tag", "registry_status",
    # Semgrep
    "security_scan", "security_report", "security_fix_suggestions", "security_setup",
    # Flagsmith
    "flag_setup", "flag_create", "flag_toggle", "flag_list", "flag_generate_sdk_code",
    # Meta
    "integration_status", "configure_integration", "deploy",
}

@app.post("/api/chat")
async def chat(request: Request):
    """Stream agent responses via SSE. Accepts template_id to switch roles."""
    body = await request.json()
    message = body.get("message", "")
    thread_id = body.get("thread_id") or str(uuid.uuid4())
    persona_id = body.get("persona_id") or body.get("template_id") or "deepagent_generator"
    skill_ids = body.get("skill_ids") or []
    project_type_id = body.get("project_type_id") or "custom"

    print(f"\n[CHAT] project={project_type_id} persona={persona_id} skills={skill_ids} thread={thread_id[:8]} msg={message[:80]}")
    agent = get_agent(persona_id, skill_ids, project_type_id)
    print(f"[CHAT] agent={agent.name if hasattr(agent, 'name') else 'unknown'}")
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 150}
    input_data = {"messages": [HumanMessage(content=message)]}

    async def event_generator():
        try:
            yield {
                "event": "metadata",
                "data": json.dumps({"thread_id": thread_id, "persona_id": persona_id, "project_type_id": project_type_id, "skill_ids": skill_ids}),
            }

            files_changed = False

            async for event in agent.astream_events(input_data, config=config, version="v2"):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        content = chunk.content
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    yield {
                                        "event": "token",
                                        "data": json.dumps({"content": block["text"]}),
                                    }
                        elif isinstance(content, str):
                            yield {
                                "event": "token",
                                "data": json.dumps({"content": content}),
                            }

                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    is_sensor = tool_name in SENSOR_TOOLS
                    is_integration = tool_name in INTEGRATION_TOOLS
                    category = "sensor" if is_sensor else "integration" if is_integration else "tool"
                    print(f"  [{category.upper()}] {tool_name} called")
                    yield {
                        "event": "tool_start",
                        "data": json.dumps({
                            "tool": tool_name,
                            "category": category,
                            "input": str(event["data"].get("input", ""))[:200],
                        }),
                    }

                elif kind == "on_tool_end":
                    tool_name = event["name"]
                    is_sensor = tool_name in SENSOR_TOOLS
                    is_integration = tool_name in INTEGRATION_TOOLS
                    category = "sensor" if is_sensor else "integration" if is_integration else "tool"
                    output = event["data"].get("output", "")
                    output_str = str(output.content) if hasattr(output, "content") else str(output)

                    # Determine sensor result (PASS/FAIL)
                    sensor_status = None
                    if is_sensor:
                        if any(w in output_str for w in ["PASSED", "VALID", "OK", "HEALTHY", "No issues"]):
                            sensor_status = "pass"
                        elif any(w in output_str for w in ["ISSUES", "VIOLATIONS", "FAIL", "NEEDS ATTENTION"]):
                            sensor_status = "fail"

                    print(f"  [{category.upper()}] {tool_name} done: {sensor_status or ''} {output_str[:100]}")
                    _track_tool(tool_name, category, sensor_status)
                    event_data = {
                        "tool": tool_name,
                        "category": category,
                        "output": output_str[:5000],
                    }
                    if sensor_status:
                        event_data["sensor_status"] = sensor_status
                    yield {
                        "event": "tool_end",
                        "data": json.dumps(event_data),
                    }
                    if tool_name in FILE_TOOLS:
                        files_changed = True
                        yield {"event": "file_changed", "data": "{}"}

            # Final AI message
            final_state = agent.get_state(config)
            messages = final_state.values.get("messages", [])
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    content = msg.content
                    if isinstance(content, list):
                        content = "".join(
                            block["text"] if isinstance(block, dict) and block.get("type") == "text"
                            else str(block) if not isinstance(block, dict)
                            else ""
                            for block in content
                        )
                    yield {
                        "event": "message_complete",
                        "data": json.dumps({"content": content, "role": "assistant"}),
                    }
                    break

            if files_changed:
                yield {"event": "file_changed", "data": "{}"}

            yield {"event": "done", "data": "{}"}

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }

    return EventSourceResponse(event_generator())


# --- Project file endpoints ---

@app.get("/api/projects")
async def get_projects():
    """List all generated projects."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    projects = []
    for name in sorted(os.listdir(OUTPUT_DIR)):
        if name.startswith("."):
            continue
        project_dir = os.path.join(OUTPUT_DIR, name)
        if os.path.isdir(project_dir):
            files = []
            for root, dirs, filenames in os.walk(project_dir):
                for fname in sorted(filenames):
                    fpath = os.path.join(root, fname)
                    rel = os.path.relpath(fpath, project_dir).replace("\\", "/")
                    files.append({"name": rel, "size": os.path.getsize(fpath)})
            projects.append({"name": name, "files": files})
    return {"projects": projects}


@app.get("/api/projects/{project_name}/files")
async def get_project_files(project_name: str):
    """List all files in a project recursively."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return {"error": "Project not found", "files": []}
    files = []
    for root, dirs, filenames in os.walk(project_dir):
        for fname in sorted(filenames):
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, project_dir).replace("\\", "/")
            files.append({"name": rel, "size": os.path.getsize(fpath)})
    return {"project": project_name, "files": files}


@app.get("/api/projects/{project_name}/files/{filename:path}")
async def read_project_file(project_name: str, filename: str):
    """Read file contents (supports subpaths)."""
    filepath = os.path.join(OUTPUT_DIR, project_name, filename)
    if not os.path.isfile(filepath):
        return {"error": "File not found"}
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return {"project": project_name, "filename": filename, "content": content}


@app.get("/api/projects/{project_name}/download/{filename:path}")
async def download_project_file(project_name: str, filename: str):
    """Download a file."""
    filepath = os.path.join(OUTPUT_DIR, project_name, filename)
    if not os.path.isfile(filepath):
        return {"error": "File not found"}
    return FileResponse(filepath, filename=os.path.basename(filename))


# --- Integration health checks ---

@app.get("/api/integrations/health")
async def check_integrations_health():
    """Check which integrations are online/reachable."""
    import subprocess
    import urllib.request

    results = {}

    # Helper: check URL
    def check_url(name, url, timeout=3):
        try:
            req = urllib.request.Request(url, method="GET")
            resp = urllib.request.urlopen(req, timeout=timeout)
            return {"status": "online", "code": resp.status}
        except Exception as e:
            return {"status": "offline", "error": str(e)[:100]}

    # Helper: check command
    def check_cmd(name, cmd, timeout=5):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {"status": "online" if r.returncode == 0 else "error", "output": r.stdout[:80]}
        except FileNotFoundError:
            return {"status": "not_installed", "error": f"{cmd[0]} not found in PATH"}
        except Exception as e:
            return {"status": "offline", "error": str(e)[:100]}

    # Git
    results["git"] = check_cmd("git", ["git", "--version"])

    # Docker
    results["docker"] = check_cmd("docker", ["docker", "info", "--format", "{{.ServerVersion}}"])

    # SonarQube
    results["sonarqube"] = check_url("sonarqube", "http://localhost:9000/api/system/status")

    # Vault
    results["vault"] = check_url("vault", "http://localhost:8200/v1/sys/health")

    # PostgreSQL
    results["postgres"] = check_cmd("postgres", ["docker", "exec", "harness-postgres", "pg_isready", "-U", "app"])

    # Prometheus
    results["prometheus"] = check_url("prometheus", "http://localhost:9090/-/healthy")

    # Grafana
    results["grafana"] = check_url("grafana", "http://localhost:3001/api/health")

    # Docker Registry
    results["registry"] = check_url("registry", "http://localhost:5000/v2/")

    # Ntfy
    results["ntfy"] = check_url("ntfy", "http://localhost:8080/v1/health")

    # Flagsmith
    results["flagsmith"] = check_url("flagsmith", "http://localhost:8001/health")

    # Task Manager
    results["task_manager"] = check_url("task_manager", "http://localhost:8100/health")

    # Semgrep
    results["semgrep"] = check_cmd("semgrep", ["semgrep", "--version"])

    # Playwright
    results["playwright"] = check_cmd("playwright", ["npx", "playwright", "--version"])

    # kubectl
    results["kubectl"] = check_cmd("kubectl", ["kubectl", "version", "--client", "--short"])

    return {"integrations": results}


# --- Integration endpoints ---

@app.get("/api/projects/{project_name}/integrations")
async def get_project_integrations(project_name: str):
    """Get integration config for a project."""
    from integrations.config import load_project_integrations
    config = load_project_integrations(project_name)
    return {"project": project_name, "integrations": config}


@app.post("/api/projects/{project_name}/integrations")
async def update_project_integrations(project_name: str, request: Request):
    """Update integration config for a project."""
    from integrations.config import save_project_integrations
    body = await request.json()
    save_project_integrations(project_name, body)
    return {"status": "ok", "project": project_name}


@app.post("/api/projects/{project_name}/deploy/{environment}")
async def trigger_deploy(project_name: str, environment: str):
    """Trigger a deploy via the chat agent (sends a deploy command)."""
    return {
        "status": "pending",
        "message": f"Send 'deploy {project_name} to {environment}' in the chat to trigger deploy.",
        "project": project_name,
        "environment": environment,
    }


# --- Deploy Manager endpoints ---

@app.get("/api/projects/{project_name}/deploy-check")
async def deploy_check(project_name: str):
    """Check which deploy artifacts are present/missing for each target."""
    from deploy_manager import check_project_artifacts, detect_project_stack
    result = check_project_artifacts(project_name)
    result["detected_stack"] = detect_project_stack(project_name)
    return result


@app.post("/api/projects/{project_name}/generate-artifact/{artifact:path}")
async def generate_artifact_endpoint(project_name: str, artifact: str):
    """Generate a specific deploy artifact."""
    from deploy_manager import generate_artifact
    return generate_artifact(project_name, artifact)


@app.post("/api/projects/{project_name}/execute-deploy/{target}")
async def execute_deploy_endpoint(project_name: str, target: str):
    """Execute the deploy to a specific target."""
    from deploy_manager import execute_deploy
    return execute_deploy(project_name, target)


# --- Reference data ---

@app.get("/api/models")
async def get_models():
    return {"models": AVAILABLE_MODELS}

@app.get("/api/harness/metrics")
async def get_harness_metrics():
    """Get harness sensor metrics."""
    total = _harness_metrics["total_sensor_runs"]
    passes = _harness_metrics["sensor_passes"]
    fails = _harness_metrics["sensor_fails"]
    return {
        "total_sensor_runs": total,
        "sensor_passes": passes,
        "sensor_fails": fails,
        "pass_rate": round(passes / total * 100, 1) if total > 0 else 0,
        "correction_opportunities": fails,
        "tools_usage": _harness_metrics["tools_by_name"],
        "sensor_usage": _harness_metrics["sensor_by_name"],
    }

@app.get("/api/tools")
async def get_tools():
    return {"tools": AVAILABLE_TOOL_TEMPLATES}

@app.get("/api/middleware")
async def get_middleware():
    return {"middleware": MIDDLEWARE_OPTIONS}

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "deepagent-harness"}


# --- Serve frontend (production) ---

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="static")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = os.path.join(FRONTEND_DIR, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
