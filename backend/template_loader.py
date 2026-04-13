"""
Template Loader — Composes Personas (behavior) + Skills (capabilities).

New model:
- 1 Persona = mandatory (defines directives, subagents, system prompt)
- N Skills = optional (define tech knowledge, methodologies)

Skills come from skills_library/<category>/<skill_name>/SKILL.md
Categories: frontend, backend, methodology, testing, architecture, devops, mobile, database
"""

import json
import os
import shutil
from typing import Optional

from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from tools import OUTPUT_DIR

BACKEND_DIR = os.path.dirname(__file__)
PERSONAS_DIR = os.path.join(BACKEND_DIR, "personas")
SKILLS_LIBRARY_DIR = os.path.join(BACKEND_DIR, "skills_library")
PROJECT_TYPES_DIR = os.path.join(BACKEND_DIR, "project_types")


class ProjectType:
    """A project type — defines the CONSTITUTION (immutable project-wide rules)."""

    def __init__(self, type_id: str):
        self.id = type_id
        self.dir = os.path.join(PROJECT_TYPES_DIR, type_id)
        if not os.path.isdir(self.dir):
            raise ValueError(f"ProjectType '{type_id}' not found")

        with open(os.path.join(self.dir, "config.json"), "r", encoding="utf-8") as f:
            self.config = json.load(f)

        constitution_path = os.path.join(self.dir, "constitution.md")
        self.constitution = ""
        if os.path.isfile(constitution_path):
            with open(constitution_path, "r", encoding="utf-8") as f:
                self.constitution = f.read()

    @property
    def name(self): return self.config["name"]
    @property
    def description(self): return self.config.get("description", "")
    @property
    def icon(self): return self.config.get("icon", "layers")
    @property
    def color(self): return self.config.get("color", "#64748b")
    @property
    def mandatory_stack(self): return self.config.get("mandatory_stack", [])
    @property
    def project_structure(self): return self.config.get("project_structure", {})

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "mandatory_stack": self.mandatory_stack,
            "constitution": self.constitution,
            "project_structure": self.project_structure,
        }


def list_project_types() -> list[dict]:
    result = []
    if not os.path.isdir(PROJECT_TYPES_DIR):
        return result
    for name in sorted(os.listdir(PROJECT_TYPES_DIR)):
        if os.path.isfile(os.path.join(PROJECT_TYPES_DIR, name, "config.json")):
            try:
                result.append(ProjectType(name).to_dict())
            except Exception:
                pass
    return result


class Persona:
    """A behavior template — defines HOW the agent acts."""

    def __init__(self, persona_id: str):
        self.id = persona_id
        self.dir = os.path.join(PERSONAS_DIR, persona_id)
        if not os.path.isdir(self.dir):
            raise ValueError(f"Persona '{persona_id}' not found")

        with open(os.path.join(self.dir, "config.json"), "r", encoding="utf-8") as f:
            self.config = json.load(f)

        directives_path = os.path.join(self.dir, "directives.md")
        self.directives = ""
        if os.path.isfile(directives_path):
            with open(directives_path, "r", encoding="utf-8") as f:
                self.directives = f.read()

        self.skills_dir = os.path.join(self.dir, "skills")

    @property
    def name(self): return self.config["name"]
    @property
    def description(self): return self.config.get("description", "")
    @property
    def icon(self): return self.config.get("icon", "bot")
    @property
    def color(self): return self.config.get("color", "#6366f1")
    @property
    def system_prompt_prefix(self): return self.config.get("system_prompt_prefix", "")
    @property
    def subagents(self): return self.config.get("subagents", [])
    @property
    def hitl_tools(self): return self.config.get("human_in_the_loop", [])
    @property
    def required_skills(self): return self.config.get("required_skills", [])
    @property
    def recommended_skills(self): return self.config.get("recommended_skills", [])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "has_subagents": len(self.subagents) > 0,
            "required_skills": self.required_skills,
            "recommended_skills": self.recommended_skills,
        }


# ═══════════════════════════════════════════
# Skills Library
# ═══════════════════════════════════════════

def list_skills_library() -> list[dict]:
    """List all skills from the library, organized by category."""
    if not os.path.isdir(SKILLS_LIBRARY_DIR):
        return []

    skills = []
    for category in sorted(os.listdir(SKILLS_LIBRARY_DIR)):
        cat_dir = os.path.join(SKILLS_LIBRARY_DIR, category)
        if not os.path.isdir(cat_dir):
            continue
        for skill_name in sorted(os.listdir(cat_dir)):
            skill_dir = os.path.join(cat_dir, skill_name)
            skill_md = os.path.join(skill_dir, "SKILL.md")
            if os.path.isfile(skill_md):
                # Parse frontmatter
                description = ""
                try:
                    with open(skill_md, "r", encoding="utf-8") as f:
                        content = f.read()
                    if content.startswith("---"):
                        end = content.index("---", 3)
                        frontmatter = content[3:end]
                        for line in frontmatter.split("\n"):
                            if line.startswith("description:"):
                                description = line.split(":", 1)[1].strip()
                                break
                except Exception:
                    pass

                skills.append({
                    "id": f"{category}/{skill_name}",
                    "name": skill_name,
                    "category": category,
                    "description": description,
                })
    return skills


def get_skill_paths(skill_ids: list[str]) -> list[str]:
    """Convert skill IDs (category/name) to absolute paths."""
    paths = []
    for sid in skill_ids:
        p = os.path.join(SKILLS_LIBRARY_DIR, sid)
        if os.path.isdir(p):
            paths.append(p)
    return paths


# ═══════════════════════════════════════════
# Listing
# ═══════════════════════════════════════════

def list_personas() -> list[dict]:
    result = []
    if not os.path.isdir(PERSONAS_DIR):
        return result
    for name in sorted(os.listdir(PERSONAS_DIR)):
        if os.path.isfile(os.path.join(PERSONAS_DIR, name, "config.json")):
            try:
                result.append(Persona(name).to_dict())
            except Exception:
                pass
    return result


# Legacy compat
def list_templates() -> list[dict]:
    return list_personas()


def list_stacks() -> list[dict]:
    """Legacy — return empty; stacks are replaced by skills."""
    return []


# ═══════════════════════════════════════════
# Composition
# ═══════════════════════════════════════════

def build_system_prompt(persona: Persona, skill_ids: list[str], project_type: "ProjectType" = None) -> str:
    """Combine project_type + persona + skills into a full system prompt."""

    required = set(persona.required_skills)

    # Project constitution
    constitution_text = ""
    project_structure_text = ""
    if project_type and project_type.id != "custom":
        constitution_text = f"\n\n## PROJECT CONSTITUTION ({project_type.name})\nThese rules override everything. They cannot be negotiated.\n\n{project_type.constitution}"
        ps = project_type.project_structure
        dirs = ps.get("required_dirs", [])
        files = ps.get("files", [])
        if dirs or files:
            project_structure_text = f"\n\n## Project Structure (from project type {project_type.name})\nALWAYS create this structure:\n"
            for d in dirs:
                project_structure_text += f"- `{d}`\n"
            for f in files:
                project_structure_text += f"- `{f}`\n"

    skills_text = ""
    if skill_ids:
        by_cat: dict[str, list[tuple[str, bool]]] = {}
        for sid in skill_ids:
            parts = sid.split("/", 1)
            if len(parts) == 2:
                cat, name = parts
                is_required = sid in required
                by_cat.setdefault(cat, []).append((name, is_required))
        if by_cat:
            skills_text = "\n\n## Your Skills\nYou have these skills available (loaded on demand):\n"
            for cat, entries in by_cat.items():
                labels = []
                for name, is_req in entries:
                    labels.append(f"{name}{' [REQUIRED]' if is_req else ''}")
                skills_text += f"- **{cat}**: {', '.join(labels)}\n"
            skills_text += "\nSkills marked [REQUIRED] are core to your persona — always apply them.\nUse other skills when relevant to the task."

    persona_directives = ""
    if persona.directives:
        persona_directives = f"\n\n## IMMUTABLE DIRECTIVES — {persona.name}\n{persona.directives}"

    return f"""{persona.system_prompt_prefix}
{skills_text}

## Your Capabilities
You are a Deep Agent with:
- `write_todos` — Plan and track tasks
- `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep` — Filesystem (rooted at output/)
- `task` — Delegate to specialized subagents

## Harness Sensors (Feedback Controls)
- `validate_before_write` — Pre-check before saving files
- `run_linter` — Lint code files
- `check_directives` — Verify directive compliance
- `validate_structure` — Check project structure
- `review_code` — Deep code review
- `scan_drift` — Find dead code
- `harness_status` — Full health report

After writing any code: run_linter → check_directives → fix if needed

## Planning (SDD)
- `create_sdd` — Software Design Document for complex work
- `write_todos` — Internal task tracking
- `task_create_item` — Push tasks to Task Manager Board (user sees these)

## Task Manager Sync
For non-trivial work: push tasks to the Board via `task_create_item`, update status:
- `task_update_item(..., status="in_progress")` before coding
- `task_update_item(..., status="review")` before sensors
- `task_update_item(..., status="done")` after sensors pass

## File Operations (CRITICAL — read carefully)
- Your filesystem root is ALREADY `output/`. You do NOT need to prefix paths with `output/`.
- CORRECT: `write_file(path="dogs_crud/agent.py", content="...")`
- WRONG: `write_file(path="output/dogs_crud/agent.py", content="...")` — this creates `output/output/dogs_crud/`.
- Project name should be the FIRST segment. Example: `my_project/src/file.py`
- NEVER include `output/` or `/output/` in any path.
- `write_file` for NEW files, `edit_file` for changes. Directories auto-created.
- NEVER claim you created a file without calling write_file. Verify with `ls`.
{project_structure_text}
{constitution_text}
{persona_directives}

## Workflow by Complexity — THE BOARD IS MANDATORY

### Simple (1 file change)
- Just write/edit the file + run_linter. No board needed.

### Medium / Complex (any new project, or 2+ files)
This workflow is **MANDATORY**. Skipping the Board is NOT allowed.

**STEP 1 — Plan on the Board**
For each task you will do, call `task_create_item` ONE BY ONE:
```
task_create_item(project_name="fruit_cake_agent", title="Create agent.py", priority="P0", status="todo")
task_create_item(project_name="fruit_cake_agent", title="Create SKILL.md", priority="P1", status="todo")
task_create_item(project_name="fruit_cake_agent", title="Create requirements.txt", priority="P1", status="todo")
... (one call per task)
```
The item_id returned is UUID. Save them (use write_todos if helps you track).

**STEP 2 — Execute each task strictly**
For EACH task, in order:
1. `task_update_item(project_name, item_id, status="in_progress")` BEFORE writing
2. `write_file` or `edit_file` — the actual work
3. `task_update_item(project_name, item_id, status="review")` BEFORE sensors
4. `run_linter` + `check_directives` — validate
5. If issues: `edit_file` to fix, then re-run sensors
6. `task_update_item(project_name, item_id, status="done")` AFTER sensors pass

**NEVER batch all status updates at the end.** The user watches the Board live — cards must move individually as you work.

**If you don't push to the board, the user literally cannot see your progress.** Always push.

### Parallel tasks
Multiple tasks can be in_progress simultaneously IF they don't depend on each other (different files).

## Language
Respond in the same language as the user.
"""


def create_agent_for_combo(
    persona: Persona,
    skill_ids: list[str],
    model: ChatOpenAI,
    extra_tools: list = None,
    project_type: "ProjectType" = None,
):
    """Create a Deep Agent for a project_type + persona + skills combo.

    Enforcement hierarchy:
    1. Project type's mandatory_stack (highest priority)
    2. Persona's required_skills
    3. User's chosen skills
    """
    # Enforce: project type mandatory stack + persona required + user chosen
    enforced: list[str] = []
    if project_type:
        for s in project_type.mandatory_stack:
            if s not in enforced:
                enforced.append(s)
    for s in persona.required_skills:
        if s not in enforced:
            enforced.append(s)
    for s in skill_ids:
        if s not in enforced:
            enforced.append(s)
    skill_ids = enforced

    skills_paths = []

    # Persona skills (if any)
    if os.path.isdir(persona.skills_dir) and os.listdir(persona.skills_dir):
        dst = os.path.join(OUTPUT_DIR, f".persona_skills_{persona.id}")
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(persona.skills_dir, dst)
        skills_paths.append(f".persona_skills_{persona.id}/")

    # Library skills — copy each into output dir
    for sid in skill_ids:
        src = os.path.join(SKILLS_LIBRARY_DIR, sid)
        if os.path.isdir(src):
            safe_name = sid.replace("/", "_")
            dst_rel = f".skill_{safe_name}"
            dst = os.path.join(OUTPUT_DIR, dst_rel)
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            # Copy contents (SKILL.md) into dst directory
            os.makedirs(dst, exist_ok=True)
            for item in os.listdir(src):
                shutil.copy(os.path.join(src, item), os.path.join(dst, item))
            skills_paths.append(f"{dst_rel}/")

    interrupt_on = None
    if persona.hitl_tools:
        interrupt_on = {t: True for t in persona.hitl_tools}

    system_prompt = build_system_prompt(persona, skill_ids, project_type)

    kwargs = {
        "name": f"harness-{persona.id}",
        "model": model,
        "system_prompt": system_prompt,
        "tools": list(extra_tools or []),
        "backend": FilesystemBackend(root_dir=OUTPUT_DIR, virtual_mode=True),
        "checkpointer": MemorySaver(),
        "store": InMemoryStore(),
    }

    if skills_paths:
        kwargs["skills"] = skills_paths
    if persona.subagents:
        kwargs["subagents"] = persona.subagents
    if interrupt_on:
        kwargs["interrupt_on"] = interrupt_on

    return create_deep_agent(**kwargs)


# Legacy
class Template:
    def __init__(self, template_id: str):
        self.persona = Persona(template_id)
        self.id = template_id

    @property
    def name(self): return self.persona.name
    @property
    def skills_dir(self): return self.persona.skills_dir
    @property
    def subagents(self): return self.persona.subagents
    @property
    def hitl_tools(self): return self.persona.hitl_tools


def create_agent_for_template(template, model, extra_tools=None):
    """Legacy function."""
    persona = template.persona if isinstance(template, Template) else Persona(template.id if hasattr(template, "id") else template)
    return create_agent_for_combo(persona, [], model, extra_tools)


# Legacy Stack class — keeps imports working but empty
class Stack:
    def __init__(self, stack_id: str):
        self.id = stack_id
        self.name = "Legacy"
        self.skills_dir = ""
    def to_dict(self):
        return {"id": self.id, "name": self.name}
