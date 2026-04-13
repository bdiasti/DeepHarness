# DeepHarness — Engineering Platform for AI Agents

![DeepHarness Presentation](presentation.gif)

A harness engineering platform built on top of [LangChain Deep Agents](https://github.com/langchain-ai/deepagents), inspired by [Birgitta Böckeler](https://www.thoughtworks.com/profiles/b/birgitta-bockeler)'s article [Harness Engineering for Coding Agent Users](https://martinfowler.com/articles/harness-engineering.html) (published on martinfowler.com). DeepHarness turns coding agents into disciplined engineering collaborators by surrounding them with a full SDLC harness: feedforward guides (skills, personas, constitutions), feedback sensors (linters, SAST, drift scans, code review), and 16 SDLC integrations that run locally via Docker.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite + Tailwind)                             │
│  ┌───────────┬──────────────────┬──────────────┐                │
│  │   Chat    │ Mission Control  │ Integrations │                │
│  │           │ (real-time       │  (SDLC view) │                │
│  │           │  timeline)       │              │                │
│  └───────────┴──────────────────┴──────────────┘                │
├─────────────────────────────────────────────────────────────────┤
│  Backend (FastAPI + Deep Agents + LangGraph)                    │
│  ┌───────────────┬──────────┬────────────┬─────────────────┐    │
│  │ Project Types │ Personas │   Skills   │  Integrations   │    │
│  │ (constitution)│ (6 roles)│ (27 skills)│ (16 providers)  │    │
│  └───────────────┴──────────┴────────────┴─────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  Azure AI Foundry (GPT-5.3) — or any OpenAI-compatible model    │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

All you need is Python and Node.js. No external integration is required to get started.

```bash
# 1. Backend
cd backend
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Azure/OpenAI API key
python server.py

# 2. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**. The harness works out of the box with:

- Chat with the agent
- 6 engineering personas
- Sensors (linter, directives, drift)
- Built-in Task Manager
- Mission Control showing everything in real time

---

## Model Configuration (.env)

```bash
# Azure AI Foundry (OpenAI-compatible)
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_MODEL=gpt-4o

# OR OpenAI directly
# AZURE_OPENAI_ENDPOINT=https://api.openai.com/v1/
# AZURE_OPENAI_API_KEY=sk-...
# AZURE_OPENAI_MODEL=gpt-4o

# OR any OpenAI-compatible endpoint (Ollama, LM Studio, etc.)
# AZURE_OPENAI_ENDPOINT=http://localhost:11434/v1/
# AZURE_OPENAI_MODEL=llama3
```

---

## Core Concepts

DeepHarness organizes agent behavior across a three-tier hierarchy. Each tier answers a different question and composes with the others to produce a focused, disciplined agent for a given job.

### 1. Project Type — the Constitution (immutable)

A **project type** is the immutable constitution of the work being done. It defines non-negotiable structure, directives, quality gates and guardrails. The agent cannot violate the project type. Examples: a `web_app_jhipster` project enforces a JHipster layout; a `microservice` project enforces 12-factor principles and observability.

### 2. Persona — Role Directives and Skill Requirements

A **persona** is the role the agent is playing (Architect, Developer, QA, Product Owner, etc.). A persona declares:

- **Role directives** — how the persona thinks, reviews, prioritizes
- **`required_skills`** — skills that MUST be loaded for the persona to function
- **`recommended_skills`** — skills the persona will pull in based on task context

Personas are stackable on top of any project type.

### 3. Skills Library — Composable Capabilities

**Skills** are small, composable capability modules. Each skill contains a SKILL.md (instructions, patterns, examples) and optional scripts. Skills are grouped in categories: `frontend`, `backend`, `methodology`, `testing`, `architecture`, `devops`, `mobile`, `database`.

The agent mixes and matches: Project Type × Persona × Skills = a specialized agent for the task at hand.

---

## Personas Available

| Persona | Role | Required Skills | Recommended Skills |
|---------|------|-----------------|--------------------|
| **Software Architect** | Designs systems, writes ADRs/SDDs | system_design, adr_writer, sdd_writer | c4_diagrams, threat_modeling |
| **Product Owner** | Defines requirements, backlog, PRDs | user_stories, prd_writer | ux_research, roadmapping |
| **Developer (Fullstack)** | Implements features end-to-end | react_components, spring_boot_api, api_integration | database_design, testing_unit |
| **QA Engineer** | Test strategy, cases, automation | test_strategy, test_cases, test_automation | playwright_e2e, performance_testing |
| **DevOps Engineer** | CI/CD, infra, observability | docker_compose, cicd_pipeline | k8s_manifests, monitoring_stack |
| **DeepAgent Generator** | Builds new AI agents | agent_builder, deepagent_examples | langgraph_patterns |

---

## Project Types

| Project Type | Constitution Enforces |
|--------------|-----------------------|
| **web_app_jhipster** | JHipster layout (Spring Boot + React), Liquibase migrations, JWT auth |
| **ai_agent** | Deep Agents structure, skills dir, SKILL.md format, tool registry |
| **microservice** | 12-factor, health endpoints, structured logging, Dockerfile, OpenAPI |
| **mobile_app** | React Native / Flutter layout, platform configs, store metadata |
| **cli_tool** | Argparse/Click entrypoint, man page, installable package |
| **library** | Public API surface, semver, changelog, docs site, published artifacts |
| **custom** | User-defined constitution via `harness.md` |

---

## Skills Library

Roughly 27 composable skills organized by category.

### Frontend
| Skill | Purpose |
|-------|---------|
| react_components | Idiomatic React components, hooks, state |
| vue_components | Vue 3 + Composition API patterns |
| tailwind_design | Tailwind design system and tokens |
| accessibility_a11y | WCAG 2.1 AA compliance patterns |

### Backend
| Skill | Purpose |
|-------|---------|
| spring_boot_api | Spring Boot REST API patterns |
| fastapi_service | FastAPI async service patterns |
| node_express_api | Node.js + Express API patterns |
| api_integration | HTTP clients, retries, idempotency |

### Methodology
| Skill | Purpose |
|-------|---------|
| user_stories | INVEST user stories with acceptance criteria |
| prd_writer | Product requirements document template |
| adr_writer | Architecture Decision Records |
| sdd_writer | Solution/System Design Documents |

### Testing
| Skill | Purpose |
|-------|---------|
| test_strategy | Test pyramid, risk-based strategy |
| test_cases | Gherkin / structured test case authoring |
| test_automation | Framework selection and patterns |
| playwright_e2e | Playwright end-to-end scenarios |

### Architecture
| Skill | Purpose |
|-------|---------|
| system_design | High-level system design patterns |
| c4_diagrams | C4 model diagramming |
| threat_modeling | STRIDE threat modeling |

### DevOps
| Skill | Purpose |
|-------|---------|
| docker_compose | Multi-service Docker Compose stacks |
| cicd_pipeline | GitLab CI / GitHub Actions pipelines |
| k8s_manifests | Kubernetes deployment, service, ingress |
| monitoring_stack | Prometheus + Grafana dashboards |

### Mobile
| Skill | Purpose |
|-------|---------|
| react_native_app | React Native app scaffolding and navigation |
| flutter_app | Flutter app scaffolding and state management |

### Database
| Skill | Purpose |
|-------|---------|
| database_design | Relational modeling, normalization |
| flyway_migrations | Flyway / Liquibase migration patterns |

---

## SDLC Integrations

All integrations are **optional**. Without them, the agent still generates code and configurations. With them, the agent runs the commands directly. Configure them per project via `integrations.json`.

The 16 providers, grouped by SDLC phase:

### Plan
- **Task Manager (built-in)** — JSON-backed task board, zero install
- **Azure DevOps** — Work items, boards, sprints via PAT token

### Develop
- **Git** — Local version control (uses system git)
- **GitLab** — Remote repo, MRs, pipelines
- **HashiCorp Vault** — Secrets management

### Review
- **SonarQube** — Code quality gates, coverage, duplication
- **Semgrep** — SAST rules, custom security patterns

### Test
- **Playwright** — E2E browser testing
- **Flyway** — Database migration validation

### Build
- **GitLab CI/CD** — Pipeline generation and execution
- **Docker Registry** — Container image registry

### Deploy
- **Docker** — Local container deployment
- **K3s / K3d** — Lightweight Kubernetes for staging
- **Kubernetes** — Production cluster deployment

### Monitor
- **Grafana + Prometheus** — Metrics and dashboards
- **Ntfy** — Push notifications (self-hosted or cloud)
- **Flagsmith** — Feature flags

---

## How to Bring Up Each Integration Locally

### PLAN — Task Management

**Task Manager (built-in)** — already enabled, nothing to install. Stores tasks as JSON inside the project.

**Azure DevOps** — configure in `integrations.json`:
```json
{
  "task_management": {
    "provider": "azdevops",
    "organization": "your-org",
    "project": "your-project",
    "token": "your-PAT-token",
    "enabled": true
  }
}
```
Generate the PAT in: Azure DevOps > User Settings > Personal Access Tokens.

### DEVELOP — Version Control and Secrets

**Git** — works if Git is installed:
```bash
git --version
# If missing: https://git-scm.com/downloads
```

**GitLab** — configure in `integrations.json`:
```json
{
  "version_control": {
    "provider": "gitlab",
    "url": "https://gitlab.com",
    "project": "your-group/your-repo",
    "token": "glpat-xxxx",
    "enabled": true
  }
}
```

**HashiCorp Vault (local)**:
```bash
docker run -d \
  --name vault \
  -p 8200:8200 \
  -e VAULT_DEV_ROOT_TOKEN_ID=dev-token \
  hashicorp/vault

curl http://localhost:8200/v1/sys/health
# Default token: dev-token  —  UI: http://localhost:8200
```

### REVIEW — Quality and Security

**SonarQube (local)**:
```bash
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
# Wait ~2 minutes, open http://localhost:9000 (admin/admin)
# Generate token: Administration > Security > Users > Tokens
```

**Semgrep (local)**:
```bash
python -m pip install semgrep
# or use Docker transparently (the agent falls back to docker run if semgrep is not on PATH)
semgrep --version
```

### TEST — E2E and Database

**Playwright (local)**:
```bash
cd your-project
npm init -y
npm install -D @playwright/test
npx playwright install
npx playwright --version
```

**Flyway + PostgreSQL (local)**:
```bash
docker run -d \
  --name postgres \
  -p 5432:5432 \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=app \
  -e POSTGRES_DB=app \
  postgres:16

# Flyway runs via Docker automatically:
# docker run --rm flyway/flyway migrate
```

### BUILD — CI/CD and Registry

**GitLab CI/CD** — no install needed, the agent generates `.gitlab-ci.yml`. Optional local runner:
```bash
pip install gitlab-runner
# or https://docs.gitlab.com/runner/install/
```

**Docker Registry (local)**:
```bash
docker run -d --name registry -p 5000:5000 registry:2
curl http://localhost:5000/v2/
docker push localhost:5000/my-image:tag
```

### DEPLOY — Local, Staging, Production

**Docker (local)** — install Docker Desktop: https://docs.docker.com/desktop/install/windows-install/
```bash
docker info
docker compose version
```

**K3s / K3d (staging on Windows)**:
```bash
choco install k3d     # or: winget install k3d
k3d cluster create staging
kubectl get nodes
k3d kubeconfig get staging > ~/.kube/k3s.yaml
```

**Kubernetes (production)** — point kubeconfig at a real cluster:
```bash
kubectl cluster-info
kubectl get nodes
```

### MONITOR — Observability and Alerts

**Grafana + Prometheus (local)** — the agent generates `docker-compose.monitoring.yml`. Manually:
```bash
docker compose -f docker-compose.monitoring.yml up -d
# Grafana: http://localhost:3001 (admin/admin)
# Prometheus: http://localhost:9090
```

**Ntfy (local)**:
```bash
docker run -d --name ntfy -p 8080:80 binwiederhier/ntfy serve
curl -d "Notification test" http://localhost:8080/harness
# Or use ntfy.sh (free cloud), or Slack/Teams webhook URLs
```

**Flagsmith (local)**:
```bash
docker run -d --name flagsmith -p 8001:8000 flagsmith/flagsmith:latest
# UI: http://localhost:8001  —  create org/project, then Settings > API Keys
```

---

## Docker Compose Infrastructure Stack

Bring everything up at once with a single compose file.

```bash
# docker-compose.infra.yml at the project root
```

```yaml
version: "3.8"
services:
  # Secrets
  vault:
    image: hashicorp/vault
    ports: ["8200:8200"]
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: dev-token
    cap_add: [IPC_LOCK]

  # Quality Gate
  sonarqube:
    image: sonarqube:community
    ports: ["9000:9000"]
    environment:
      SONAR_ES_BOOTSTRAP_CHECKS_DISABLE: "true"

  # Database
  postgres:
    image: postgres:16
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app

  # Docker Registry
  registry:
    image: registry:2
    ports: ["5000:5000"]

  # Monitoring
  prometheus:
    image: prom/prometheus
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports: ["3001:3000"]
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin

  # Notifications
  ntfy:
    image: binwiederhier/ntfy
    ports: ["8080:80"]
    command: serve

  # Feature Flags
  flagsmith:
    image: flagsmith/flagsmith:latest
    ports: ["8001:8000"]

  # Task Manager microservice (DeepHarness)
  task-manager:
    build: ./services/task-manager
    ports: ["8100:8100"]
```

```bash
docker compose -f docker-compose.infra.yml up -d
docker compose -f docker-compose.infra.yml ps
docker compose -f docker-compose.infra.yml down
```

### Services once the stack is up

| Service | URL | Credentials |
|---------|-----|-------------|
| DeepHarness (frontend) | http://localhost:3000 | — |
| DeepHarness (backend) | http://localhost:8000 | — |
| Vault | http://localhost:8200 | Token: dev-token |
| SonarQube | http://localhost:9000 | admin / admin |
| PostgreSQL | localhost:5432 | app / app |
| Docker Registry | http://localhost:5000 | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3001 | admin / admin |
| Ntfy | http://localhost:8080 | — |
| Flagsmith | http://localhost:8001 | Create in UI |
| Task Manager | http://localhost:8100 | — |

---

## Directory Structure

```
deepharness/
├── backend/
│   ├── server.py                # FastAPI + SSE streaming
│   ├── agent.py                 # Deep Agent factory (cached per persona)
│   ├── tools.py                 # Agent-facing tools
│   ├── sensors.py               # Feedback sensors + SDD + steering loop
│   ├── template_loader.py       # Loads project types / personas / skills
│   ├── project_types/           # Constitutions (immutable)
│   │   ├── web_app_jhipster/
│   │   ├── ai_agent/
│   │   ├── microservice/
│   │   ├── mobile_app/
│   │   ├── cli_tool/
│   │   ├── library/
│   │   └── custom/
│   ├── personas/                # Role directives + required/recommended skills
│   │   ├── architect/
│   │   ├── product_owner/
│   │   ├── developer/
│   │   ├── qa_engineer/
│   │   ├── devops/
│   │   └── deepagent_generator/
│   ├── skills/                  # Composable skills library (SKILL.md + scripts)
│   │   ├── frontend/
│   │   ├── backend/
│   │   ├── methodology/
│   │   ├── testing/
│   │   ├── architecture/
│   │   ├── devops/
│   │   ├── mobile/
│   │   └── database/
│   ├── integrations/            # Decoupled SDLC integrations
│   │   ├── base.py              # IntegrationBase interface
│   │   ├── config.py            # integrations.json loader
│   │   ├── registry.py          # Central registry
│   │   ├── tools.py             # Meta-tools (configure, deploy, status)
│   │   └── providers/           # 16 providers
│   │       ├── gitlab.py
│   │       ├── docker.py
│   │       ├── task_manager.py
│   │       ├── azdevops.py
│   │       ├── playwright_e2e.py
│   │       ├── k3s.py
│   │       ├── k8s.py
│   │       ├── sonarqube.py
│   │       ├── cicd_pipeline.py
│   │       ├── notifications.py
│   │       ├── monitoring.py
│   │       ├── vault.py
│   │       ├── flyway.py
│   │       ├── registry.py
│   │       ├── semgrep_sast.py
│   │       └── flagsmith_flags.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Layout: Chat + Mission Control + Integrations
│   │   ├── lib/useChat.ts       # SSE hook with full activity log
│   │   └── components/
│   │       ├── ChatPanel.tsx
│   │       ├── ActivityPanel.tsx       # Mission Control timeline
│   │       ├── ProjectExplorer.tsx     # File browser
│   │       ├── PersonaSelector.tsx
│   │       ├── ProjectTypeSelector.tsx
│   │       └── Header.tsx              # Deploy button
│   └── package.json
├── services/
│   └── task-manager/            # Task Manager microservice
├── output/                      # Generated projects (gitignored)
└── README.md
```

---

## Harness Engineering Coverage

DeepHarness implements the concepts from Birgitta Böckeler's [Harness Engineering for Coding Agent Users](https://martinfowler.com/articles/harness-engineering.html) (martinfowler.com). Full transparency on what is **implemented**, **partial**, and **missing**:

### Overall Coverage

```
██████████████████████████████████████████████ 74% Implemented (37/50)
██████ 6% Partial (3/50)
████████████ 20% Missing (10/50)
```

### Implemented (37 concepts)

#### Feedforward (Guides)
| Concept | Implementation |
|---------|----------------|
| AGENTS.md | `read_agents_md` / `update_agents_md` |
| Skills | 27 skills across 8 categories |
| Bootstrap scripts | `generate_agent_code` scaffolds complete projects |
| Architecture documentation | Architect persona with `sdd_writer`, `system_design`, `adr_writer` |
| API documentation skills | `spring_boot_api`, `api_integration`, `fastapi_service` |
| How-to guides | Skills are practical guides with runnable code |

#### Feedback (Sensors)
| Concept | Implementation |
|---------|----------------|
| Code review (LLM-based) | `review_code` tool + `code_reviewer` subagent |
| Linter | `run_linter` (Python / TS / Java / MD) |
| Architecture review | `validate_structure` + `check_directives` |
| Dead code detection | `scan_drift` (unused imports, empty files, temp files) |
| Security patterns | `check_directives` (hardcoded secrets, SQL injection) |
| SAST | `security_scan` via Semgrep |

#### Computational Controls
| Concept | Implementation |
|---------|----------------|
| Linters | `run_linter` + Semgrep |
| Pre-commit hooks | `validate_before_write` (keep quality left) |
| Type checkers | Partial (linter flags `: any` in TS) |

#### Inferential Controls
| Concept | Implementation |
|---------|----------------|
| LLM as judge | `review_code` |
| Semantic analysis | `code_reviewer` subagent |

#### Regulation Dimensions
| Concept | Implementation |
|---------|----------------|
| Maintainability harness | Linter + directives + drift scan |
| Architecture fitness | `validate_structure` + enforced project structure |

#### Patterns
| Concept | Implementation |
|---------|----------------|
| Fitness functions | `validate_structure` + `check_directives` |
| Harness templates | 6 personas × 7 project types |
| Custom linters (positive prompt injection) | Lint output includes `FIX:` instructions for the agent |
| Cybernetic governor | Full loop: guides → action → sensors → correction |
| Janitor army (drift) | `scan_drift` |
| Pre-push hooks | `validate_before_write` |
| Blueprints (workflow) | SDD workflow embedded in prompt |

#### Lifecycle
| Concept | Implementation |
|---------|----------------|
| Pre-commit fast controls | `validate_before_write` |
| Post-write checks | Linter + directives after write |
| Continuous drift monitoring | `scan_drift` |

#### Failure Modes Covered
| Concept | Implementation |
|---------|----------------|
| Architectural drift | `validate_structure` |
| Style violations | `run_linter` |
| Brute-force fixes | `code_reviewer` subagent |
| Dead code | `scan_drift` |

#### Evaluation
| Concept | Implementation |
|---------|----------------|
| Keep quality left | Pre-write validation |
| Sensor metrics | `GET /api/harness/metrics` (pass rate, sensor usage) |
| Harness coherence | Directives and sensors kept in lockstep |

#### Steering and SDD
| Concept | Implementation |
|---------|----------------|
| Human iterates on harness | `harness.md` per-project custom rules |
| Use AI to build the harness | Agent creates skills, SDDs, rules |
| Plan before code | `create_sdd` with complexity assessment (simple / medium / complex) |
| Task breakdown | `write_todos` + Task Manager Board (microservice) |

#### Visibility
| Concept | Implementation |
|---------|----------------|
| Mission Control | Real-time timeline (chat + sensors + integrations) |

---

### Partial (3 concepts)

| Concept | What we have | What's missing |
|---------|--------------|----------------|
| **Full Semgrep coverage** | Exposed tool, basic scan | Enterprise ruleset (full OWASP, custom rules) |
| **Behaviour harness** | SDD + Playwright + tests | Automatic validation of expected behavior vs SDD |
| **Dependency scanning** | — | Dependabot-equivalent |

---

### Missing (10 concepts)

| Concept | Why it's missing | Difficulty to add |
|---------|------------------|-------------------|
| **OpenRewrite (codemods)** | AST-based automatic refactoring | High — Java/AST tooling |
| **LSP integration** | Language servers (autocomplete, hover) | High — IDE plugin required |
| **Coverage monitoring** | Real numbers from `npm run coverage`, jacoco | Medium — subprocess execution |
| **Mutation testing** | PIT, Stryker — generates mutants to test tests | High — complex frameworks |
| **Test coverage quality** | Analyzes whether tests cover meaningful cases | High — semantic analysis |
| **Cyclomatic complexity** | Per-function complexity metric | Low — easy to add |
| **Approved fixtures pattern** | Approved snapshots of expected behavior | Medium |
| **SLO monitoring (runtime)** | Real SLO checks on running services | Medium — Prometheus wired, queries missing |
| **Log anomaly detection** | Detect anomalous log patterns | High — ML / heuristics |
| **Response quality sampling** | Sample outputs and rate their quality | High |

---

### Honest Conclusion

**The harness is functional for local development** with 74% of the concepts from Böckeler's article covered. The remaining 26% breaks down as:

- **Heavy external tooling** (OpenRewrite, LSP, mutation testing) — heavy dependencies with limited value for prototyping
- **Real runtime/production** (SLO monitoring, log anomaly) — require real services running 24/7
- **Advanced metrics** (coverage quality, complexity) — easy to add but low immediate ROI

For serious enterprise adoption, the Partial and Missing items should be prioritized in this order:

1. **P0** — Real coverage monitoring + cyclomatic complexity (easy, high ROI)
2. **P1** — Full behaviour harness (SDD vs behavior validation)
3. **P2** — Dependency scanning + real SLO monitoring
4. **P3** — Mutation testing, OpenRewrite, LSP (nice to have)

---

## Stats

- **6** engineering personas
- **7** project types (constitutions)
- **27** composable skills across 8 categories
- **16** integration providers (including the Task Manager microservice)
- **85+** integration tools
- **11** feedback sensors
- **7** SDLC phases covered (Plan, Develop, Review, Test, Build, Deploy, Monitor)
- **3** deploy environments (local, staging, production)

---

## License

MIT
