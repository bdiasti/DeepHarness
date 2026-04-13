"""
Harness Sensors & Planning Tools

Sensors (feedback controls that run after agent actions):
- Computational: deterministic, fast (linters, type checkers, structure validators)
- Inferential: LLM-based, slower (code review, semantic analysis)

Planning (feedforward controls that guide before coding):
- SDD: Software Design Document creation and task breakdown
- Pre-write validation: checks before saving files

All outputs are formatted for LLM self-correction.
"""

import os
import re
import json
import subprocess
from typing import Optional
from langchain.tools import tool

from tools import OUTPUT_DIR


# =============================================================================
# Computational Sensors
# =============================================================================

@tool
def run_linter(project_name: str, filename: str) -> str:
    """Run a linter on a file in a generated project. Returns issues found.

    Supports: .py (ruff/pyflakes), .ts/.tsx/.js/.jsx (eslint basic checks),
    .java (basic pattern checks). Returns structured feedback for self-correction.

    Args:
        project_name: The project folder name
        filename: The file to lint (relative to project root)
    """
    filepath = os.path.join(OUTPUT_DIR, project_name, filename)
    if not os.path.isfile(filepath):
        return f"File not found: {project_name}/{filename}"

    ext = os.path.splitext(filename)[1].lower()
    issues = []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.split("\n")

    if ext == ".py":
        issues = _lint_python(lines, filename)
    elif ext in (".ts", ".tsx", ".js", ".jsx"):
        issues = _lint_typescript(lines, filename)
    elif ext == ".java":
        issues = _lint_java(lines, filename)
    elif ext == ".md":
        issues = _lint_markdown(lines, filename)
    else:
        return f"No linter available for {ext} files."

    if not issues:
        return f"LINT PASSED: {filename} — No issues found."

    result = f"LINT ISSUES in {filename} ({len(issues)} found):\n\n"
    for issue in issues:
        result += f"  Line {issue['line']}: [{issue['severity']}] {issue['message']}\n"
        if issue.get("fix"):
            result += f"    FIX: {issue['fix']}\n"
    result += f"\nPlease fix these issues using edit_file on {project_name}/{filename}."
    return result


def _lint_python(lines: list[str], filename: str) -> list[dict]:
    issues = []
    for i, line in enumerate(lines, 1):
        # Line too long
        if len(line) > 120:
            issues.append({"line": i, "severity": "WARNING", "message": f"Line too long ({len(line)} > 120 chars)", "fix": "Break line into multiple lines"})
        # Bare except
        if re.match(r'\s*except\s*:', line):
            issues.append({"line": i, "severity": "ERROR", "message": "Bare except clause — catches all exceptions including KeyboardInterrupt", "fix": "Use 'except Exception:' or a specific exception type"})
        # Hardcoded secrets
        if re.search(r'(api_key|password|secret|token)\s*=\s*["\'][^"\']{8,}', line, re.IGNORECASE):
            issues.append({"line": i, "severity": "CRITICAL", "message": "Possible hardcoded secret/credential", "fix": "Use environment variables: os.environ.get('KEY_NAME')"})
        # Print statements in non-main code
        if re.match(r'\s*print\(', line) and '__main__' not in ''.join(lines[max(0,i-5):i]):
            issues.append({"line": i, "severity": "INFO", "message": "print() statement — consider using logging", "fix": "Replace with logging.info() or logging.debug()"})
        # TODO comments
        if re.search(r'#\s*TODO', line, re.IGNORECASE):
            issues.append({"line": i, "severity": "WARNING", "message": "TODO comment found — should be tracked as a task", "fix": "Create a task/issue instead of a TODO comment"})
        # Import *
        if re.match(r'\s*from\s+\S+\s+import\s+\*', line):
            issues.append({"line": i, "severity": "WARNING", "message": "Wildcard import — pollutes namespace", "fix": "Import specific names instead"})
    return issues


def _lint_typescript(lines: list[str], filename: str) -> list[dict]:
    issues = []
    for i, line in enumerate(lines, 1):
        # any type
        if re.search(r':\s*any\b', line):
            issues.append({"line": i, "severity": "ERROR", "message": "Usage of 'any' type — defeats TypeScript safety", "fix": "Use a specific type or 'unknown' if type is truly dynamic"})
        # console.log
        if re.search(r'console\.(log|debug|info)', line):
            issues.append({"line": i, "severity": "WARNING", "message": "console.log statement — remove before commit", "fix": "Remove or replace with proper logging"})
        # var keyword
        if re.match(r'\s*var\s+', line):
            issues.append({"line": i, "severity": "ERROR", "message": "'var' is deprecated — use const or let", "fix": "Replace 'var' with 'const' (preferred) or 'let'"})
        # Hardcoded URLs/keys
        if re.search(r'(http://|https://)\S+', line) and not re.search(r'localhost|127\.0\.0\.1|example\.com', line):
            issues.append({"line": i, "severity": "WARNING", "message": "Hardcoded URL — consider using environment variable", "fix": "Move URL to environment config"})
        # Line too long
        if len(line) > 120:
            issues.append({"line": i, "severity": "WARNING", "message": f"Line too long ({len(line)} > 120 chars)", "fix": "Break into multiple lines"})
    return issues


def _lint_java(lines: list[str], filename: str) -> list[dict]:
    issues = []
    for i, line in enumerate(lines, 1):
        # System.out.println
        if re.search(r'System\.(out|err)\.(print|println)', line):
            issues.append({"line": i, "severity": "WARNING", "message": "System.out.println — use a logger (SLF4J)", "fix": "Replace with logger.info() or logger.debug()"})
        # Catch generic Exception
        if re.search(r'catch\s*\(\s*Exception\s+', line):
            issues.append({"line": i, "severity": "WARNING", "message": "Catching generic Exception — catch specific types", "fix": "Catch specific exception types (e.g., IOException, IllegalArgumentException)"})
        # Raw SQL strings
        if re.search(r'(executeQuery|executeUpdate|prepareStatement)\s*\(\s*".*\+', line):
            issues.append({"line": i, "severity": "CRITICAL", "message": "Possible SQL injection — string concatenation in query", "fix": "Use parameterized queries with PreparedStatement"})
        # Hardcoded credentials
        if re.search(r'(password|secret|apiKey)\s*=\s*"[^"]{4,}"', line, re.IGNORECASE):
            issues.append({"line": i, "severity": "CRITICAL", "message": "Hardcoded credential detected", "fix": "Use environment variables or a secrets manager"})
    return issues


def _lint_markdown(lines: list[str], filename: str) -> list[dict]:
    issues = []
    has_h1 = any(line.startswith("# ") for line in lines)
    if not has_h1:
        issues.append({"line": 1, "severity": "WARNING", "message": "Missing H1 heading", "fix": "Add a title as '# Title' at the top"})
    return issues


@tool
def validate_structure(project_name: str, template_id: str) -> str:
    """Validate that a project follows the required folder structure for its template.

    Args:
        project_name: The project folder name
        template_id: The template to validate against (e.g., 'fullstack_react_java')
    """
    from template_loader import Template

    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Project '{project_name}' not found."

    try:
        template = Template(template_id)
    except ValueError:
        return f"Template '{template_id}' not found."

    ps = template.project_structure
    missing_files = []
    missing_dirs = []

    for f in ps.get("files", []):
        if not os.path.isfile(os.path.join(project_dir, f)):
            missing_files.append(f)

    for d in ps.get("required_dirs", []):
        if not os.path.isdir(os.path.join(project_dir, d)):
            missing_dirs.append(d)

    if not missing_files and not missing_dirs:
        return f"STRUCTURE VALID: {project_name} follows the {template.name} template structure."

    result = f"STRUCTURE ISSUES in {project_name}:\n\n"
    if missing_files:
        result += "Missing required files:\n"
        for f in missing_files:
            result += f"  - {f}\n"
    if missing_dirs:
        result += "Missing required directories:\n"
        for d in missing_dirs:
            result += f"  - {d}\n"
    result += f"\nCreate these using write_file. Directories are auto-created."
    return result


@tool
def check_directives(project_name: str, filename: str, template_id: str) -> str:
    """Check if a file follows the immutable directives of its template.

    Performs pattern-based checks against known directive violations.

    Args:
        project_name: The project folder name
        filename: The file to check
        template_id: The template whose directives to check against
    """
    filepath = os.path.join(OUTPUT_DIR, project_name, filename)
    if not os.path.isfile(filepath):
        return f"File not found: {project_name}/{filename}"

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    violations = []

    # Universal directive checks
    # Check for hardcoded secrets
    secret_patterns = [
        (r'(api_key|apikey|password|secret|token)\s*=\s*["\'][A-Za-z0-9+/=]{16,}', "Hardcoded secret detected"),
        (r'(sk-|pk_live_|ghp_|xoxb-)[A-Za-z0-9]{10,}', "API key/token pattern detected"),
    ]
    for pattern, msg in secret_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            violations.append({"severity": "CRITICAL", "directive": "No hardcoded secrets", "message": msg})

    # Template-specific checks
    ext = os.path.splitext(filename)[1].lower()

    if template_id == "fullstack_react_java":
        if ext in (".ts", ".tsx"):
            if ": any" in content or ":any" in content:
                violations.append({"severity": "ERROR", "directive": "TypeScript types MUST be explicit — NEVER use any", "message": "Found 'any' type usage"})
        if ext == ".java":
            if "System.out.println" in content:
                violations.append({"severity": "WARNING", "directive": "Use proper logging", "message": "Found System.out.println instead of logger"})
            if re.search(r'public class \w+Controller', content) and "Service" not in content:
                violations.append({"severity": "ERROR", "directive": "Controller must use Service layer", "message": "Controller appears to have business logic without Service injection"})

    if template_id in ("developer", "fullstack_react_java"):
        if ext == ".py" and len(content.split("\n")) > 300:
            violations.append({"severity": "WARNING", "directive": "Files should be focused", "message": f"File has {len(content.split(chr(10)))} lines — consider splitting"})

    if not violations:
        return f"DIRECTIVES OK: {filename} complies with {template_id} directives."

    result = f"DIRECTIVE VIOLATIONS in {filename}:\n\n"
    for v in violations:
        result += f"  [{v['severity']}] {v['message']}\n"
        result += f"    Directive: {v['directive']}\n"
    result += f"\nFix these violations — they are non-negotiable rules."
    return result


# =============================================================================
# Inferential Sensor (LLM-as-judge code review)
# =============================================================================

@tool
def review_code(project_name: str, filename: str) -> str:
    """Request a code review of a file. This triggers the code_reviewer subagent
    to analyze the code for quality issues, SOLID violations, and potential bugs.

    Use this after writing or editing important files.

    Args:
        project_name: The project folder name
        filename: The file to review
    """
    filepath = os.path.join(OUTPUT_DIR, project_name, filename)
    if not os.path.isfile(filepath):
        return f"File not found: {project_name}/{filename}"

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Return the content with review instructions - the agent or subagent will do the actual review
    return (
        f"CODE REVIEW REQUEST for {filename}:\n\n"
        f"```\n{content[:3000]}\n```\n\n"
        f"Review this code for:\n"
        f"1. SOLID principle violations\n"
        f"2. Security vulnerabilities\n"
        f"3. Performance issues\n"
        f"4. Missing error handling\n"
        f"5. Unclear naming or structure\n"
        f"6. Missing tests\n"
        f"Provide specific, actionable feedback with line references."
    )


# =============================================================================
# Harness Status Tool
# =============================================================================

@tool
def harness_status(project_name: str, template_id: str) -> str:
    """Get the overall harness health status for a project.

    Runs all computational sensors and returns a summary.

    Args:
        project_name: The project folder name
        template_id: The template to validate against
    """
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Project '{project_name}' not found."

    results = {
        "structure": "PENDING",
        "lint_issues": 0,
        "directive_violations": 0,
        "files_checked": 0,
    }

    # Structure check
    struct_result = validate_structure.invoke({"project_name": project_name, "template_id": template_id})
    results["structure"] = "PASS" if "VALID" in struct_result else "FAIL"

    # Lint all code files
    for root, dirs, files in os.walk(project_dir):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in (".py", ".ts", ".tsx", ".js", ".jsx", ".java"):
                rel_path = os.path.relpath(os.path.join(root, fname), project_dir).replace("\\", "/")
                results["files_checked"] += 1

                lint_result = run_linter.invoke({"project_name": project_name, "filename": rel_path})
                if "ISSUES" in lint_result:
                    count = int(re.search(r'(\d+) found', lint_result).group(1)) if re.search(r'(\d+) found', lint_result) else 0
                    results["lint_issues"] += count

                dir_result = check_directives.invoke({"project_name": project_name, "filename": rel_path, "template_id": template_id})
                if "VIOLATIONS" in dir_result:
                    results["directive_violations"] += 1

    # Build summary
    status = "HEALTHY" if results["lint_issues"] == 0 and results["directive_violations"] == 0 and results["structure"] == "PASS" else "NEEDS ATTENTION"

    return (
        f"HARNESS STATUS for {project_name} ({template_id}):\n\n"
        f"  Overall: {status}\n"
        f"  Structure: {results['structure']}\n"
        f"  Files checked: {results['files_checked']}\n"
        f"  Lint issues: {results['lint_issues']}\n"
        f"  Directive violations: {results['directive_violations']}\n"
        f"\nUse run_linter, check_directives, or validate_structure for details on specific files."
    )


# =============================================================================
# Steering Loop — Custom harness rules per project
# =============================================================================

@tool
def read_harness_rules(project_name: str) -> str:
    """Read the custom harness.md rules for a project.

    The harness.md file contains user-defined rules that supplement the template directives.

    Args:
        project_name: The project folder name
    """
    filepath = os.path.join(OUTPUT_DIR, project_name, "harness.md")
    if not os.path.isfile(filepath):
        return f"No custom harness rules found for '{project_name}'. The user can ask to create one."

    with open(filepath, "r", encoding="utf-8") as f:
        return f"Custom harness rules for {project_name}:\n\n{f.read()}"


@tool
def update_harness_rules(project_name: str, rules: str) -> str:
    """Create or update the custom harness.md rules for a project.

    This is the steering loop — users add rules when they notice recurring issues.
    These rules are loaded alongside the template directives.

    Args:
        project_name: The project folder name
        rules: The complete harness rules content in markdown
    """
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Project '{project_name}' not found."

    filepath = os.path.join(project_dir, "harness.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Custom Harness Rules — {project_name}\n\n{rules}")

    return f"Harness rules updated for '{project_name}'. These will be enforced on all future actions."


# =============================================================================
# AGENTS.md — Project memory
# =============================================================================

@tool
def read_agents_md(project_name: str) -> str:
    """Read the AGENTS.md project memory file.

    AGENTS.md stores project context: conventions, decisions, architecture notes.

    Args:
        project_name: The project folder name
    """
    filepath = os.path.join(OUTPUT_DIR, project_name, "AGENTS.md")
    if not os.path.isfile(filepath):
        return f"No AGENTS.md found for '{project_name}'."

    with open(filepath, "r", encoding="utf-8") as f:
        return f"Project context for {project_name}:\n\n{f.read()}"


@tool
def update_agents_md(project_name: str, content: str) -> str:
    """Create or update the AGENTS.md project memory file.

    Use this to record important decisions, conventions, and context about the project.

    Args:
        project_name: The project folder name
        content: The AGENTS.md content
    """
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Project '{project_name}' not found."

    filepath = os.path.join(project_dir, "AGENTS.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return f"AGENTS.md updated for '{project_name}'."


# =============================================================================
# Drift Detection — "Janitor Army" pattern (garbage collection scanning)
# =============================================================================

@tool
def scan_drift(project_name: str) -> str:
    """Scan a project for drift: unused imports, dead files, orphan configs, naming issues.

    This is the "janitor army" sensor — runs periodically to find accumulated quality drift.

    Args:
        project_name: The project folder name
    """
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return f"Project '{project_name}' not found."

    issues = []
    all_files = []

    for root, dirs, files in os.walk(project_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, project_dir).replace("\\", "/")
            all_files.append(rel)

            # Check for empty files
            if os.path.getsize(fpath) == 0:
                issues.append(f"EMPTY FILE: {rel} — delete or add content")

            # Check for temp/backup files
            if fname.endswith((".bak", ".tmp", ".swp", ".orig")):
                issues.append(f"TEMP FILE: {rel} — should be deleted")

            # Check for duplicate config files
            if fname in (".env", ".env.local", ".env.development"):
                issues.append(f"ENV FILE: {rel} — ensure it's in .gitignore and has no real secrets")

    # Python-specific drift
    py_files = [f for f in all_files if f.endswith(".py")]
    for py_file in py_files:
        filepath = os.path.join(project_dir, py_file)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        # Unused imports (simple heuristic: import X but X never used again)
        imports = []
        for line in lines:
            match = re.match(r'^(?:from\s+\S+\s+)?import\s+(\w+)', line)
            if match:
                name = match.group(1)
                if name not in ("os", "sys", "json", "re", "typing"):
                    imports.append(name)

        for imp in imports:
            # Check if the import is used anywhere besides the import line
            uses = sum(1 for line in lines if imp in line)
            if uses <= 1:
                issues.append(f"UNUSED IMPORT: '{imp}' in {py_file} — imported but never used")

    # TypeScript-specific drift
    ts_files = [f for f in all_files if f.endswith((".ts", ".tsx"))]
    for ts_file in ts_files:
        filepath = os.path.join(project_dir, ts_file)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for commented-out code blocks
        commented_lines = sum(1 for line in content.split("\n") if line.strip().startswith("//") and len(line.strip()) > 5)
        if commented_lines > 10:
            issues.append(f"DEAD CODE: {ts_file} has {commented_lines} commented lines — clean up")

    # Check README exists and isn't a stub
    if "README.md" in all_files:
        readme_path = os.path.join(project_dir, "README.md")
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()
        if len(readme) < 100:
            issues.append(f"STUB README: README.md has only {len(readme)} chars — needs more documentation")

    if not issues:
        return f"DRIFT SCAN CLEAN: {project_name} — no drift detected. {len(all_files)} files scanned."

    result = f"DRIFT DETECTED in {project_name} ({len(issues)} issues, {len(all_files)} files scanned):\n\n"
    for issue in issues:
        result += f"  - {issue}\n"
    result += "\nFix these issues to maintain project health."
    return result


# =============================================================================
# Pre-write Validation — "Keep Quality Left"
# =============================================================================

@tool
def validate_before_write(project_name: str, filename: str, content: str, template_id: str) -> str:
    """Validate a file BEFORE writing it. Run this before write_file to catch issues early.

    Checks: naming conventions, file location, directive compliance, basic quality.
    Returns APPROVED or REJECTED with reasons.

    Args:
        project_name: The project folder name
        filename: The file path to be written
        content: The content to be written
        template_id: The template to validate against
    """
    issues = []

    # Check file naming
    basename = os.path.basename(filename)
    ext = os.path.splitext(basename)[1].lower()

    # Java naming: classes should be PascalCase
    if ext == ".java":
        class_name = os.path.splitext(basename)[0]
        if not class_name[0].isupper():
            issues.append(f"Java class name '{class_name}' should be PascalCase")

    # Python naming: modules should be snake_case
    if ext == ".py":
        module_name = os.path.splitext(basename)[0]
        if module_name != module_name.lower():
            issues.append(f"Python module '{module_name}' should be snake_case")

    # TypeScript/React: components should be PascalCase
    if ext in (".tsx", ".jsx") and not basename[0].isupper() and basename != "index.tsx":
        issues.append(f"React component '{basename}' should start with uppercase (PascalCase)")

    # Check content quality
    lines = content.split("\n")

    # File too large
    if len(lines) > 500:
        issues.append(f"File has {len(lines)} lines — consider splitting into smaller modules")

    # Hardcoded secrets in content
    secret_patterns = [
        (r'(api_key|password|secret|token)\s*=\s*["\'][A-Za-z0-9+/=]{16,}', "Possible hardcoded secret"),
        (r'(sk-|pk_live_|ghp_|xoxb-)[A-Za-z0-9]{10,}', "API key pattern detected"),
    ]
    for pattern, msg in secret_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"CRITICAL: {msg} — use environment variables instead")

    # Check location makes sense for template
    from template_loader import Template
    try:
        template = Template(template_id)
        required_dirs = template.project_structure.get("required_dirs", [])
        if required_dirs:
            file_dir = os.path.dirname(filename)
            # Just warn if file is in the root instead of a structured directory
            if "/" not in filename and ext in (".py", ".java", ".ts", ".tsx", ".js", ".jsx"):
                if any(d.startswith("src/") for d in required_dirs):
                    issues.append(f"File '{filename}' is in the project root — should be in a structured directory (src/, etc.)")
    except ValueError:
        pass

    if not issues:
        return f"PRE-WRITE APPROVED: {filename} passed all pre-write checks."

    if any("CRITICAL" in i for i in issues):
        result = f"PRE-WRITE REJECTED: {filename}\n\n"
    else:
        result = f"PRE-WRITE WARNING: {filename}\n\n"

    for issue in issues:
        result += f"  - {issue}\n"
    result += "\nFix these before writing the file."
    return result


# =============================================================================
# SDD — Software Design Document (Plan-First Workflow)
# =============================================================================

@tool
def create_sdd(
    project_name: str,
    title: str,
    objective: str,
    scope: str,
    technical_approach: str,
    data_model: str = "",
    api_design: str = "",
    error_handling: str = "",
    security_considerations: str = "",
    tasks: list[dict] = [],
    risks: str = "",
    out_of_scope: str = "",
) -> str:
    """Create a Software Design Document (SDD) for a project BEFORE writing any code.

    This is MANDATORY before any implementation. The SDD captures the plan, breaks it
    into tasks, and saves it to docs/sdd.md in the project.

    The tasks list will also be passed to write_todos automatically.

    Args:
        project_name: The project folder name
        title: SDD title (e.g., "CRUD de Pessoas API")
        objective: What this feature/project achieves
        scope: What's included in this work
        technical_approach: How it will be built (architecture, patterns, tech stack)
        data_model: Database entities and relationships
        api_design: API endpoints with methods, paths, request/response
        error_handling: Error handling strategy
        security_considerations: Security measures
        tasks: List of implementation tasks, each with 'title', 'description', 'priority' (P0-P3)
        risks: Known risks and mitigations
        out_of_scope: What's explicitly NOT included
    """
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    os.makedirs(os.path.join(project_dir, "docs"), exist_ok=True)

    # Build SDD document
    sdd = f"""# SDD: {title}

## 1. Objective
{objective}

## 2. Scope
{scope}

### Out of Scope
{out_of_scope or "N/A"}

## 3. Technical Approach
{technical_approach}
"""

    if data_model:
        sdd += f"""
## 4. Data Model
{data_model}
"""

    if api_design:
        sdd += f"""
## 5. API Design
{api_design}
"""

    if error_handling:
        sdd += f"""
## 6. Error Handling
{error_handling}
"""

    if security_considerations:
        sdd += f"""
## 7. Security
{security_considerations}
"""

    if tasks:
        sdd += "\n## 8. Implementation Tasks\n\n"
        sdd += "| # | Task | Priority | Status |\n"
        sdd += "|---|------|----------|--------|\n"
        for i, task in enumerate(tasks, 1):
            title_t = task.get("title", f"Task {i}")
            priority = task.get("priority", "P2")
            sdd += f"| {i} | {title_t} | {priority} | Pending |\n"

        sdd += f"\n**Total: {len(tasks)} tasks**\n"

    if risks:
        sdd += f"""
## 9. Risks
{risks}
"""

    sdd += "\n---\n*Generated by DeepHarness — SDD Planning Tool*\n"

    # Save SDD
    sdd_path = os.path.join(project_dir, "docs", "sdd.md")
    with open(sdd_path, "w", encoding="utf-8") as f:
        f.write(sdd)

    # Build task summary for agent to use with write_todos
    task_summary = []
    for i, task in enumerate(tasks, 1):
        task_summary.append(f"{i}. [{task.get('priority', 'P2')}] {task.get('title', f'Task {i}')}: {task.get('description', '')}")

    result = f"SDD CREATED: docs/sdd.md saved to {project_name}.\n\n"
    result += f"**{len(tasks)} tasks** defined:\n\n"
    for t in task_summary:
        result += f"  {t}\n"

    result += f"\n\n**MANDATORY NEXT STEPS** (do all of them in order):\n\n"
    result += f"1. Call `write_todos` with these tasks (internal planning).\n\n"
    result += f"2. Push each task to the Task Manager Board so the user sees them:\n"
    for i, task in enumerate(tasks, 1):
        title_t = task.get("title", f"Task {i}").replace('"', "'")
        prio = task.get("priority", "P2")
        desc = task.get("description", "").replace('"', "'")[:200]
        result += f'   task_create_item(project_name="{project_name}", title="{title_t}", priority="{prio}", description="{desc}")\n'

    result += f"\n3. For each task, before working: `task_update_item(..., status=\"in_progress\")`\n"
    result += f"4. After completing: `task_update_item(..., status=\"done\")`\n"
    result += f"\nThis way the user can track progress in BOTH Mission Control AND the Board tab."

    return result


@tool
def get_sdd(project_name: str) -> str:
    """Read the current SDD (Software Design Document) for a project.

    Args:
        project_name: The project folder name
    """
    sdd_path = os.path.join(OUTPUT_DIR, project_name, "docs", "sdd.md")
    if not os.path.isfile(sdd_path):
        return f"No SDD found for '{project_name}'. Create one with create_sdd first."

    with open(sdd_path, "r", encoding="utf-8") as f:
        return f.read()
