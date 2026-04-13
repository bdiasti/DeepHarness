---
name: deepagent-examples
description: Ready-to-use Deep Agent code examples for common use cases — customer support, research, data analysis, email automation, and coding assistants
---

# Deep Agent Examples

## Customer Support Agent

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langchain.tools import tool

@tool
def search_knowledge_base(query: str) -> str:
    """Search the company knowledge base for answers."""
    # Replace with your actual KB search
    return f"Knowledge base results for: {query}"

@tool
def create_ticket(subject: str, description: str, priority: str = "medium") -> str:
    """Create a support ticket for issues that need escalation."""
    return f"Ticket created: {subject} (priority: {priority})"

agent = create_deep_agent(
    name="support-agent",
    model="openai:gpt-4o",
    system_prompt="""You are a friendly customer support agent.

## Guidelines
- Always greet the customer warmly
- Search the knowledge base before answering
- If you can't resolve the issue, create a ticket
- Never share internal information
- Be empathetic and professional
""",
    tools=[search_knowledge_base, create_ticket],
    backend=FilesystemBackend(root_dir=".", virtual_mode=True),
    checkpointer=MemorySaver(),
    store=InMemoryStore(),
)
```

## Research Agent with Subagents

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

agent = create_deep_agent(
    name="research-agent",
    model="anthropic:claude-sonnet-4-6",
    system_prompt="""You are a research coordinator.
Use the researcher subagent to gather information, then synthesize findings.
Save research reports using write_file.
Use write_todos to plan your research steps.""",
    tools=[],
    subagents=[
        {
            "name": "researcher",
            "description": "Search the web and compile findings on a topic",
            "system_prompt": "You are a thorough researcher. Search for information and return detailed findings with sources.",
            "tools": [web_search_tool],
        }
    ],
    backend=FilesystemBackend(root_dir=".", virtual_mode=True),
    checkpointer=MemorySaver(),
)
```

## Data Analysis Agent

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool

@tool
def run_sql(query: str) -> str:
    """Execute a SQL query against the analytics database."""
    from sqlalchemy import create_engine, text
    engine = create_engine("sqlite:///analytics.db")
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
        return str(rows[:100])

@tool
def create_chart(data: str, chart_type: str = "bar", title: str = "") -> str:
    """Create a chart from data. chart_type: bar, line, pie, scatter."""
    return f"Chart '{title}' created as {chart_type} chart"

agent = create_deep_agent(
    name="data-analyst",
    model="openai:gpt-4o",
    system_prompt="""You are a data analyst. You can:
- Query databases with SQL
- Create charts and visualizations
- Save analysis reports as files
- Plan complex analyses with todos

Always explain your findings in plain language.""",
    tools=[run_sql, create_chart],
    backend=FilesystemBackend(root_dir=".", virtual_mode=True),
    checkpointer=MemorySaver(),
)
```

## Email Automation Agent

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to the specified recipient."""
    import smtplib, os
    from email.mime.text import MIMEText
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["To"] = to
    msg["From"] = os.environ["SMTP_USER"]
    with smtplib.SMTP(os.environ["SMTP_HOST"], 587) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)
    return f"Email sent to {to}"

@tool
def list_emails(folder: str = "inbox", limit: int = 10) -> str:
    """List recent emails from a folder."""
    return f"Listing {limit} emails from {folder}"

agent = create_deep_agent(
    name="email-agent",
    model="openai:gpt-4o",
    system_prompt="""You are an email assistant. You can:
- Read and summarize emails
- Draft and send emails
- Organize emails into categories
Always ask for confirmation before sending emails.""",
    tools=[send_email, list_emails],
    backend=FilesystemBackend(root_dir=".", virtual_mode=True),
    interrupt_on={"send_email": True},  # Require approval before sending
    checkpointer=MemorySaver(),
)
```
