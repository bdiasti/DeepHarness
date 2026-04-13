"""
Deploy Manager — Checks and generates artifacts required for deploy.

Deploy targets:
- docker: just Dockerfile
- docker_compose: Dockerfile + docker-compose.yml
- k3s: Dockerfile + k8s/ manifests (+ optionally docker-compose for build)
- gitlab: .gitlab-ci.yml (+ Dockerfile for build jobs)
"""

import os
import subprocess
from typing import Optional
from tools import OUTPUT_DIR


DEPLOY_TARGETS = {
    "docker": {
        "name": "Docker Local",
        "description": "Build and run a single container locally",
        "icon": "container",
        "color": "#2496ED",
        "required_artifacts": ["Dockerfile"],
    },
    "docker_compose": {
        "name": "Docker Compose",
        "description": "Multi-container local deploy with docker-compose",
        "icon": "container",
        "color": "#2496ED",
        "required_artifacts": ["Dockerfile", "docker-compose.yml"],
    },
    "k3s": {
        "name": "K3s (Local Cluster)",
        "description": "Deploy to a local Kubernetes cluster via K3s",
        "icon": "rocket",
        "color": "#FFC61C",
        "required_artifacts": ["Dockerfile", "k8s/deployment.yaml", "k8s/service.yaml"],
    },
    "gitlab_push": {
        "name": "GitLab CI/CD Push",
        "description": "Push to GitLab — pipeline handles build+deploy",
        "icon": "git-branch",
        "color": "#FC6D26",
        "required_artifacts": ["Dockerfile", ".gitlab-ci.yml"],
    },
}


def check_project_artifacts(project_name: str) -> dict:
    """Check what artifacts exist in a project."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return {"error": "Project not found"}

    all_artifacts = set()
    for target_info in DEPLOY_TARGETS.values():
        all_artifacts.update(target_info["required_artifacts"])

    status = {}
    for artifact in all_artifacts:
        filepath = os.path.join(project_dir, artifact)
        status[artifact] = {
            "path": artifact,
            "exists": os.path.isfile(filepath),
            "size": os.path.getsize(filepath) if os.path.isfile(filepath) else 0,
        }

    # Per-target readiness
    targets_status = {}
    for target_id, target_info in DEPLOY_TARGETS.items():
        missing = [a for a in target_info["required_artifacts"] if not status[a]["exists"]]
        targets_status[target_id] = {
            **target_info,
            "id": target_id,
            "ready": len(missing) == 0,
            "missing": missing,
            "present": [a for a in target_info["required_artifacts"] if status[a]["exists"]],
        }

    return {
        "project": project_name,
        "artifacts": status,
        "targets": targets_status,
    }


# ═══════════════════════════════════════════
# Artifact Generators
# ═══════════════════════════════════════════

def detect_project_stack(project_name: str) -> str:
    """Detect what kind of project this is (python, node, java, etc.)."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)

    if os.path.isfile(os.path.join(project_dir, "requirements.txt")) or \
       os.path.isfile(os.path.join(project_dir, "pyproject.toml")):
        return "python"
    if os.path.isfile(os.path.join(project_dir, "pom.xml")):
        return "java_maven"
    if os.path.isfile(os.path.join(project_dir, "build.gradle")) or \
       os.path.isfile(os.path.join(project_dir, "build.gradle.kts")):
        return "java_gradle"
    if os.path.isfile(os.path.join(project_dir, "package.json")):
        return "node"
    if os.path.isfile(os.path.join(project_dir, "go.mod")):
        return "go"
    if os.path.isfile(os.path.join(project_dir, "Cargo.toml")):
        return "rust"
    return "generic"


def generate_dockerfile(project_name: str) -> str:
    """Generate a Dockerfile based on the detected stack."""
    stack = detect_project_stack(project_name)
    project_dir = os.path.join(OUTPUT_DIR, project_name)

    templates = {
        "python": """FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
        "node": """FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
# Use npm ci if package-lock exists, otherwise npm install
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY . .
RUN npm run build 2>/dev/null || true

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app .
EXPOSE 3000
CMD ["npm", "start"]
""",
        "java_maven": """FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
EXPOSE 8080
USER 1000
CMD ["java", "-jar", "app.jar"]
""",
        "java_gradle": """FROM gradle:8-jdk21 AS builder
WORKDIR /app
COPY . .
RUN gradle build --no-daemon

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /app/build/libs/*.jar app.jar
EXPOSE 8080
USER 1000
CMD ["java", "-jar", "app.jar"]
""",
        "go": """FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /app/bin/app ./cmd/...

FROM alpine:3.19
WORKDIR /app
COPY --from=builder /app/bin/app .
EXPOSE 8080
USER 1000
CMD ["./app"]
""",
        "generic": """# TODO: customize for your stack
FROM alpine:3.19
WORKDIR /app
COPY . .
EXPOSE 8080
CMD ["sh", "-c", "echo 'Configure your CMD'"]
""",
    }

    content = templates.get(stack, templates["generic"])
    filepath = os.path.join(project_dir, "Dockerfile")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Generated Dockerfile for stack={stack}"


def generate_docker_compose(project_name: str) -> str:
    """Generate a docker-compose.yml."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    safe_name = project_name.replace("_", "-").lower()

    content = f"""services:
  app:
    build: .
    container_name: {safe_name}
    ports:
      - "8080:8080"
    environment:
      - APP_ENV=local
    restart: unless-stopped
    # depends_on:
    #   - db

  # Uncomment if you need a database:
  # db:
  #   image: postgres:16
  #   environment:
  #     POSTGRES_DB: app
  #     POSTGRES_USER: app
  #     POSTGRES_PASSWORD: app
  #   ports:
  #     - "5432:5432"
  #   volumes:
  #     - db_data:/var/lib/postgresql/data

# volumes:
#   db_data:
"""
    filepath = os.path.join(project_dir, "docker-compose.yml")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return "Generated docker-compose.yml"


def generate_gitlab_ci(project_name: str) -> str:
    """Generate .gitlab-ci.yml."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    stack = detect_project_stack(project_name)

    test_cmd = {
        "python": "pip install -r requirements.txt && pytest",
        "node": "npm ci && npm test",
        "java_maven": "mvn test",
        "java_gradle": "gradle test",
        "go": "go test ./...",
    }.get(stack, "echo 'No tests configured'")

    content = f"""stages:
  - build
  - test
  - quality
  - deploy_staging
  - deploy_production

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build -t $DOCKER_IMAGE .
    - docker push $DOCKER_IMAGE
  only:
    - main
    - develop
    - merge_requests

test:
  stage: test
  script:
    - {test_cmd}

quality:
  stage: quality
  image: sonarsource/sonar-scanner-cli
  script:
    - sonar-scanner
  only:
    - main
  allow_failure: true

deploy_staging:
  stage: deploy_staging
  image: bitnami/kubectl
  script:
    - kubectl apply -f k8s/ -n staging
    - kubectl rollout status deployment/{project_name} -n staging
  environment:
    name: staging
  only:
    - develop

deploy_production:
  stage: deploy_production
  image: bitnami/kubectl
  script:
    - kubectl apply -f k8s/ -n production
    - kubectl rollout status deployment/{project_name} -n production
  environment:
    name: production
  only:
    - main
  when: manual
"""
    filepath = os.path.join(project_dir, ".gitlab-ci.yml")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return "Generated .gitlab-ci.yml"


def generate_k8s_manifests(project_name: str) -> str:
    """Generate k8s/deployment.yaml and k8s/service.yaml."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    k8s_dir = os.path.join(project_dir, "k8s")
    os.makedirs(k8s_dir, exist_ok=True)
    safe_name = project_name.replace("_", "-").lower()

    deployment = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {safe_name}
  labels:
    app: {safe_name}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {safe_name}
  template:
    metadata:
      labels:
        app: {safe_name}
    spec:
      containers:
      - name: {safe_name}
        image: localhost:5000/{safe_name}:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
"""

    service = f"""apiVersion: v1
kind: Service
metadata:
  name: {safe_name}
spec:
  selector:
    app: {safe_name}
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
"""

    with open(os.path.join(k8s_dir, "deployment.yaml"), "w", encoding="utf-8") as f:
        f.write(deployment)
    with open(os.path.join(k8s_dir, "service.yaml"), "w", encoding="utf-8") as f:
        f.write(service)

    return "Generated k8s/deployment.yaml and k8s/service.yaml"


ARTIFACT_GENERATORS = {
    "Dockerfile": generate_dockerfile,
    "docker-compose.yml": generate_docker_compose,
    ".gitlab-ci.yml": generate_gitlab_ci,
    "k8s/deployment.yaml": generate_k8s_manifests,
    "k8s/service.yaml": generate_k8s_manifests,
}


def generate_artifact(project_name: str, artifact: str) -> dict:
    """Generate a specific artifact."""
    generator = ARTIFACT_GENERATORS.get(artifact)
    if not generator:
        return {"error": f"Unknown artifact: {artifact}"}

    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return {"error": "Project not found"}

    try:
        result = generator(project_name)
        return {"status": "ok", "message": result}
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════
# Deploy Executors
# ═══════════════════════════════════════════

def _run(cmd: list, cwd: str) -> dict:
    """Run a command and capture output."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=180)
        return {
            "code": r.returncode,
            "stdout": r.stdout[-2000:],
            "stderr": r.stderr[-2000:],
            "success": r.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"code": -1, "success": False, "stderr": "Timeout after 180s"}
    except FileNotFoundError as e:
        return {"code": -1, "success": False, "stderr": f"Command not found: {e}"}
    except Exception as e:
        return {"code": -1, "success": False, "stderr": str(e)}


def execute_deploy(project_name: str, target: str) -> dict:
    """Execute the actual deploy."""
    project_dir = os.path.join(OUTPUT_DIR, project_name)
    if not os.path.isdir(project_dir):
        return {"error": "Project not found"}

    safe_name = project_name.replace("_", "-").lower()

    if target == "docker":
        build = _run(["docker", "build", "-t", f"{safe_name}:latest", "."], project_dir)
        if not build.get("success"):
            return {"target": target, "step": "build", **build}
        # Stop any previous
        _run(["docker", "rm", "-f", safe_name], project_dir)
        run = _run([
            "docker", "run", "-d",
            "--name", safe_name,
            "-p", "8080:8080",
            f"{safe_name}:latest",
        ], project_dir)
        return {"target": target, "step": "run", **run}

    elif target == "docker_compose":
        r = _run(["docker", "compose", "up", "-d", "--build"], project_dir)
        return {"target": target, **r}

    elif target == "k3s":
        build = _run(["docker", "build", "-t", f"localhost:5000/{safe_name}:latest", "."], project_dir)
        if not build.get("success"):
            return {"target": target, "step": "build", **build}
        push = _run(["docker", "push", f"localhost:5000/{safe_name}:latest"], project_dir)
        if not push.get("success"):
            return {"target": target, "step": "push", **push}
        apply = _run(["kubectl", "apply", "-f", "k8s/"], project_dir)
        return {"target": target, "step": "apply", **apply}

    elif target == "gitlab_push":
        # Make sure git is initialized
        if not os.path.isdir(os.path.join(project_dir, ".git")):
            _run(["git", "init"], project_dir)
        add = _run(["git", "add", "-A"], project_dir)
        commit = _run(["git", "commit", "-m", f"Deploy: {safe_name}"], project_dir)
        push = _run(["git", "push"], project_dir)
        return {"target": target, "step": "push", "add": add, "commit": commit, "push": push}

    return {"error": f"Unknown target: {target}"}
