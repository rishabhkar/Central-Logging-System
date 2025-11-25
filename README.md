# Central Logging System (Python + OpenTelemetry + Grafana)

This repo is intentionally minimal. Per request, it only includes:
- `.gitignore`
- `.gitattributes`
- `README.md` (this file)

Below is a tiny, self-contained Python example you can copy into your own `main.py` to try OpenTelemetry logs and see them in Grafana/Loki (or any OTLP-compatible backend).

## Prerequisites
- Python 3.10+
- An OTLP endpoint to receive logs (for example: an OpenTelemetry Collector that forwards to Grafana Loki, Grafana Cloud OTLP, or another OTLP-compatible backend).

## Quick start (local test)

1) Create and activate a virtual environment, then install OpenTelemetry packages:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install opentelemetry-sdk opentelemetry-api opentelemetry-exporter-otlp-proto-http opentelemetry-instrumentation-logging
```

2) Create a file named `main.py` with the following content:

```text
import logging
import os
import random
import sys
import time
from datetime import datetime

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

SERVICE_NAME = os.getenv("SERVICE_NAME", "python-otel-logging-demo")
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://localhost:4318")  # change to your collector or Grafana Cloud OTLP endpoint

# Configure tracing (optional, helps correlate logs/spans)
resource = Resource.create({"service.name": SERVICE_NAME})
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{OTLP_ENDPOINT}/v1/traces"))
)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

# Configure logging provider with OTLP exporter
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{OTLP_ENDPOINT}/v1/logs"))
)

otel_handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

# Stdout + OTel handlers
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
console = logging.StreamHandler(stream=sys.stdout)
console.setLevel(logging.DEBUG)
console.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] trace_id=%(otelTraceID)s span_id=%(otelSpanID)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
)
root_logger.addHandler(console)
root_logger.addHandler(otel_handler)

log = logging.getLogger("demo.app")


def emit_some_logs():
    # Create a span so logs can be correlated
    with tracer.start_as_current_span("simulate_work"):
        log.info("Starting work")
        time.sleep(0.2)
        for i in range(5):
            level = random.choice([logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR])
            if level == logging.DEBUG:
                log.debug("Step %d completed", i, extra={"user_id": i})
            elif level == logging.INFO:
                log.info("Processing event", extra={"event": f"evt-{i}"})
            elif level == logging.WARNING:
                log.warning("Slow response detected", extra={"latency_ms": random.randint(100, 800)})
            else:
                try:
                    raise ValueError("Uh oh something went wrong")
                except Exception as exc:
                    log.exception("Handled error: %s", exc)
        log.info("Work finished", extra={"finished_at": datetime.utcnow().isoformat()})


if __name__ == "__main__":
    while True:
        emit_some_logs()
        time.sleep(2)
```

3) Set your OTLP endpoint and run the demo. For a local OpenTelemetry Collector listening on default OTLP/HTTP port 4318:

```cmd
set OTLP_ENDPOINT=http://localhost:4318
set SERVICE_NAME=python-otel-logging-demo
python main.py
```

If your backend requires auth (e.g., Grafana Cloud OTLP), consult that provider's docs for the correct endpoint and headers. For Grafana Cloud, you typically send OTLP to a URL like `https://<stack-id>.grafana.net/otlp`, with basic auth using your instance ID and API token.

## Viewing logs in Grafana/Loki
- If you already have Grafana + Loki wired to your OpenTelemetry Collector, open Grafana Explore and query by label (for example, `{service_name="python-otel-logging-demo"}`) or by text search.
- To correlate logs with traces, include `trace_id` in your log line format (as shown). If you're also exporting traces to a system like Tempo, you can add a derived field in Grafana to link logs to traces.

## Notes
- This README keeps the repository clean. It doesn't add Docker, Collector, or Grafana configuration files. If you'd like me to scaffold those later, say the word and I'll add them in a separate PR/commit.
