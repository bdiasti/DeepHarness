---
name: docker
description: Docker best practices — multi-stage builds, caching, security, compose
---

# Docker

Package applications with their runtime into portable, reproducible images.

## Multi-Stage Build (Node example)

```dockerfile
# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build && npm prune --production

FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S app && adduser -S app -G app
COPY --from=build --chown=app:app /app/dist ./dist
COPY --from=build --chown=app:app /app/node_modules ./node_modules
COPY --from=build --chown=app:app /app/package.json ./
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8080/health || exit 1
CMD ["node", "dist/server.js"]
```

## Layer Caching Rules

- Copy **dependency manifests first**, install, then copy source
- Order layers from least-changing to most-changing
- Use BuildKit cache mounts (`--mount=type=cache`)
- Combine related `RUN` steps; clean apt lists in same layer: `rm -rf /var/lib/apt/lists/*`

## Security

- Use minimal base images (`alpine`, `distroless`, `-slim`)
- Pin versions (`node:20.11.1-alpine`), not `latest`
- Run as **non-root** user
- Don't bake secrets into images; use build args only for non-secret config, runtime secrets via env/mounts
- Scan images: `docker scout cves`, Trivy, Snyk
- `.dockerignore` (node_modules, .git, .env, tests) to shrink context and avoid leaks

## docker compose

```yaml
services:
  api:
    build: .
    ports: ["8080:8080"]
    environment:
      DATABASE_URL: postgres://app:app@db:5432/app
    depends_on:
      db: { condition: service_healthy }
    develop:
      watch:
        - { action: sync, path: ./src, target: /app/src }
        - { action: rebuild, path: package.json }
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "app"]
      interval: 5s
volumes: { pgdata: {} }
```

## Handy Commands

```bash
docker build -t app:dev .
docker buildx build --platform linux/amd64,linux/arm64 -t app:1.0 --push .
docker compose up -d --build
docker compose logs -f api
docker system prune -af --volumes       # reclaim space
docker image inspect app:dev --format '{{.Size}}'
```
