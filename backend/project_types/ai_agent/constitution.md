# Constitution — AI Agent Project

These rules are IMMUTABLE.

## Framework (FIXED)
1. MUST use `deepagents` library from LangChain — no other agent framework.
2. MUST use `create_deep_agent()` as the entry point.
3. Skills MUST follow SKILL.md format with YAML frontmatter (name, description).
4. Subagents MUST be defined via `subagents=[...]` parameter.

## Architecture
5. Tools MUST be decorated with `@tool` from `langchain.tools`.
6. Tool names MUST be snake_case.
7. Filesystem operations MUST use `FilesystemBackend` (not direct os calls in tools).
8. Persistence MUST use `MemorySaver` or `InMemoryStore` (or proper backend).

## Configuration
9. API keys MUST come from environment variables (never hardcoded).
10. Model config MUST support multiple providers (OpenAI, Anthropic, Azure).
11. Must include `langgraph.json` for LangGraph Server compatibility.

## Quality
12. Every tool MUST have a clear docstring with Args description.
13. System prompt MUST define: role, mission, workflow, language.
14. Directives MUST be enforced via system prompt (immutable rules).

## What's NOT allowed
- Do NOT use other agent frameworks (no AutoGen, no CrewAI, no raw OpenAI).
- Do NOT hardcode secrets anywhere.
- Do NOT skip the SKILL.md frontmatter format.
