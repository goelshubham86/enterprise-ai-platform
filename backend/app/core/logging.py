"""
Structured logging configuration for the Enterprise AI Platform.

Outputs JSON-formatted log records so Google Cloud Logging can index
individual fields (document_id, elapsed_ms, stage) for alerting and dashboards.

Usage:
    from app.core.logging import configure_logging, get_logger

    configure_logging(level="INFO")          # call once in main.py lifespan
    logger = get_logger(__name__)            # in every module

    logger.info(
        "Stage complete",
        extra={
            "document_id": "abc-123",
            "stage": "chunking",
            "chunk_count": 42,
            "elapsed_ms": 150.3,
        },
    )

Cloud Logging integration:
    The JSON keys map directly to Cloud Logging's structured payload.
    When deployed to Cloud Run, stdout JSON is auto-parsed.
    The `severity` key overrides the default `textPayload` severity label.
    The `logging.googleapis.com/sourceLocation` key provides file/line context.
"""

from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any


# ─── JSON Formatter ───────────────────────────────────────────────────────────


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects.

    Cloud Logging severity labels differ from Python's levelname strings,
    so we map them explicitly.
    """

    _SEVERITY_MAP: dict[int, str] = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "severity": self._SEVERITY_MAP.get(record.levelno, "DEFAULT"),
            "logger": record.name,
            "message": record.getMessage(),
            "logging.googleapis.com/sourceLocation": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            },
        }

        # Attach any extra fields the caller passed via extra={...}
        standard_attrs = logging.LogRecord.__dict__.keys() | {
            "message",
            "asctime",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "name",
            "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        elif record.exc_text:
            payload["exception"] = record.exc_text

        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(payload, default=str)


# ─── Plain text formatter (local dev readability) ─────────────────────────────


class DevFormatter(logging.Formatter):
    """Human-readable formatter for local development.

    Outputs: 2024-01-15T10:23:45Z [INFO] app.services.pdf: message | key=val
    Extra fields are appended as key=value pairs for quick scanning.
    """

    _LEVEL_COLORS: dict[str, str] = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%H:%M:%S")
        level = record.levelname
        color = self._LEVEL_COLORS.get(level, "")

        parts = [f"{ts} {color}[{level:8s}]{self._RESET} {record.name}: {record.getMessage()}"]

        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in standard_attrs and not k.startswith("_")
        }
        if extras:
            parts.append(" | " + " ".join(f"{k}={v}" for k, v in extras.items()))

        line = "".join(parts)

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)

        return line


# ─── Public API ───────────────────────────────────────────────────────────────


def configure_logging(level: str = "INFO", *, use_json: bool | None = None) -> None:
    """Configure the root logger for the application.

    Call exactly once at application startup (in main.py lifespan).

    Args:
        level: Log level string ("DEBUG", "INFO", "WARNING", "ERROR").
        use_json: Force JSON or plain-text output. Defaults to JSON when
                  APP_ENV != "development" so Cloud Run gets structured logs
                  and local dev gets readable output.
    """
    from app.core.config import settings

    if use_json is None:
        use_json = settings.app_env != "development"

    formatter: logging.Formatter = JsonFormatter() if use_json else DevFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure the root logger; all child loggers inherit this.
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Remove any handlers added by uvicorn or earlier imports.
    root.handlers.clear()
    root.addHandler(handler)

    # Suppress noisy third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.

    Thin wrapper around logging.getLogger() — exists so all modules
    import from the same place, making it easy to swap the logging
    backend (e.g. structlog) in future without changing every file.
    """
    return logging.getLogger(name)
