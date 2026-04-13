"""
DeepHarness — Engineering Platform

Creates Deep Agents configured by engineering role templates.
Includes feedback sensors, planning tools (SDD), and integrations
(Git, Tasks, Docker, K8s, Playwright).
Templates can be switched at runtime via the API.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI

from tools import (
    generate_agent_code,
    validate_agent_config,
    list_available_models,
    list_available_tools,
    list_middleware_options,
    list_projects,
    OUTPUT_DIR,
)
from sensors import (
    run_linter,
    validate_structure,
    check_directives,
    review_code,
    harness_status,
    read_harness_rules,
    update_harness_rules,
    read_agents_md,
    update_agents_md,
    scan_drift,
    validate_before_write,
    create_sdd,
    get_sdd,
)
from integrations.tools import (
    integration_status,
    configure_integration,
    deploy,
)
from template_loader import (
    Template, create_agent_for_template, list_templates,
    Persona, Stack, create_agent_for_combo, list_personas, list_stacks,
    list_skills_library, ProjectType, list_project_types,
)

# --- Model: Azure AI Foundry (OpenAI-compatible) ---

_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
if not _endpoint:
    raise RuntimeError("AZURE_OPENAI_ENDPOINT environment variable is required")

model = ChatOpenAI(
    base_url=_endpoint,
    api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""),
    model=os.environ.get("AZURE_OPENAI_MODEL", "gpt-5.3-chat"),
)

# --- Core tools (available to ALL templates) ---

CORE_TOOLS = [
    # Planning
    create_sdd,
    get_sdd,
    # Sensors
    run_linter,
    validate_structure,
    check_directives,
    review_code,
    harness_status,
    validate_before_write,
    scan_drift,
    # Steering loop
    read_harness_rules,
    update_harness_rules,
    # Project memory
    read_agents_md,
    update_agents_md,
    # Integrations
    integration_status,
    configure_integration,
    deploy,
    # Utility
    list_projects,
]

# --- Load integration provider tools ---

PROVIDER_CLASSES = [
    # Version Control
    ("integrations.providers.gitlab", "GitLabIntegration"),
    # Task Management
    ("integrations.providers.task_manager", "TaskManagerIntegration"),
    ("integrations.providers.azdevops", "AzureDevOpsIntegration"),
    # Deploy
    ("integrations.providers.docker", "DockerIntegration"),
    ("integrations.providers.k3s", "K3sIntegration"),
    ("integrations.providers.k8s", "K8sIntegration"),
    # Testing
    ("integrations.providers.playwright_e2e", "PlaywrightIntegration"),
    # Quality
    ("integrations.providers.sonarqube", "SonarQubeIntegration"),
    # CI/CD
    ("integrations.providers.cicd_pipeline", "CICDPipelineIntegration"),
    # Notifications
    ("integrations.providers.notifications", "NotificationsIntegration"),
    # Monitoring
    ("integrations.providers.monitoring", "MonitoringIntegration"),
    # Secrets
    ("integrations.providers.vault", "VaultIntegration"),
    # Database
    ("integrations.providers.flyway", "FlywayIntegration"),
    # Registry
    ("integrations.providers.registry", "RegistryIntegration"),
    # Security
    ("integrations.providers.semgrep_sast", "SemgrepIntegration"),
    # Feature Flags
    ("integrations.providers.flagsmith_flags", "FlagsmithIntegration"),
]


def _load_integration_tools() -> list:
    """Load tools from all integration providers."""
    import importlib
    tools = []
    for module_path, class_name in PROVIDER_CLASSES:
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            instance = cls({})
            provider_tools = instance.get_tools()
            tools.extend(provider_tools)
            print(f"  [OK] {class_name}: {len(provider_tools)} tools")
        except Exception as e:
            print(f"  [SKIP] {class_name}: {e}")
    return tools


INTEGRATION_TOOLS = _load_integration_tools()
print(f"[INTEGRATIONS] Loaded {len(INTEGRATION_TOOLS)} integration tools")

# --- Tools only for the deepagent_generator template ---

GENERATOR_TOOLS = [
    generate_agent_code,
    validate_agent_config,
    list_available_models,
    list_available_tools,
    list_middleware_options,
]

# --- Agent cache (one agent per template) ---

_agent_cache: dict = {}


def get_agent(
    persona_id: str = "deepagent_generator",
    skill_ids: list = None,
    project_type_id: str = "custom",
):
    """Get or create the Deep Agent for project_type + persona + skills."""
    skill_ids = skill_ids or []
    cache_key = f"{project_type_id}:{persona_id}:{','.join(sorted(skill_ids))}"

    if cache_key in _agent_cache:
        return _agent_cache[cache_key]

    print(f"[AGENT] Creating agent for project={project_type_id} persona={persona_id} skills={skill_ids}")
    persona = Persona(persona_id)
    project_type = None
    try:
        project_type = ProjectType(project_type_id)
    except Exception:
        pass

    extra_tools = list(CORE_TOOLS) + list(INTEGRATION_TOOLS)
    if persona_id == "deepagent_generator":
        extra_tools.extend(GENERATOR_TOOLS)

    agent = create_agent_for_combo(persona, skill_ids, model, extra_tools, project_type)
    _agent_cache[cache_key] = agent
    return agent


def clear_agent_cache(persona_id: str = None, stack_id: str = None):
    """Clear cached agents (forces re-creation on next request)."""
    if persona_id and stack_id:
        _agent_cache.pop(f"{persona_id}:{stack_id}", None)
    else:
        _agent_cache.clear()
