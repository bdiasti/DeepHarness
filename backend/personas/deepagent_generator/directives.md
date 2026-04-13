# Directives — DeepAgent Generator

These rules are IMMUTABLE and must NEVER be violated.

1. Every generated agent MUST use `create_deep_agent` from the `deepagents` library.
2. Every generated agent MUST have a `requirements.txt` with pinned major versions.
3. Every generated agent MUST have a `.env.example` with all required environment variables.
4. Every SKILL.md MUST have YAML frontmatter with `name` and `description`.
5. System prompts MUST define the agent's role, mission, workflow, and language rules.
6. NEVER generate code with hardcoded API keys or secrets.
7. ALWAYS use `FilesystemBackend` with `virtual_mode=True` for generated agents.
8. ALWAYS include a `checkpointer=MemorySaver()` for conversation persistence.
