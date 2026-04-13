---
name: agent-builder
description: Complete guide for building Deep Agents with create_deep_agent — covers architecture, model config, tools, subagents, skills, middleware, backends, and best practices
---

# Deep Agent Builder Skill

## Overview
This skill provides expert knowledge on creating effective Deep Agents using the
`create_deep_agent()` function from the `deepagents` library.

## Deep Agent Architecture

Deep Agents are built on LangGraph and include automatic middleware:
- **TodoListMiddleware** (always on): `write_todos` tool for planning
- **FilesystemMiddleware** (always on): `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`
- **SubAgentMiddleware** (always on): `task` tool for delegation
- **SkillsMiddleware** (opt-in): Load SKILL.md files on demand
- **MemoryMiddleware** (opt-in): Long-term memory via Store
- **HumanInTheLoopMiddleware** (opt-in): Approval before sensitive ops

## Creating a Deep Agent

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langchain.tools import tool

# Custom tools
@tool
def my_tool(query: str) -> str:
    """Description of what the tool does."""
    return f"Result for {query}"

# Create the agent
agent = create_deep_agent(
    name="my-agent",
    model="anthropic:claude-sonnet-4-6",  # or pass a ChatModel instance
    system_prompt="You are a helpful assistant that...",
    tools=[my_tool],
    backend=FilesystemBackend(root_dir=".", virtual_mode=True),
    checkpointer=MemorySaver(),
    # Optional:
    # store=InMemoryStore(),          # for memory middleware
    # skills=["./skills/"],           # for skills middleware
    # subagents=[{...}],              # for custom subagents
    # interrupt_on={"tool_name": True} # for HITL (requires checkpointer)
)
```

## Model Configuration

Models can be specified as strings or instances:
- `"anthropic:claude-sonnet-4-6"` — Anthropic Claude
- `"openai:gpt-4o"` — OpenAI
- `"google:gemini-2.5-pro"` — Google
- Or pass an initialized LangChain chat model instance for custom endpoints (Azure, etc.)

## System Prompt Best Practices

A good system prompt should have:
1. **Role definition**: Who the agent is
2. **Mission**: What it should accomplish
3. **Workflow**: Step-by-step instructions
4. **Guidelines**: How it should behave
5. **Constraints**: What it should NOT do

## Tool Selection Guide

### When to use pre-built tools
- `web_search`: Agent needs current information from the internet
- `calculator`: Math, data analysis, or financial calculations
- `http_request`: Integration with external APIs
- `database_query`: Read/write structured data
- `file_reader`: Process local documents

### When to create custom tools
- Domain-specific logic required
- Proprietary API integration
- Specific business rules

## Subagent Patterns

Add subagents when the main task has clearly distinct subtasks:

```python
agent = create_deep_agent(
    subagents=[
        {
            "name": "researcher",
            "description": "Research information on a topic",
            "system_prompt": "You are a research specialist...",
            "tools": [search_tool],
        },
        {
            "name": "writer",
            "description": "Write content based on research",
            "system_prompt": "You are a content writer...",
        }
    ]
)
```

Common patterns:
1. **Researcher + Writer**: One gathers info, another produces output
2. **Planner + Executor**: One creates the plan, another executes
3. **Validator**: Reviews output quality before returning

## Skills Setup

Skills require a FilesystemBackend and a directory with SKILL.md files:

```
skills/
└── my-skill/
    └── SKILL.md    # Must have YAML frontmatter with name + description
```

## Middleware Recommendations

| Use Case | Enable |
|----------|--------|
| Long-running sessions with users | Memory (requires Store) |
| Multi-domain agent | Skills |
| High-stakes operations | HITL (requires checkpointer) |
| Complex multi-step tasks | TodoList (always on) |

## Common Mistakes to Avoid

1. Skills without FilesystemBackend — skills won't load
2. HITL without checkpointer — interrupts won't work
3. Memory without Store — will error
4. Vague SKILL.md descriptions — agent won't know when to load them
5. Subagents don't inherit skills — provide them explicitly
