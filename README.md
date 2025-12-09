# Central Logging System

A reusable Python exception wrapper that catches all exceptions and sends them to Grafana Cloud via OpenTelemetry (OTLP).

## Project Structure

```
├── app.py                 # Main application with OTel configuration
├── exception_wrapper.py   # Reusable exception handler (copy to any project)
└── requirements.txt       # Dependencies
```

## How It Works

1. **app.py** - Configures OpenTelemetry to send logs to Grafana Cloud
2. **exception_wrapper.py** - Catches all exceptions globally and routes them through the logger

### Exception Wrapper Features
- `install_global_exception_handlers()` - Catches uncaught exceptions in main thread and all threads
- `run_with_exception_logging(func)` - Wraps a function to log any exception it throws
- `@exception_safe` - Decorator version of the above

## Setup

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

In `app.py`, update the Grafana Cloud credentials:

```python
exporter = OTLPLogExporter(
    endpoint="https://otlp-gateway-prod-gb-south-1.grafana.net/otlp",
    headers={
        "Authorization": "Basic <your-token-from-grafana>",
    },
)
```

## Run

```cmd
python app.py
```

This triggers a division-by-zero exception which gets logged to console and sent to Grafana Cloud.

## Reusing the Wrapper

Copy `exception_wrapper.py` to any Python project. Then:

```python
from exception_wrapper import install_global_exception_handlers, run_with_exception_logging

# At startup - catches all uncaught exceptions
install_global_exception_handlers(logger=your_logger)

# Wrap specific functions
run_with_exception_logging(your_function, rethrow=False)
```
