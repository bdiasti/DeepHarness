"""Custom tools for the DeepAgent Generator."""

import json
import os
from typing import Optional
from langchain.tools import tool

# Output directory where generated agent projects are saved
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _get_project_dir(agent_name: str) -> str:
    """Get the project directory for a given agent name."""
    return os.path.join(OUTPUT_DIR, agent_name)


AVAILABLE_MODELS = {
    "claude-sonnet-4-5-20250929": {
        "name": "Claude Sonnet 4.5",
        "provider": "anthropic",
        "package": "langchain-anthropic",
        "description": "Best balance of speed and intelligence",
    },
    "claude-opus-4-5-20250929": {
        "name": "Claude Opus 4.5",
        "provider": "anthropic",
        "package": "langchain-anthropic",
        "description": "Most capable model for complex tasks",
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "provider": "openai",
        "package": "langchain-openai",
        "description": "OpenAI's most capable multimodal model",
    },
    "gpt-4o-mini": {
        "name": "GPT-4o Mini",
        "provider": "openai",
        "package": "langchain-openai",
        "description": "Fast and cost-effective OpenAI model",
    },
}

AVAILABLE_TOOL_TEMPLATES = {
    "web_search": {
        "name": "Web Search",
        "description": "Search the web for information",
        "package": "langchain-tavily",
        "code": '''from langchain_tavily import TavilySearch

web_search = TavilySearch(max_results=5)''',
    },
    "calculator": {
        "name": "Calculator",
        "description": "Perform mathematical calculations",
        "package": None,
        "code": '''@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"''',
    },
    "http_request": {
        "name": "HTTP Request",
        "description": "Make HTTP requests to APIs",
        "package": "requests",
        "code": '''import requests as req

@tool
def http_request(url: str, method: str = "GET", body: str = "") -> str:
    """Make an HTTP request to an API endpoint."""
    try:
        response = req.request(method, url, data=body if body else None, timeout=30)
        return response.text[:2000]
    except Exception as e:
        return f"Error: {e}"''',
    },
    "database_query": {
        "name": "Database Query",
        "description": "Execute SQL queries against a database",
        "package": "sqlalchemy",
        "code": '''from sqlalchemy import create_engine, text

@tool
def database_query(query: str, connection_string: str = "sqlite:///data.db") -> str:
    """Execute a SQL query and return results."""
    engine = create_engine(connection_string)
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
        return str(rows[:50])''',
    },
    "file_reader": {
        "name": "File Reader",
        "description": "Read contents of local files",
        "package": None,
        "code": '''@tool
def file_reader(path: str) -> str:
    """Read the contents of a file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:5000]
    except Exception as e:
        return f"Error reading file: {e}"''',
    },
    "json_parser": {
        "name": "JSON Parser",
        "description": "Parse and query JSON data",
        "package": None,
        "code": '''import json as json_lib

@tool
def json_parser(data: str, query: str = "") -> str:
    """Parse JSON data and optionally extract a field using dot notation."""
    try:
        parsed = json_lib.loads(data)
        if query:
            for key in query.split("."):
                parsed = parsed[key] if isinstance(parsed, dict) else parsed[int(key)]
        return json_lib.dumps(parsed, indent=2)
    except Exception as e:
        return f"Error: {e}"''',
    },
    "email_sender": {
        "name": "Email Sender",
        "description": "Send emails via SMTP",
        "package": None,
        "code": '''import smtplib
from email.mime.text import MIMEText

@tool
def email_sender(to: str, subject: str, body: str) -> str:
    """Send an email. Requires SMTP_HOST, SMTP_USER, SMTP_PASS env vars."""
    import os
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["To"] = to
    msg["From"] = os.environ.get("SMTP_USER", "agent@example.com")
    try:
        with smtplib.SMTP(os.environ.get("SMTP_HOST", "localhost"), 587) as server:
            server.starttls()
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            server.send_message(msg)
        return f"Email sent to {to}"
    except Exception as e:
        return f"Error sending email: {e}"''',
    },
}

MIDDLEWARE_OPTIONS = {
    "todo_list": {
        "name": "Todo List (Planning)",
        "description": "Allows the agent to break down complex tasks into a tracked todo list",
        "always_on": True,
    },
    "filesystem": {
        "name": "Filesystem",
        "description": "Gives the agent tools to read, write, and manage files",
        "always_on": True,
    },
    "subagent": {
        "name": "Sub-Agent Delegation",
        "description": "Allows the agent to delegate tasks to specialized sub-agents",
        "always_on": True,
    },
    "skills": {
        "name": "Skills (On-demand)",
        "description": "Load specialized SKILL.md files on demand for domain-specific knowledge",
        "always_on": False,
    },
    "memory": {
        "name": "Long-term Memory",
        "description": "Persistent memory across sessions using a Store backend",
        "always_on": False,
    },
    "human_in_the_loop": {
        "name": "Human-in-the-Loop",
        "description": "Require human approval before executing sensitive tools",
        "always_on": False,
    },
}


@tool
def list_available_models() -> str:
    """List all available AI models that can power a deep agent."""
    lines = []
    for model_id, info in AVAILABLE_MODELS.items():
        lines.append(f"- **{info['name']}** (`{model_id}`): {info['description']} [provider: {info['provider']}]")
    return "\n".join(lines)


@tool
def list_available_tools() -> str:
    """List all pre-built tool templates available for deep agents."""
    lines = []
    for tool_id, info in AVAILABLE_TOOL_TEMPLATES.items():
        pkg = f" (requires `{info['package']}`)" if info["package"] else " (built-in)"
        lines.append(f"- **{info['name']}** (`{tool_id}`): {info['description']}{pkg}")
    return "\n".join(lines)


@tool
def list_middleware_options() -> str:
    """List all middleware options for deep agents, showing which are always-on vs opt-in."""
    lines = []
    for mid_id, info in MIDDLEWARE_OPTIONS.items():
        status = "Always ON" if info["always_on"] else "Opt-in"
        lines.append(f"- **{info['name']}** (`{mid_id}`): {info['description']} [{status}]")
    return "\n".join(lines)


@tool
def generate_agent_code(
    agent_name: str,
    model_id: str,
    system_prompt: str,
    tool_ids: list[str],
    custom_tools: list[dict],
    enable_skills: bool = False,
    skills_config: list[dict] = [],
    enable_memory: bool = False,
    enable_hitl: bool = False,
    hitl_tools: list[str] = [],
    subagents: list[dict] = [],
    description: str = "",
) -> str:
    """Generate complete Python code for a deep agent and save all files to disk.

    This tool creates the entire project folder with all files including skills.

    Args:
        agent_name: Name for the agent (snake_case)
        model_id: Model identifier (e.g., 'claude-sonnet-4-5-20250929')
        system_prompt: The system prompt/instructions for the agent
        tool_ids: List of pre-built tool IDs to include (e.g., ['web_search', 'calculator'])
        custom_tools: List of custom tool definitions with 'name', 'description', 'parameters', 'code'
        enable_skills: Whether to enable SkillsMiddleware
        skills_config: List of skill definitions to create. Each skill is a dict with:
            - 'name': skill name (e.g., 'seo_writer')
            - 'description': what the skill does
            - 'content': the full SKILL.md content (instructions for the agent)
            Example: [{"name": "seo_writer", "description": "Writes SEO articles", "content": "## Instructions\\n..."}]
        enable_memory: Whether to enable MemoryMiddleware
        enable_hitl: Whether to enable HumanInTheLoopMiddleware
        hitl_tools: List of tool names that require human approval
        subagents: List of subagent configs with 'name', 'description', 'system_prompt', 'tools'
        description: Brief description of what the agent does
    """
    model_info = AVAILABLE_MODELS.get(model_id)
    if not model_info:
        return f"Error: Unknown model '{model_id}'. Use list_available_models() to see options."

    # Build imports
    imports = [
        "from deepagents import create_deep_agent",
        "from deepagents.backends import FilesystemBackend",
        "from langgraph.checkpoint.memory import MemorySaver",
        "from langchain.tools import tool",
    ]

    if enable_memory:
        imports.append("from langgraph.store.memory import InMemoryStore")

    # Provider-specific imports
    provider_pkg = model_info["package"]
    if provider_pkg == "langchain-anthropic":
        imports.append("from langchain_anthropic import ChatAnthropic")
    elif provider_pkg == "langchain-openai":
        imports.append("from langchain_openai import ChatOpenAI")

    # Build requirements
    requirements = [
        "deepagents",
        "langchain>=1.0,<2.0",
        "langchain-core>=1.0,<2.0",
        "langsmith>=0.3.0",
        provider_pkg,
    ]

    # Tool imports and code
    tool_code_blocks = []
    for tid in tool_ids:
        tmpl = AVAILABLE_TOOL_TEMPLATES.get(tid)
        if tmpl:
            tool_code_blocks.append(tmpl["code"])
            if tmpl["package"]:
                requirements.append(tmpl["package"])

    # Custom tools
    for ct in custom_tools:
        params_str = ", ".join(
            f"{p['name']}: {p.get('type', 'str')}" for p in ct.get("parameters", [])
        )
        tool_code_blocks.append(
            f'''@tool\ndef {ct["name"]}({params_str}) -> str:\n    """{ct["description"]}"""\n    {ct.get("code", "return 'Not implemented yet'")}'''
        )

    # Build tool list
    tool_names = []
    for tid in tool_ids:
        tmpl = AVAILABLE_TOOL_TEMPLATES.get(tid)
        if tmpl:
            # Extract the variable name from the code
            code = tmpl["code"]
            if code.startswith("@tool"):
                # Function-based tool
                fname = code.split("def ")[1].split("(")[0]
                tool_names.append(fname)
            else:
                # Object-based tool (like TavilySearch)
                vname = code.strip().split("\n")[-1].split("=")[0].strip()
                tool_names.append(vname)

    for ct in custom_tools:
        tool_names.append(ct["name"])

    # Build subagent configs
    subagent_code = ""
    if subagents:
        sa_list = []
        for sa in subagents:
            sa_dict = {
                "name": sa["name"],
                "description": sa.get("description", ""),
                "system_prompt": sa.get("system_prompt", "You are a helpful assistant."),
            }
            sa_list.append(f"        {sa_dict},")
        subagent_code = "    subagents=[\n" + "\n".join(sa_list) + "\n    ],"

    # Build interrupt_on
    interrupt_code = ""
    if enable_hitl and hitl_tools:
        interrupt_dict = {t: True for t in hitl_tools}
        interrupt_code = f"    interrupt_on={json.dumps(interrupt_dict)},"

    # Assemble the full code
    imports_str = "\n".join(sorted(set(imports)))
    tools_str = "\n\n\n".join(tool_code_blocks)
    tool_list_str = f"[{', '.join(tool_names)}]" if tool_names else "[]"
    requirements_str = "\n".join(sorted(set(requirements)))

    system_prompt_escaped = system_prompt.replace('"""', '\\"\\"\\"')

    code = f'''"""
{agent_name} - {description}

Generated by DeepAgent Generator
"""

{imports_str}


# === Tools ===

{tools_str}


# === Agent Configuration ===

agent = create_deep_agent(
    name="{agent_name}",
    model="{model_id}",
    system_prompt="""{system_prompt_escaped}""",
    tools={tool_list_str},
    backend=FilesystemBackend(root_dir=".", virtual_mode=True),
    checkpointer=MemorySaver(),
{"    store=InMemoryStore()," if enable_memory else ""}
{"    skills=['./skills/']," if enable_skills else ""}
{subagent_code}
{interrupt_code}
)


# === Run the agent ===

if __name__ == "__main__":
    config = {{"configurable": {{"thread_id": "default"}}}}
    print(f"🤖 {{agent.name or '{agent_name}'}} is ready!")
    print("Type your message (or 'quit' to exit):")
    while True:
        user_input = input("\\n> ")
        if user_input.lower() in ("quit", "exit"):
            break
        result = agent.invoke(
            {{"messages": [{{"role": "user", "content": user_input}}]}},
            config=config,
        )
        last_msg = result["messages"][-1]
        print(f"\\n{{last_msg.content}}")
'''

    # Clean up empty lines from conditional sections
    lines = code.split("\n")
    cleaned = []
    prev_empty = False
    for line in lines:
        is_empty = line.strip() == ""
        if is_empty and prev_empty:
            continue
        cleaned.append(line)
        prev_empty = is_empty
    code = "\n".join(cleaned)

    # --- Save project to disk ---
    project_dir = _get_project_dir(agent_name)
    os.makedirs(project_dir, exist_ok=True)

    files = {
        "agent.py": code,
        "requirements.txt": requirements_str,
        "langgraph.json": json.dumps(
            {"graphs": {"agent": "./agent.py:agent"}}, indent=2
        ),
        ".env.example": "# Add your API keys here\nANTHROPIC_API_KEY=your-key-here\nOPENAI_API_KEY=your-key-here\nLANGSMITH_API_KEY=your-key-here\n",
        "README.md": f"# {agent_name}\n\n{description}\n\n## Setup\n\n```bash\npip install -r requirements.txt\ncp .env.example .env\n# Edit .env with your API keys\n```\n\n## Run\n\n```bash\npython agent.py\n```\n\n## Run with LangGraph Server\n\n```bash\nlanggraph up\n```\n\nGenerated by DeepAgent Generator\n",
    }

    for filename, content in files.items():
        filepath = os.path.join(project_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    # --- Create skills if configured ---
    created_skills = []
    if enable_skills and skills_config:
        for skill in skills_config:
            skill_name = skill.get("name", "unnamed")
            skill_desc = skill.get("description", "")
            skill_content = skill.get("content", "")
            skill_dir = os.path.join(project_dir, "skills", skill_name)
            os.makedirs(skill_dir, exist_ok=True)

            skill_md = f"""---
name: {skill_name}
description: {skill_desc}
---

{skill_content}
"""
            skill_path = os.path.join(skill_dir, "SKILL.md")
            with open(skill_path, "w", encoding="utf-8") as f:
                f.write(skill_md)
            created_skills.append(skill_name)
            files[f"skills/{skill_name}/SKILL.md"] = skill_md

    # Build the result
    result = {
        "agent_name": agent_name,
        "description": description,
        "project_dir": agent_name,
        "files": list(files.keys()),
        "skills": created_skills,
        "model": model_id,
        "tools": tool_ids + [ct["name"] for ct in custom_tools],
        "middleware": {
            "skills": enable_skills,
            "memory": enable_memory,
            "hitl": enable_hitl,
        },
        "subagents": [sa["name"] for sa in subagents],
    }

    return json.dumps(result, indent=2)


@tool
def validate_agent_config(
    agent_name: str,
    model_id: str,
    system_prompt: str,
    tool_ids: list[str],
) -> str:
    """Validate an agent configuration before generating code.

    Args:
        agent_name: Name for the agent
        model_id: Model to use
        system_prompt: System prompt text
        tool_ids: List of tool IDs
    """
    issues = []

    if not agent_name or not agent_name.replace("_", "").replace("-", "").isalnum():
        issues.append("agent_name must be alphanumeric with underscores/hyphens only")

    if model_id not in AVAILABLE_MODELS:
        issues.append(f"Unknown model '{model_id}'. Available: {list(AVAILABLE_MODELS.keys())}")

    if not system_prompt or len(system_prompt) < 10:
        issues.append("system_prompt should be at least 10 characters to be useful")

    for tid in tool_ids:
        if tid not in AVAILABLE_TOOL_TEMPLATES:
            issues.append(f"Unknown tool '{tid}'. Available: {list(AVAILABLE_TOOL_TEMPLATES.keys())}")

    if issues:
        return "Validation FAILED:\n" + "\n".join(f"- {i}" for i in issues)
    return "Validation PASSED. Configuration is valid."


@tool
def list_projects() -> str:
    """List all generated agent projects."""
    if not os.path.isdir(OUTPUT_DIR):
        return "No projects generated yet."

    projects = []
    for name in sorted(os.listdir(OUTPUT_DIR)):
        project_dir = os.path.join(OUTPUT_DIR, name)
        if os.path.isdir(project_dir):
            files = os.listdir(project_dir)
            projects.append(f"- **{name}/** ({len(files)} files: {', '.join(files)})")

    if not projects:
        return "No projects generated yet."
    return "Generated projects:\n" + "\n".join(projects)
