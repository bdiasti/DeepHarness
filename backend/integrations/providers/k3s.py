"""
K3s Staging Deployment Integration — Deploy and manage apps on a K3s cluster.
"""

import os
import subprocess
import json

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


class K3sIntegration(IntegrationBase):
    """K3s lightweight Kubernetes cluster integration for staging deployments."""

    name = "k3s"
    category = "deploy"
    icon = "ship"
    color = "#FFC61C"

    DEFAULT_CONFIG = {
        "kubeconfig": "~/.kube/k3s.yaml",
        "namespace": "staging",
        "enabled": False,
    }

    def __init__(self, config: dict):
        merged = {**self.DEFAULT_CONFIG, **config}
        super().__init__(merged)

    def _kubectl_env(self) -> dict:
        """Build environment with KUBECONFIG set."""
        env = os.environ.copy()
        kubeconfig = self.config.get("kubeconfig", "~/.kube/k3s.yaml")
        env["KUBECONFIG"] = os.path.expanduser(kubeconfig)
        return env

    def _run_kubectl(self, args: list[str], timeout: int = 60) -> str:
        """Run a kubectl command and return combined output."""
        cmd = ["kubectl"] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                env=self._kubectl_env()
            )
            output = result.stdout + "\n" + result.stderr
            if result.returncode != 0:
                return f"kubectl exited with code {result.returncode}:\n{output}"
            return output.strip()
        except FileNotFoundError:
            return "Error: 'kubectl' not found. Please install kubectl first."
        except subprocess.TimeoutExpired:
            return f"Error: kubectl command timed out after {timeout} seconds."
        except Exception as e:
            return f"Error running kubectl: {e}"

    def get_tools(self) -> list:
        integration = self

        @tool
        def k3s_deploy(project_name: str, namespace: str = "staging", manifest_path: str = "k8s/") -> str:
            """Apply Kubernetes manifests to the K3s staging cluster for a project."""
            project_dir = os.path.join(OUTPUT_DIR, project_name)
            manifests_dir = os.path.join(project_dir, manifest_path)

            if not os.path.isdir(project_dir):
                return f"Error: Project directory not found: {project_dir}"
            if not os.path.isdir(manifests_dir):
                return f"Error: Manifests directory not found: {manifests_dir}"

            # Ensure namespace exists
            integration._run_kubectl(["create", "namespace", namespace, "--dry-run=client", "-o", "yaml"])
            ns_result = integration._run_kubectl(
                ["apply", "-f", "-"],
            )

            # Apply manifests
            result = integration._run_kubectl(
                ["apply", "-f", manifests_dir, "-n", namespace, "--recursive"],
                timeout=120
            )
            return f"[K3s Staging Deploy] namespace={namespace}\n{result}"

        @tool
        def k3s_status(project_name: str, namespace: str = "staging") -> str:
            """Get pod and service status from the K3s staging cluster for a project."""
            pods = integration._run_kubectl(
                ["get", "pods", "-n", namespace, "-o", "wide"]
            )
            services = integration._run_kubectl(
                ["get", "services", "-n", namespace]
            )
            deployments = integration._run_kubectl(
                ["get", "deployments", "-n", namespace]
            )
            return (
                f"[K3s Staging Status] project={project_name}, namespace={namespace}\n\n"
                f"--- Pods ---\n{pods}\n\n"
                f"--- Services ---\n{services}\n\n"
                f"--- Deployments ---\n{deployments}"
            )

        @tool
        def k3s_logs(project_name: str, namespace: str = "staging", tail: int = 50) -> str:
            """Get pod logs from the K3s staging cluster. Shows logs for all pods matching the project name."""
            # Find pods matching the project name
            pod_list = integration._run_kubectl(
                ["get", "pods", "-n", namespace, "-o", "jsonpath={.items[*].metadata.name}"]
            )
            if pod_list.startswith("Error"):
                return pod_list

            pods = pod_list.strip().split()
            if not pods or (len(pods) == 1 and not pods[0]):
                return f"No pods found in namespace '{namespace}'."

            logs_output = []
            for pod in pods:
                log = integration._run_kubectl(
                    ["logs", pod, "-n", namespace, f"--tail={tail}"],
                    timeout=30
                )
                logs_output.append(f"--- {pod} ---\n{log}")

            return f"[K3s Staging Logs] namespace={namespace}\n\n" + "\n\n".join(logs_output)

        @tool
        def k3s_rollback(project_name: str, deployment: str, namespace: str = "staging") -> str:
            """Rollback a deployment on the K3s staging cluster to its previous revision."""
            result = integration._run_kubectl(
                ["rollout", "undo", f"deployment/{deployment}", "-n", namespace]
            )
            status = integration._run_kubectl(
                ["rollout", "status", f"deployment/{deployment}", "-n", namespace, "--timeout=120s"]
            )
            return (
                f"[K3s Staging Rollback] deployment={deployment}, namespace={namespace}\n"
                f"{result}\n\n"
                f"Rollout status:\n{status}"
            )

        return [k3s_deploy, k3s_status, k3s_logs, k3s_rollback]

    async def health_check(self) -> bool:
        """Check if kubectl can reach the K3s cluster."""
        try:
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True, text=True, timeout=10,
                env=self._kubectl_env()
            )
            if result.returncode == 0:
                self._status = IntegrationStatus.CONNECTED
                return True
            self._status = IntegrationStatus.ERROR
            return False
        except FileNotFoundError:
            self._status = IntegrationStatus.DISCONNECTED
            return False
        except Exception:
            self._status = IntegrationStatus.ERROR
            return False
