# Directives — DevOps / SRE

These rules are IMMUTABLE and must NEVER be violated.

## Infrastructure
1. All infrastructure MUST be defined as code (Terraform, Pulumi, or CloudFormation).
2. Every service MUST have health checks (liveness + readiness probes in K8s).
3. Resource limits (CPU, memory) MUST be defined for all containers.
4. NEVER run containers as root — always use non-root users.

## CI/CD
5. Every PR MUST pass tests + lint + security scan before merge.
6. Production deploys MUST require manual approval.
7. Rollback procedures MUST be documented and tested.
8. Deploy pipelines MUST include smoke tests post-deployment.

## Secrets & Security
9. NEVER commit secrets to git — use Vault, Key Vault, or Secrets Manager.
10. All secrets MUST be rotated on a schedule.
11. Network policies MUST follow least-privilege principle.
12. TLS MUST be enforced on all external endpoints.

## Observability
13. Every service MUST emit structured logs (JSON).
14. Every service MUST expose metrics (Prometheus format).
15. Distributed tracing MUST be enabled for all services.
16. Alert rules MUST have runbook links.
17. SLOs MUST be defined for user-facing services.

## Kubernetes
18. Namespaces MUST be used to isolate environments.
19. RBAC MUST follow least-privilege — no cluster-admin in apps.
20. Pod Security Standards MUST be enforced.
21. Image pull policy MUST use digests (not latest) in production.
