"""
Kubernetes Production Deployment Integration — Deploy and manage apps on a production K8s cluster.
"""

import os
import subprocess
import json

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


class K8sIntegration(IntegrationBase):
    """Kubernetes production cluster integration for production deployments."""

    name = "k8s"
    category = "deploy"
    icon = "container"
    color = "#326CE5"

    DEFAULT_CONFIG = {
        "kubeconfig": "~/.kube/config",
        "namespace": "production",
        "cluster": "prod-cluster",
        "enabled": False,
    }

    def __init__(self, config: dict):
        merged = {**self.DEFAULT_CONFIG, **config}
        super().__init__(merged)

    def _kubectl_env(self) -> dict:
        """Build environment with KUBECONFIG set."""
        env = os.environ.copy()
        kubeconfig = self.config.get("kubeconfig", "~/.kube/config")
        env["KUBECONFIG"] = os.path.expanduser(kubeconfig)
        return env

    def _run_kubectl(self, args: list[str], timeout: int = 60) -> str:
        """Run a kubectl command and return combined output."""
        cmd = ["kubectl"] + args
        cluster = self.config.get("cluster")
        if cluster:
            cmd.extend(["--context", cluster])

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
        def k8s_deploy(project_name: str, namespace: str = "production", manifest_path: str = "k8s/") -> str:
            """Apply Kubernetes manifests to the PRODUCTION cluster. Use with caution — this deploys to live production."""
            project_dir = os.path.join(OUTPUT_DIR, project_name)
            manifests_dir = os.path.join(project_dir, manifest_path)

            if not os.path.isdir(project_dir):
                return f"Error: Project directory not found: {project_dir}"
            if not os.path.isdir(manifests_dir):
                return f"Error: Manifests directory not found: {manifests_dir}"

            warning = (
                "==============================================================\n"
                "  WARNING: PRODUCTION DEPLOYMENT\n"
                "  Applying manifests to the PRODUCTION cluster.\n"
                f"  Namespace: {namespace}\n"
                f"  Manifests: {manifests_dir}\n"
                "==============================================================\n"
            )

            # Apply manifests
            result = integration._run_kubectl(
                ["apply", "-f", manifests_dir, "-n", namespace, "--recursive"],
                timeout=120
            )
            return f"{warning}\n{result}"

        @tool
        def k8s_status(project_name: str, namespace: str = "production") -> str:
            """Get pod, service, and deployment status from the production Kubernetes cluster."""
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
                f"[K8s Production Status] project={project_name}, namespace={namespace}\n\n"
                f"--- Pods ---\n{pods}\n\n"
                f"--- Services ---\n{services}\n\n"
                f"--- Deployments ---\n{deployments}"
            )

        @tool
        def k8s_logs(project_name: str, namespace: str = "production", pod: str = "", tail: int = 50) -> str:
            """Get pod logs from the production Kubernetes cluster. Specify a pod name or leave empty to get logs for all pods."""
            if pod:
                log = integration._run_kubectl(
                    ["logs", pod, "-n", namespace, f"--tail={tail}"],
                    timeout=30
                )
                return f"[K8s Production Logs] pod={pod}, namespace={namespace}\n\n{log}"

            # No specific pod — get logs for all pods in namespace
            pod_list = integration._run_kubectl(
                ["get", "pods", "-n", namespace, "-o", "jsonpath={.items[*].metadata.name}"]
            )
            if pod_list.startswith("Error"):
                return pod_list

            pods = pod_list.strip().split()
            if not pods or (len(pods) == 1 and not pods[0]):
                return f"No pods found in namespace '{namespace}'."

            logs_output = []
            for p in pods:
                log = integration._run_kubectl(
                    ["logs", p, "-n", namespace, f"--tail={tail}"],
                    timeout=30
                )
                logs_output.append(f"--- {p} ---\n{log}")

            return f"[K8s Production Logs] namespace={namespace}\n\n" + "\n\n".join(logs_output)

        @tool
        def k8s_scale(project_name: str, deployment: str, replicas: int, namespace: str = "production") -> str:
            """Scale a deployment in the production Kubernetes cluster to the specified number of replicas."""
            result = integration._run_kubectl(
                ["scale", f"deployment/{deployment}", f"--replicas={replicas}", "-n", namespace]
            )
            status = integration._run_kubectl(
                ["rollout", "status", f"deployment/{deployment}", "-n", namespace, "--timeout=120s"]
            )
            return (
                f"[K8s Production Scale] deployment={deployment}, replicas={replicas}, namespace={namespace}\n"
                f"{result}\n\n"
                f"Rollout status:\n{status}"
            )

        @tool
        def k8s_rollback(project_name: str, deployment: str, namespace: str = "production") -> str:
            """Rollback a deployment in the production Kubernetes cluster to its previous revision."""
            result = integration._run_kubectl(
                ["rollout", "undo", f"deployment/{deployment}", "-n", namespace]
            )
            status = integration._run_kubectl(
                ["rollout", "status", f"deployment/{deployment}", "-n", namespace, "--timeout=120s"]
            )
            return (
                f"[K8s Production Rollback] deployment={deployment}, namespace={namespace}\n"
                f"{result}\n\n"
                f"Rollout status:\n{status}"
            )

        return [k8s_deploy, k8s_status, k8s_logs, k8s_scale, k8s_rollback]

    async def health_check(self) -> bool:
        """Check if kubectl can reach the production K8s cluster."""
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
