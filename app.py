#OTel Dependencies
import logging

from opentelemetry._logs import set_logger_provider # Function to set the global logger provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (OTLPLogExporter) # OTLP log exporter class from gRPC module
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler # LoggerProvider: Class to create a logger provider; LoggingHandler: Handler to integrate logging with OpenTelemetry
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor # BatchLogRecordProcessor: Class to process log records in batches
from opentelemetry.sdk.resources import Resource # Resource: Class to define resource attributes for telemetry data

# Logger Provider Configuration to identify the source of the logs
logger_provider = LoggerProvider(
    resource=Resource.create(
        {
            "service.name": "central-logging-system",
            "service.instance.id": "instance-1"
        }
    )
)

# Set the created configurations to the global logger provider
set_logger_provider(logger_provider)

# Configure the exporter object with insecure connection settings, insecure: True indicates that the connection does not use TLS encryption
exporter = OTLPLogExporter(insecure=True)

# This line adds a BatchLogRecordProcessor to the logger provider, which processes log records in batches and exports them using the configured OTLPLogExporter.
logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

# Logging handler will route standard logging messages to OpenTelemetry
handler = LoggingHandler(level = logging.NOTSET, logger_provider=logger_provider)

# Integrate the logging handler with the standard logging module
logging.getLogger().addHandler(handler)

# Application Code

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def always_trigger_exception():
    return 1/0

if __name__ == "__main__":
    try:
        always_trigger_exception()
    except Exception as e:
        logger.exception("Deliberate Failure: An exception to check logging functionality. Exception: %s", e)