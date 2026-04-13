"""
Integration Tools — Exposed to the agent for managing integrations.

These meta-tools let the agent configure, check, and use integrations.
The actual provider tools (git_commit, docker_build, etc.) are registered
separately by each provider.
"""

import json
import os
from langchain.tools import tool
from tools import OUTPUT_DIR
from integrations.config import load_project_integrations, save_project_integrations


@tool
def integration_status(project_name: str) -> str:
    """Show the status of all integrations configured for a project.

    Args:
        project_name: The project folder name
    """
    config = load_project_integrations(project_name)

    lines = [f"INTEGRATIONS for {project_name}:\n"]

    # Version control
    vc = config.get("version_control", {})
    vc_status = "ENABLED" if vc.get("enabled") else "DISABLED"
    lines.append(f"  Git ({vc.get('provider', 'gitlab')}): {vc_status}")
    if vc.get("url"):
        lines.append(f"    URL: {vc['url']}")

    # Task management
    tm = config.get("task_management", {})
    tm_provider = tm.get("provider", "builtin")
    tm_status = "ENABLED" if tm.get("enabled") else "DISABLED"
    lines.append(f"  Tasks ({tm_provider}): {tm_status}")

    # Testing
    test = config.get("testing", {})
    test_status = "ENABLED" if test.get("enabled") else "DISABLED"
    lines.append(f"  E2E ({test.get('provider', 'playwright')}): {test_status}")

    # Deploy
    deploy = config.get("deploy", {})
    for env in ["local", "staging", "production"]:
        d = deploy.get(env, {})
        d_status = "ENABLED" if d.get("enabled") else "DISABLED"
        lines.append(f"  Deploy {env} ({d.get('provider', 'N/A')}): {d_status}")

    lines.append("\nUse configure_integration to enable/configure integrations.")
    return "\n".join(lines)


@tool
def configure_integration(
    project_name: str,
    category: str,
    provider: str,
    enabled: bool = True,
    url: str = "",
    token: str = "",
    organization: str = "",
    project: str = "",
    namespace: str = "",
    kubeconfig: str = "",
) -> str:
    """Configure an integration for a project.

    Args:
        project_name: The project folder name
        category: One of: version_control, task_management, testing, deploy_local, deploy_staging, deploy_production
        provider: The provider name (gitlab, builtin, azdevops, playwright, docker, k3s, k8s)
        enabled: Whether the integration is enabled
        url: URL for the service (GitLab URL, etc.)
        token: Authentication token (API key, PAT, etc.)
        organization: Organization name (Azure DevOps)
        project: Project/repo name
        namespace: Kubernetes namespace
        kubeconfig: Path to kubeconfig file
    """
    config = load_project_integrations(project_name)

    entry = {"provider": provider, "enabled": enabled}
    if url:
        entry["url"] = url
    if token:
        entry["token"] = token
    if organization:
        entry["organization"] = organization
    if project:
        entry["project"] = project
    if namespace:
        entry["namespace"] = namespace
    if kubeconfig:
        entry["kubeconfig"] = kubeconfig

    if category.startswith("deploy_"):
        env = category.replace("deploy_", "")
        if "deploy" not in config:
            config["deploy"] = {}
        config["deploy"][env] = entry
    else:
        config[category] = entry

    save_project_integrations(project_name, config)
    return f"Integration '{category}' configured with provider '{provider}' for {project_name}. Status: {'ENABLED' if enabled else 'DISABLED'}."


@tool
def deploy(project_name: str, environment: str = "local") -> str:
    """Deploy a project to the specified environment.

    This is the main deploy entry point. It checks which provider is configured
    for the target environment and calls the appropriate deploy tool.

    Args:
        project_name: The project folder name
        environment: Target environment - "local" (Docker), "staging" (K3s), or "production" (K8s)
    """
    config = load_project_integrations(project_name)
    deploy_config = config.get("deploy", {}).get(environment, {})

    if not deploy_config.get("enabled"):
        return (
            f"Deploy to '{environment}' is not configured for {project_name}.\n"
            f"Use configure_integration to set it up:\n"
            f"  configure_integration(project_name='{project_name}', "
            f"category='deploy_{environment}', provider='docker|k3s|k8s', enabled=True)"
        )

    provider = deploy_config.get("provider", "")

    if provider == "docker" and environment == "local":
        return (
            f"DEPLOY LOCAL: Use docker_compose_up('{project_name}') or "
            f"docker_build('{project_name}') + docker_run('{project_name}').\n"
            f"The user can see the deploy progress in Mission Control."
        )
    elif provider == "k3s" and environment == "staging":
        ns = deploy_config.get("namespace", "staging")
        return (
            f"DEPLOY STAGING: Use k3s_deploy('{project_name}', namespace='{ns}').\n"
            f"Check status with k3s_status('{project_name}')."
        )
    elif provider == "k8s" and environment == "production":
        ns = deploy_config.get("namespace", "production")
        return (
            f"⚠️ PRODUCTION DEPLOY: Use k8s_deploy('{project_name}', namespace='{ns}').\n"
            f"WARNING: This affects production. Verify staging first.\n"
            f"Check status with k8s_status('{project_name}')."
        )
    else:
        return f"Unknown deploy provider '{provider}' for environment '{environment}'."
