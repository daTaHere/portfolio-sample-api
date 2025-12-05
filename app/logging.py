import structlog

"""
Logging configuration for the application using structlog for structured logging.
Sets up a logger with JSON output format and various processors for enhanced log information.
Logs include timestamps, log levels, and exception information.
Logging centered around structured events for better traceability and analysis.

To use the logger in other modules, import it from this file:
from app.logging import logger
"""

logger = structlog.get_logger()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
