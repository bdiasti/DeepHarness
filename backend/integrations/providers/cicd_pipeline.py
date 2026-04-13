"""
GitLab CI/CD pipeline generation — generates and manages .gitlab-ci.yml files.

Config:
    {
        "enabled": true
    }
"""

import os
import subprocess
import json

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


def _project_dir(project_name: str) -> str:
    return os.path.join(OUTPUT_DIR, project_name)


def _pipeline_path(project_name: str) -> str:
    return os.path.join(_project_dir(project_name), ".gitlab-ci.yml")


def _load_yaml_simple(path: str) -> dict | None:
    """Load a YAML file using a simple parser (avoids external deps).

    Tries PyYAML first, falls back to json-compatible subset parsing.
    """
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        pass

    # Minimal fallback: read raw content and return as string-keyed dict
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"_raw": content}
    except Exception:
        return None


def _dump_yaml(data: dict) -> str:
    """Dump dict to YAML string."""
    try:
        import yaml
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    except ImportError:
        # Manual YAML-like serialisation for simple structures
        lines = []
        for key, value in data.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    if isinstance(item, str):
                        lines.append(f"  - {item}")
                    else:
                        lines.append(f"  - {item}")
            elif isinstance(value, dict):
                lines.append(f"{key}:")
                for k2, v2 in value.items():
                    if isinstance(v2, list):
                        lines.append(f"  {k2}:")
                        for item in v2:
                            lines.append(f"    - {item}")
                    elif isinstance(v2, dict):
                        lines.append(f"  {k2}:")
                        for k3, v3 in v2.items():
                            if isinstance(v3, list):
                                lines.append(f"    {k3}:")
                                for item in v3:
                                    lines.append(f"      - {item}")
                            else:
                                lines.append(f"    {k3}: {v3}")
                    else:
                        lines.append(f"  {k2}: {v2}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

@tool
def cicd_generate_pipeline(
    project_name: str,
    stages: str = "build,test,quality,deploy_staging,deploy_prod",
    docker_image: str = "",
    sonar_enabled: bool = True,
) -> str:
    """Generate a .gitlab-ci.yml pipeline file with proper stages.

    Stages: build (docker build), test (run tests), quality (sonar-scanner),
    deploy_staging (kubectl to k3s), deploy_prod (kubectl to k8s, manual trigger).
    """
    project_dir = _project_dir(project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."

    stage_list = [s.strip() for s in stages.split(",") if s.strip()]
    base_image = docker_image or "docker:24.0"
    project_slug = project_name.replace(" ", "-").lower()

    pipeline = {
        "stages": stage_list,
        "variables": {
            "DOCKER_IMAGE": f"$CI_REGISTRY_IMAGE/{project_slug}",
            "DOCKER_TAG": "$CI_COMMIT_SHORT_SHA",
            "KUBECONFIG": "/etc/deploy/config",
        },
    }

    if "build" in stage_list:
        pipeline["build"] = {
            "stage": "build",
            "image": base_image,
            "services": ["docker:24.0-dind"],
            "variables": {
                "DOCKER_TLS_CERTDIR": "/certs",
            },
            "script": [
                "docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY",
                f"docker build -t $DOCKER_IMAGE:$DOCKER_TAG .",
                f"docker push $DOCKER_IMAGE:$DOCKER_TAG",
                f"docker tag $DOCKER_IMAGE:$DOCKER_TAG $DOCKER_IMAGE:latest",
                f"docker push $DOCKER_IMAGE:latest",
            ],
            "tags": ["docker"],
        }

    if "test" in stage_list:
        pipeline["test"] = {
            "stage": "test",
            "image": "python:3.12-slim",
            "script": [
                "pip install -r requirements.txt 2>/dev/null || true",
                "pip install pytest pytest-cov",
                "pytest --tb=short --junitxml=report.xml --cov=. --cov-report=term-missing || true",
            ],
            "artifacts": {
                "reports": {
                    "junit": "report.xml",
                },
                "when": "always",
            },
        }

    if "quality" in stage_list:
        quality_job = {
            "stage": "quality",
            "image": "sonarsource/sonar-scanner-cli:latest",
            "script": [],
            "allow_failure": True,
        }
        if sonar_enabled:
            quality_job["script"] = [
                "sonar-scanner "
                "-Dsonar.projectKey=$CI_PROJECT_PATH_SLUG "
                "-Dsonar.sources=. "
                "-Dsonar.host.url=$SONAR_HOST_URL "
                "-Dsonar.login=$SONAR_TOKEN",
            ]
            quality_job["variables"] = {
                "SONAR_HOST_URL": "${SONAR_HOST_URL}",
                "SONAR_TOKEN": "${SONAR_TOKEN}",
            }
        else:
            quality_job["script"] = ["echo 'Quality gate skipped — SonarQube not enabled.'"]
        pipeline["quality"] = quality_job

    if "deploy_staging" in stage_list:
        pipeline["deploy_staging"] = {
            "stage": "deploy_staging",
            "image": "bitnami/kubectl:latest",
            "environment": {
                "name": "staging",
                "url": f"https://staging.{project_slug}.local",
            },
            "script": [
                "kubectl config use-context k3s-staging",
                f"kubectl set image deployment/{project_slug} app=$DOCKER_IMAGE:$DOCKER_TAG -n staging",
                "kubectl rollout status deployment/" + project_slug + " -n staging --timeout=120s",
            ],
            "only": ["develop", "main"],
        }

    if "deploy_prod" in stage_list:
        pipeline["deploy_prod"] = {
            "stage": "deploy_prod",
            "image": "bitnami/kubectl:latest",
            "environment": {
                "name": "production",
                "url": f"https://{project_slug}.local",
            },
            "script": [
                "kubectl config use-context k8s-production",
                f"kubectl set image deployment/{project_slug} app=$DOCKER_IMAGE:$DOCKER_TAG -n production",
                "kubectl rollout status deployment/" + project_slug + " -n production --timeout=180s",
            ],
            "when": "manual",
            "only": ["main"],
        }

    yaml_content = _dump_yaml(pipeline)
    pipeline_path = _pipeline_path(project_name)
    with open(pipeline_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    return (
        f"Generated .gitlab-ci.yml for '{project_name}' with stages: {', '.join(stage_list)}.\n"
        f"File saved to: {pipeline_path}"
    )


@tool
def cicd_validate_pipeline(project_name: str) -> str:
    """Read the .gitlab-ci.yml and validate its structure (stages, jobs)."""
    pipeline_path = _pipeline_path(project_name)
    if not os.path.isfile(pipeline_path):
        return f"Error: no .gitlab-ci.yml found in project '{project_name}'."

    data = _load_yaml_simple(pipeline_path)
    if data is None:
        return "Error: could not parse .gitlab-ci.yml."

    # If we only have raw content (no PyYAML), do basic text checks
    if "_raw" in data:
        raw = data["_raw"]
        issues = []
        if "stages:" not in raw:
            issues.append("Missing 'stages' key.")
        if "script:" not in raw:
            issues.append("No jobs with 'script' found — pipeline has no runnable jobs.")
        if not issues:
            return "Basic validation passed (install PyYAML for deeper checks)."
        return "Validation issues:\n" + "\n".join(f"  - {i}" for i in issues)

    issues = []

    # Check for stages key
    if "stages" not in data:
        issues.append("Missing top-level 'stages' key.")
    elif not isinstance(data["stages"], list) or len(data["stages"]) == 0:
        issues.append("'stages' must be a non-empty list.")

    declared_stages = set(data.get("stages", []))

    # Check jobs
    reserved_keys = {"stages", "variables", "image", "services", "before_script", "after_script",
                     "cache", "include", "default", "workflow"}
    jobs = {k: v for k, v in data.items() if k not in reserved_keys and isinstance(v, dict)}

    if not jobs:
        issues.append("No jobs defined in pipeline.")

    for job_name, job_config in jobs.items():
        if "stage" not in job_config:
            issues.append(f"Job '{job_name}' is missing 'stage' key.")
        elif job_config["stage"] not in declared_stages:
            issues.append(f"Job '{job_name}' references undeclared stage '{job_config['stage']}'.")
        if "script" not in job_config:
            issues.append(f"Job '{job_name}' is missing 'script' key.")

    if not issues:
        return f"Pipeline is valid. Found {len(jobs)} job(s) across {len(declared_stages)} stage(s)."
    return "Validation issues:\n" + "\n".join(f"  - {i}" for i in issues)


@tool
def cicd_add_stage(
    project_name: str,
    stage_name: str,
    script: str,
    image: str = "",
    only: str = "",
) -> str:
    """Add a new stage/job to the existing .gitlab-ci.yml pipeline.

    script: semicolon-separated commands (e.g. 'echo hello;make lint').
    """
    pipeline_path = _pipeline_path(project_name)
    if not os.path.isfile(pipeline_path):
        return f"Error: no .gitlab-ci.yml found in project '{project_name}'. Generate one first."

    try:
        import yaml
    except ImportError:
        return "Error: PyYAML is required to modify pipeline files. Install with: pip install pyyaml"

    with open(pipeline_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        return "Error: .gitlab-ci.yml has unexpected format."

    # Ensure stages list includes the new stage
    if "stages" not in data:
        data["stages"] = []
    if stage_name not in data["stages"]:
        data["stages"].append(stage_name)

    # Build the job definition
    script_lines = [s.strip() for s in script.split(";") if s.strip()]
    job = {
        "stage": stage_name,
        "script": script_lines,
    }
    if image:
        job["image"] = image
    if only:
        job["only"] = [b.strip() for b in only.split(",") if b.strip()]

    data[stage_name] = job

    yaml_content = yaml.dump(data, default_flow_style=False, sort_keys=False)
    with open(pipeline_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    return f"Added stage '{stage_name}' to pipeline with {len(script_lines)} command(s)."


@tool
def cicd_show_pipeline(project_name: str) -> str:
    """Read and display the current .gitlab-ci.yml pipeline configuration."""
    pipeline_path = _pipeline_path(project_name)
    if not os.path.isfile(pipeline_path):
        return f"Error: no .gitlab-ci.yml found in project '{project_name}'."

    try:
        with open(pipeline_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f".gitlab-ci.yml for '{project_name}':\n\n{content}"
    except Exception as exc:
        return f"Error reading pipeline: {exc}"


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class CICDPipelineIntegration(IntegrationBase):
    name = "cicd_pipeline"
    category = "cicd"
    icon = "git-merge"
    color = "#FC6D26"

    def __init__(self, config: dict):
        super().__init__(config)
        if config.get("enabled"):
            self._status = IntegrationStatus.CONNECTED
        else:
            self._status = IntegrationStatus.DISCONNECTED

    def get_tools(self) -> list:
        """Return all CI/CD pipeline tools for the agent."""
        return [
            cicd_generate_pipeline,
            cicd_validate_pipeline,
            cicd_add_stage,
            cicd_show_pipeline,
        ]

    async def health_check(self) -> bool:
        """Always healthy — this integration only generates files."""
        self._status = IntegrationStatus.CONNECTED
        return True
