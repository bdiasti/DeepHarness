# Constitution — Microservice

IMMUTABLE rules for microservices.

## Architecture (FIXED)
1. MUST follow Clean Architecture: api/application/domain/infrastructure layers.
2. Domain MUST be independent of frameworks (no Spring in domain/).
3. Dependency direction MUST be inward (infrastructure → application → domain).
4. Communication with other services MUST use DTOs, never entities.

## Observability (NON-NEGOTIABLE)
5. Every service MUST expose `/actuator/health`, `/actuator/metrics`, `/actuator/prometheus`.
6. Structured logging MUST be JSON (no plain text logs).
7. OpenTelemetry tracing MUST be enabled.
8. SLOs MUST be defined: latency p99 < 500ms, error rate < 0.1%.

## Containerization (FIXED)
9. MUST have a multi-stage Dockerfile.
10. Container MUST run as non-root user.
11. Image MUST be tagged with git SHA, not `latest`.
12. MUST include K8s manifests (deployment, service, ingress).

## Resilience
13. External calls MUST have timeouts (default 5s).
14. Circuit breakers MUST protect external dependencies (Resilience4j).
15. Retries MUST be configured with exponential backoff.
16. Graceful shutdown MUST drain connections.

## What's NOT allowed
- Do NOT put business logic in controllers.
- Do NOT access DB directly from domain layer.
- Do NOT expose internal implementation via REST.
- Do NOT run as root in container.
