"""
Semgrep SAST integration — exposes security scanning operations as LangChain tools.

Config:
    {
        "rulesets": "auto",
        "enabled": false
    }
"""

import os
import subprocess
import json
import shutil

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


def _run_cmd(args: list[str], cwd: str | None = None) -> str:
    """Run a subprocess command and return combined output."""
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode != 0:
            return f"Error (exit {result.returncode}): {err}" if err else f"Error (exit {result.returncode})"
        combined = output if output else err
        return combined if combined else "(no output)"
    except FileNotFoundError:
        return "Error: command not found on PATH."
    except Exception as exc:
        return f"Error: {exc}"


def _semgrep_available() -> bool:
    """Check if semgrep is installed locally."""
    return shutil.which("semgrep") is not None


def _format_findings(findings: list[dict]) -> str:
    """Format Semgrep findings into a readable report."""
    if not findings:
        return "No findings."

    lines = [f"Found {len(findings)} issue(s):\n"]
    for i, f in enumerate(findings, 1):
        severity = f.get("extra", {}).get("severity", "UNKNOWN")
        rule_id = f.get("check_id", "unknown")
        path = f.get("path", "?")
        start_line = f.get("start", {}).get("line", "?")
        message = f.get("extra", {}).get("message", "")
        lines.append(
            f"  [{i}] {severity} — {rule_id}\n"
            f"      File: {path}:{start_line}\n"
            f"      {message}\n"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

@tool
def security_scan(project_name: str, ruleset: str = "auto") -> str:
    """Run a Semgrep SAST scan on the project directory.

    Uses the local semgrep CLI if available, otherwise falls back to Docker.
    Returns formatted findings with severity levels.
    """
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."

    results_file = os.path.join(project_dir, ".semgrep-results.json")

    if _semgrep_available():
        result = subprocess.run(
            ["semgrep", "scan", "--config", ruleset, "--json", project_dir],
            capture_output=True,
            text=True,
        )
        raw_output = result.stdout
    else:
        # Fall back to Docker
        abs_dir = os.path.abspath(project_dir)
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{abs_dir}:/src",
                "semgrep/semgrep",
                "semgrep", "scan", "--config", ruleset, "--json", "/src",
            ],
            capture_output=True,
            text=True,
        )
        raw_output = result.stdout

    # Parse JSON output
    try:
        data = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError):
        return f"Scan completed but could not parse output.\nStdout: {raw_output[:500]}\nStderr: {result.stderr[:500]}"

    # Save results for later use
    try:
        with open(results_file, "w") as fh:
            json.dump(data, fh, indent=2)
    except OSError:
        pass

    findings = data.get("results", [])
    errors = data.get("errors", [])

    report = _format_findings(findings)
    if errors:
        report += f"\n\nScan errors: {len(errors)}"
        for err in errors[:5]:
            report += f"\n  - {err.get('message', str(err))}"

    return report


@tool
def security_report(project_name: str) -> str:
    """Read the last Semgrep scan results and produce a summary.

    Summarises total findings by severity (ERROR, WARNING, INFO) and the top rules triggered.
    """
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    results_file = os.path.join(project_dir, ".semgrep-results.json")

    if not os.path.isfile(results_file):
        return f"No scan results found. Run security_scan('{project_name}') first."

    try:
        with open(results_file) as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        return f"Error reading results file: {exc}"

    findings = data.get("results", [])
    if not findings:
        return "Last scan had 0 findings — clean!"

    # Count by severity
    severity_counts: dict[str, int] = {}
    rule_counts: dict[str, int] = {}
    for f in findings:
        sev = f.get("extra", {}).get("severity", "UNKNOWN")
        rule = f.get("check_id", "unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        rule_counts[rule] = rule_counts.get(rule, 0) + 1

    lines = [f"Semgrep scan summary — {len(findings)} finding(s):\n"]
    lines.append("By severity:")
    for sev in ("ERROR", "WARNING", "INFO", "UNKNOWN"):
        count = severity_counts.get(sev, 0)
        if count:
            lines.append(f"  {sev}: {count}")

    # Top rules
    top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    lines.append("\nTop rules triggered:")
    for rule, count in top_rules:
        lines.append(f"  {rule}: {count}")

    return "\n".join(lines)


@tool
def security_fix_suggestions(project_name: str, finding_id: str = "") -> str:
    """Provide fix suggestions from Semgrep findings.

    If finding_id is given (as a 1-based index), shows detail for that specific finding.
    Otherwise lists suggestions for all findings.
    """
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    results_file = os.path.join(project_dir, ".semgrep-results.json")

    if not os.path.isfile(results_file):
        return f"No scan results found. Run security_scan('{project_name}') first."

    try:
        with open(results_file) as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        return f"Error reading results file: {exc}"

    findings = data.get("results", [])
    if not findings:
        return "No findings to show suggestions for."

    if finding_id:
        try:
            idx = int(finding_id) - 1
            if idx < 0 or idx >= len(findings):
                return f"Invalid finding_id '{finding_id}'. Valid range: 1–{len(findings)}."
            f = findings[idx]
            sev = f.get("extra", {}).get("severity", "UNKNOWN")
            rule = f.get("check_id", "unknown")
            path = f.get("path", "?")
            start = f.get("start", {}).get("line", "?")
            end = f.get("end", {}).get("line", "?")
            message = f.get("extra", {}).get("message", "No message available.")
            fix = f.get("extra", {}).get("fix", "")
            metadata = f.get("extra", {}).get("metadata", {})
            refs = metadata.get("references", [])

            lines = [
                f"Finding #{finding_id}: {rule}",
                f"Severity: {sev}",
                f"File: {path} (lines {start}–{end})",
                f"\nMessage:\n  {message}",
            ]
            if fix:
                lines.append(f"\nSuggested fix:\n  {fix}")
            if refs:
                lines.append("\nReferences:")
                for ref in refs[:5]:
                    lines.append(f"  - {ref}")
            return "\n".join(lines)
        except ValueError:
            return f"finding_id must be a number, got '{finding_id}'."

    # Show all suggestions
    lines = [f"Fix suggestions for {len(findings)} finding(s):\n"]
    for i, f in enumerate(findings, 1):
        rule = f.get("check_id", "unknown")
        message = f.get("extra", {}).get("message", "No suggestion available.")
        fix = f.get("extra", {}).get("fix", "")
        lines.append(f"  [{i}] {rule}")
        lines.append(f"      {message}")
        if fix:
            lines.append(f"      Fix: {fix}")
        lines.append("")

    return "\n".join(lines)


@tool
def security_setup(project_name: str, rulesets: str = "auto,p/owasp-top-ten,p/security-audit") -> str:
    """Create Semgrep configuration files in the project directory.

    Creates a .semgrep.yml with the specified rulesets and a .semgrepignore to
    exclude common non-source directories.
    """
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Error: project directory '{project_name}' does not exist."

    ruleset_list = [r.strip() for r in rulesets.split(",") if r.strip()]

    # Create .semgrep.yml
    semgrep_config = "# Semgrep configuration\n# Docs: https://semgrep.dev/docs/\nrules: []\n\n# Rulesets to include:\n"
    for rs in ruleset_list:
        semgrep_config += f"# - {rs}\n"
    semgrep_config += (
        "\n# Run with:\n"
        f"#   semgrep scan --config {' --config '.join(ruleset_list)} .\n"
    )

    config_path = os.path.join(project_dir, ".semgrep.yml")
    try:
        with open(config_path, "w") as fh:
            fh.write(semgrep_config)
    except OSError as exc:
        return f"Error writing .semgrep.yml: {exc}"

    # Create .semgrepignore
    ignore_content = (
        "# Semgrep ignore patterns\n"
        "node_modules/\n"
        "dist/\n"
        "build/\n"
        ".git/\n"
    )

    ignore_path = os.path.join(project_dir, ".semgrepignore")
    try:
        with open(ignore_path, "w") as fh:
            fh.write(ignore_content)
    except OSError as exc:
        return f"Error writing .semgrepignore: {exc}"

    return (
        f"Semgrep configuration created in {project_name}/:\n"
        f"  .semgrep.yml — rulesets: {', '.join(ruleset_list)}\n"
        f"  .semgrepignore — excludes node_modules, dist, build, .git\n\n"
        f"Run a scan with: security_scan('{project_name}')"
    )


# ---------------------------------------------------------------------------
# Integration class
# ---------------------------------------------------------------------------

class SemgrepSastIntegration(IntegrationBase):
    name = "semgrep_sast"
    category = "security"
    icon = "shield"
    color = "#4B11A8"

    def __init__(self, config: dict):
        super().__init__(config)
        self.rulesets = config.get("rulesets", "auto")

        if config.get("enabled"):
            self._status = IntegrationStatus.CONNECTED
        else:
            self._status = IntegrationStatus.DISCONNECTED

    def get_tools(self) -> list:
        """Return all Semgrep SAST tools for the agent."""
        return [
            security_scan,
            security_report,
            security_fix_suggestions,
            security_setup,
        ]

    async def health_check(self) -> bool:
        """Check if semgrep CLI is available or if the Docker image is pullable."""
        try:
            if _semgrep_available():
                self._status = IntegrationStatus.CONNECTED
                return True

            # Try docker image
            result = subprocess.run(
                ["docker", "image", "inspect", "semgrep/semgrep"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                self._status = IntegrationStatus.CONNECTED
                return True

            # Try pulling the image
            result = subprocess.run(
                ["docker", "pull", "semgrep/semgrep"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            healthy = result.returncode == 0
            self._status = IntegrationStatus.CONNECTED if healthy else IntegrationStatus.ERROR
            return healthy
        except Exception:
            self._status = IntegrationStatus.ERROR
            return False
