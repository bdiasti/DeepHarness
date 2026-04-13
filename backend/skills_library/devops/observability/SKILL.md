---
name: observability
description: Observability — metrics (Prometheus), logs (structured JSON), traces (OpenTelemetry)
---

# Observability

Three pillars: **metrics** (what/how much), **logs** (what happened), **traces** (where time went). Correlate via `trace_id`.

## Metrics (Prometheus)

Golden signals: **latency, traffic, errors, saturation**. Use RED (Rate/Errors/Duration) for services and USE (Utilization/Saturation/Errors) for resources.

```python
from prometheus_client import Counter, Histogram, start_http_server

REQS = Counter("http_requests_total", "HTTP requests", ["method", "route", "status"])
LAT  = Histogram("http_request_duration_seconds", "Latency", ["route"],
                 buckets=(.005,.01,.025,.05,.1,.25,.5,1,2.5,5,10))

@LAT.labels("/orders").time()
def handle():
    REQS.labels("GET", "/orders", "200").inc()

start_http_server(9090)  # /metrics
```

Keep label cardinality low — never use user IDs or URLs with params.

Example alert:

```yaml
- alert: HighErrorRate
  expr: sum(rate(http_requests_total{status=~"5.."}[5m]))
      / sum(rate(http_requests_total[5m])) > 0.02
  for: 10m
  labels: { severity: page }
  annotations: { summary: ">2% 5xx on {{ $labels.service }}" }
```

## Structured Logs (JSON)

One event per line, machine-parseable, include context + trace IDs.

```python
import logging, json, sys
from pythonjsonlogger import jsonlogger

h = logging.StreamHandler(sys.stdout)
h.setFormatter(jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"))
log = logging.getLogger(); log.addHandler(h); log.setLevel(logging.INFO)

log.info("order_created", extra={
    "order_id": "o_123", "user_id": "u_1", "amount": 42.50,
    "trace_id": current_trace_id(),
})
```

Rules: no PII/secrets, include `service`, `env`, `version`, `trace_id`. Use levels consistently (DEBUG/INFO/WARN/ERROR).

## Traces (OpenTelemetry)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="otel-collector:4317")))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("charge_card") as span:
    span.set_attribute("order.id", order_id)
    span.set_attribute("amount", amount)
    try:
        gateway.charge(...)
    except Exception as e:
        span.record_exception(e); span.set_status(trace.StatusCode.ERROR); raise
```

Auto-instrument frameworks (FastAPI, Flask, requests, SQLAlchemy) via `opentelemetry-instrumentation`. Propagate `traceparent` header across services.

## Stack & Practices

- Collector: **OpenTelemetry Collector** (receives OTLP, exports anywhere)
- Backends: Prometheus/Grafana (metrics), Loki/ELK (logs), Jaeger/Tempo (traces); unified: Grafana, Datadog, Honeycomb
- **SLIs/SLOs** drive alerts; page on symptoms, not causes
- Sample traces (e.g., 10%) but keep errors at 100%
- Dashboards per service with RED + saturation + deploy markers
- Always log and tag metrics/spans with `trace_id` so one click correlates all three
