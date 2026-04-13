"""
Playwright E2E Testing Integration — Run end-to-end tests via Playwright.
"""

import os
import subprocess
import json
import glob as globmod

from langchain.tools import tool
from integrations.base import IntegrationBase, IntegrationStatus
from tools import OUTPUT_DIR


class PlaywrightE2EIntegration(IntegrationBase):
    """Playwright-based E2E testing integration."""

    name = "playwright"
    category = "testing"
    icon = "flask-conical"
    color = "#2EAD33"

    DEFAULT_CONFIG = {
        "config_path": "playwright.config.ts",
        "enabled": False,
    }

    def __init__(self, config: dict):
        merged = {**self.DEFAULT_CONFIG, **config}
        super().__init__(merged)

    def get_tools(self) -> list:
        config = self.config

        @tool
        def e2e_run_tests(project_name: str, test_path: str = "", headed: bool = False) -> str:
            """Run Playwright E2E tests for a project. Optionally specify a test path glob and headed mode."""
            project_dir = os.path.join(OUTPUT_DIR, project_name)
            if not os.path.isdir(project_dir):
                return f"Error: Project directory not found: {project_dir}"

            cmd = ["npx", "playwright", "test"]
            if test_path:
                cmd.append(test_path)
            conf = config.get("config_path", "playwright.config.ts")
            if conf:
                cmd.extend(["--config", conf])
            if headed:
                cmd.append("--headed")

            try:
                result = subprocess.run(
                    cmd, cwd=project_dir, capture_output=True, text=True, timeout=300
                )
                output = result.stdout + "\n" + result.stderr

                # Parse pass/fail counts from Playwright output
                passed = failed = skipped = 0
                for line in output.splitlines():
                    lower = line.lower()
                    if "passed" in lower or "failed" in lower or "skipped" in lower:
                        import re
                        for match in re.finditer(r"(\d+)\s+(passed|failed|skipped)", lower):
                            count = int(match.group(1))
                            status = match.group(2)
                            if status == "passed":
                                passed += count
                            elif status == "failed":
                                failed += count
                            elif status == "skipped":
                                skipped += count

                summary = f"Results: {passed} passed, {failed} failed, {skipped} skipped"
                return f"{summary}\n\n--- Full Output ---\n{output}"
            except FileNotFoundError:
                return "Error: 'npx' not found. Please install Node.js and npm first."
            except subprocess.TimeoutExpired:
                return "Error: Test run timed out after 300 seconds."
            except Exception as e:
                return f"Error running Playwright tests: {e}"

        @tool
        def e2e_run_single_test(project_name: str, test_file: str) -> str:
            """Run a single Playwright test file for a project."""
            project_dir = os.path.join(OUTPUT_DIR, project_name)
            if not os.path.isdir(project_dir):
                return f"Error: Project directory not found: {project_dir}"

            conf = config.get("config_path", "playwright.config.ts")
            cmd = ["npx", "playwright", "test", test_file, "--config", conf]

            try:
                result = subprocess.run(
                    cmd, cwd=project_dir, capture_output=True, text=True, timeout=300
                )
                return result.stdout + "\n" + result.stderr
            except FileNotFoundError:
                return "Error: 'npx' not found. Please install Node.js and npm first."
            except subprocess.TimeoutExpired:
                return "Error: Test run timed out after 300 seconds."
            except Exception as e:
                return f"Error running test: {e}"

        @tool
        def e2e_show_report(project_name: str) -> str:
            """Show the last Playwright test report summary for a project."""
            project_dir = os.path.join(OUTPUT_DIR, project_name)
            if not os.path.isdir(project_dir):
                return f"Error: Project directory not found: {project_dir}"

            # Playwright stores results in test-results/ or playwright-report/
            report_dir = os.path.join(project_dir, "playwright-report")
            if not os.path.isdir(report_dir):
                return "No Playwright report found. Run tests first with e2e_run_tests."

            # Try to read the JSON report if available
            json_report = os.path.join(project_dir, "test-results", ".last-run.json")
            if os.path.isfile(json_report):
                try:
                    with open(json_report, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    return f"Last run status: {json.dumps(data, indent=2)}"
                except Exception:
                    pass

            # Fallback: list contents of report directory
            files = os.listdir(report_dir)
            return f"Report directory exists with {len(files)} file(s). Open playwright-report/index.html in a browser for the full report."

        @tool
        def e2e_list_tests(project_name: str) -> str:
            """List all Playwright test files in a project."""
            project_dir = os.path.join(OUTPUT_DIR, project_name)
            if not os.path.isdir(project_dir):
                return f"Error: Project directory not found: {project_dir}"

            # Try using playwright --list flag
            conf = config.get("config_path", "playwright.config.ts")
            cmd = ["npx", "playwright", "test", "--list", "--config", conf]
            try:
                result = subprocess.run(
                    cmd, cwd=project_dir, capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and result.stdout.strip():
                    return f"Test files:\n{result.stdout}"
            except Exception:
                pass

            # Fallback: glob for common test file patterns
            patterns = ["**/*.spec.ts", "**/*.spec.js", "**/*.test.ts", "**/*.test.js"]
            test_files = []
            for pattern in patterns:
                test_files.extend(globmod.glob(os.path.join(project_dir, pattern), recursive=True))

            if not test_files:
                return "No test files found. Initialize Playwright first with e2e_init."

            relative = [os.path.relpath(f, project_dir) for f in sorted(test_files)]
            return "Test files:\n" + "\n".join(f"  - {f}" for f in relative)

        @tool
        def e2e_init(project_name: str) -> str:
            """Initialize Playwright in a project. Installs browsers and dependencies."""
            project_dir = os.path.join(OUTPUT_DIR, project_name)
            if not os.path.isdir(project_dir):
                return f"Error: Project directory not found: {project_dir}"

            try:
                result = subprocess.run(
                    ["npx", "playwright", "install"],
                    cwd=project_dir, capture_output=True, text=True, timeout=300
                )
                output = result.stdout + "\n" + result.stderr
                if result.returncode == 0:
                    return f"Playwright initialized successfully.\n{output}"
                else:
                    return f"Playwright initialization failed (exit code {result.returncode}):\n{output}"
            except FileNotFoundError:
                return "Error: 'npx' not found. Please install Node.js and npm first."
            except subprocess.TimeoutExpired:
                return "Error: Installation timed out after 300 seconds."
            except Exception as e:
                return f"Error initializing Playwright: {e}"

        return [e2e_run_tests, e2e_run_single_test, e2e_show_report, e2e_list_tests, e2e_init]

    async def health_check(self) -> bool:
        """Check if Playwright / npx is available."""
        try:
            result = subprocess.run(
                ["npx", "playwright", "--version"],
                capture_output=True, text=True, timeout=15
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
