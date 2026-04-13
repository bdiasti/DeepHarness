"""
Grafana + Prometheus monitoring integration — local via Docker Compose.

Config:
    {
        "grafana_port": 3001,
        "prometheus_port": 9090,
        "enabled": false
    }
"""

import os
import subprocess
import json

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


def _run_cmd(args: list[str], cwd: str | None = None) -> str:
    """Run a subprocess command and return combined output."""
    try:
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
        output = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode != 0:
            return f"Error (exit {result.returncode}): {err}" if err else f"Error (exit {result.returncode})"
        combined = output if output else err
        return combined if combined else "(no output)"
    except FileNotFoundError:
        return "Error: docker is not installed or not found on PATH."
    except Exception as exc:
        return f"Error: {exc}"


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

@tool
def monitoring_setup(project_name: str, app_port: int = 8080) -> str:
    """Generate a docker-compose.monitoring.yml with Grafana and Prometheus, a prometheus.yml config, and a basic Grafana dashboard for the application."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."

    # --- docker-compose.monitoring.yml ---
    compose_content = f"""version: "3.8"

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: {project_name}-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: {project_name}-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_AUTH_ANONYMOUS_ENABLED=true
    volumes:
      - ./dashboards:/var/lib/grafana/dashboards
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  grafana-data:
"""

    # --- prometheus.yml ---
    prometheus_config = f"""global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "{project_name}-app"
    static_configs:
      - targets: ["host.docker.internal:{app_port}"]
    metrics_path: /metrics
    scrape_interval: 10s
"""

    # --- Grafana dashboard JSON ---
    dashboard = {
        "dashboard": {
            "title": f"{project_name} Overview",
            "panels": [
                {
                    "title": "Request Rate",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0},
                    "targets": [
                        {
                            "expr": f'rate(http_requests_total{{job="{project_name}-app"}}[5m])',
                            "legendFormat": "{{method}} {{status}}",
                        }
                    ],
                },
                {
                    "title": "Error Rate",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0},
                    "targets": [
                        {
                            "expr": f'rate(http_requests_total{{job="{project_name}-app",status=~"5.."}}[5m])',
                            "legendFormat": "{{method}} {{status}}",
                        }
                    ],
                },
                {
                    "title": "Response Time (p95)",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0},
                    "targets": [
                        {
                            "expr": f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{job="{project_name}-app"}}[5m]))',
                            "legendFormat": "p95",
                        }
                    ],
                },
            ],
            "schemaVersion": 30,
            "version": 1,
        }
    }

    # Write files
    compose_path = os.path.join(project_dir, "docker-compose.monitoring.yml")
    prom_path = os.path.join(project_dir, "prometheus.yml")
    dashboards_dir = os.path.join(project_dir, "dashboards")
    os.makedirs(dashboards_dir, exist_ok=True)
    dashboard_path = os.path.join(dashboards_dir, "overview.json")

    with open(compose_path, "w") as f:
        f.write(compose_content)
    with open(prom_path, "w") as f:
        f.write(prometheus_config)
    with open(dashboard_path, "w") as f:
        json.dump(dashboard, f, indent=2)

    return (
        f"Monitoring stack generated for '{project_name}':\n"
        f"  - {compose_path}\n"
        f"  - {prom_path}\n"
        f"  - {dashboard_path}\n\n"
        f"Start with: docker compose -f docker-compose.monitoring.yml up -d\n"
        f"  Grafana:    http://localhost:3001  (admin/admin)\n"
        f"  Prometheus: http://localhost:9090\n"
        f"  App metrics expected at: http://localhost:{app_port}/metrics"
    )


@tool
def monitoring_status(project_name: str) -> str:
    """Check if Grafana and Prometheus containers are running for the project."""
    grafana = _run_cmd([
        "docker", "ps", "--filter", f"name={project_name}-grafana",
        "--format", "{{.ID}}  {{.Status}}  {{.Ports}}",
    ])
    prometheus = _run_cmd([
        "docker", "ps", "--filter", f"name={project_name}-prometheus",
        "--format", "{{.ID}}  {{.Status}}  {{.Ports}}",
    ])

    lines = [f"[Monitoring Status] project={project_name}"]
    lines.append(f"  Grafana:    {grafana if grafana and grafana != '(no output)' else 'not running'}")
    lines.append(f"  Prometheus: {prometheus if prometheus and prometheus != '(no output)' else 'not running'}")
    return "\n".join(lines)


@tool
def monitoring_start(project_name: str) -> str:
    """Start the Grafana + Prometheus monitoring stack via docker compose."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."
    compose_file = os.path.join(project_dir, "docker-compose.monitoring.yml")
    if not os.path.isfile(compose_file):
        return f"Error: docker-compose.monitoring.yml not found. Run monitoring_setup first."
    return _run_cmd(
        ["docker", "compose", "-f", "docker-compose.monitoring.yml", "up", "-d"],
        cwd=project_dir,
    )


@tool
def monitoring_stop(project_name: str) -> str:
    """Stop the Grafana + Prometheus monitoring stack."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."
    return _run_cmd(
        ["docker", "compose", "-f", "docker-compose.monitoring.yml", "down"],
        cwd=project_dir,
    )


@tool
def monitoring_check_alerts(project_name: str) -> str:
    """Query Prometheus API for active alerts and return a formatted list."""
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request("http://localhost:9090/api/v1/alerts")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        return f"Error: could not reach Prometheus — {e}"
    except Exception as e:
        return f"Error querying Prometheus alerts: {e}"

    alerts = data.get("data", {}).get("alerts", [])
    if not alerts:
        return f"[Monitoring Alerts] project={project_name}\nNo active alerts."

    lines = [f"[Monitoring Alerts] project={project_name} ({len(alerts)} active)"]
    for alert in alerts:
        labels = alert.get("labels", {})
        state = alert.get("state", "unknown")
        name = labels.get("alertname", "unnamed")
        severity = labels.get("severity", "-")
        lines.append(f"  - [{state.upper()}] {name} (severity={severity})")
    return "\n".join(lines)


@tool
def monitoring_add_dashboard(project_name: str, dashboard_json: str) -> str:
    """Save a Grafana dashboard JSON to the project dashboards directory."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."

    try:
        dashboard = json.loads(dashboard_json)
    except json.JSONDecodeError as e:
        return f"Error: invalid JSON — {e}"

    dashboards_dir = os.path.join(project_dir, "dashboards")
    os.makedirs(dashboards_dir, exist_ok=True)

    # Derive filename from dashboard title
    title = dashboard.get("dashboard", dashboard).get("title", "custom")
    filename = title.lower().replace(" ", "_") + ".json"
    filepath = os.path.join(dashboards_dir, filename)

    with open(filepath, "w") as f:
        json.dump(dashboard, f, indent=2)

    return f"Dashboard saved to {filepath}"


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class MonitoringIntegration(IntegrationBase):
    name = "monitoring"
    category = "monitoring"
    icon = "activity"
    color = "#F46800"

    DEFAULT_CONFIG = {
        "grafana_port": 3001,
        "prometheus_port": 9090,
        "enabled": False,
    }

    def __init__(self, config: dict):
        merged = {**self.DEFAULT_CONFIG, **config}
        super().__init__(merged)

        if merged.get("enabled"):
            self._status = IntegrationStatus.CONNECTED
        else:
            self._status = IntegrationStatus.DISCONNECTED

    def get_tools(self) -> list:
        return [
            monitoring_setup,
            monitoring_status,
            monitoring_start,
            monitoring_stop,
            monitoring_check_alerts,
            monitoring_add_dashboard,
        ]

    async def health_check(self) -> bool:
        """Check if Grafana responds at the configured port."""
        import urllib.request
        import urllib.error

        port = self.config.get("grafana_port", 3001)
        try:
            req = urllib.request.Request(f"http://localhost:{port}/api/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                healthy = resp.status == 200
        except Exception:
            healthy = False

        self._status = IntegrationStatus.CONNECTED if healthy else IntegrationStatus.ERROR
        return healthy
