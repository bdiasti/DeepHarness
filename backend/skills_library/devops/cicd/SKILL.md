---
name: cicd
description: CI/CD pipelines — stages (build, test, quality, deploy), GitLab CI / GitHub Actions
---

# CI/CD Pipelines

Automate build, verify, and deploy to ship safely and fast.

## Canonical Stages

1. **Build** — compile, package, build container image
2. **Test** — unit, integration, e2e
3. **Quality** — lint, format check, type check, SAST, dependency scan, coverage gate
4. **Package/Publish** — push artifact/image with immutable tag (git SHA)
5. **Deploy** — staging (auto) then production (manual approval or progressive)

## GitHub Actions Example

```yaml
name: ci
on:
  push: { branches: [main] }
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci
      - run: npm run lint
      - run: npm test -- --coverage
      - uses: codecov/codecov-action@v4

  build:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## GitLab CI Example

```yaml
stages: [test, build, deploy]

test:
  stage: test
  image: node:20
  cache: { key: $CI_COMMIT_REF_SLUG, paths: [node_modules/] }
  script:
    - npm ci
    - npm run lint
    - npm test -- --coverage
  coverage: '/Lines\s*:\s*(\d+\.\d+)%/'

build:
  stage: build
  image: docker:24
  services: [docker:24-dind]
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only: [main]

deploy:prod:
  stage: deploy
  script: ./scripts/deploy.sh $CI_COMMIT_SHA
  environment: production
  when: manual
  only: [main]
```

## Best Practices

- **Fail fast**: run lint/unit before slower e2e
- **Cache** dependencies (npm, pip, maven, docker layers)
- **Parallelize** independent jobs; shard test suites
- **Immutable artifacts**: tag by git SHA, promote same artifact across envs
- **Secrets**: use provider vault (GitHub Secrets, GitLab Variables masked/protected), never commit
- **Branch protection**: required checks + code review before merge
- **Trunk-based** with short-lived feature branches
- Progressive delivery: canary/blue-green; auto-rollback on SLO breach
- Pipeline-as-code reviewed like app code; pin action versions (SHAs)
