"""Formatadores text e JSON (observabilidade / Cloud Logging)."""

from __future__ import annotations

import json
import logging
import os
import traceback
from datetime import UTC, datetime
from typing import Any

from mqtt_chat.logging.filters import redact_mapping, redact_text


class JsonLogFormatter(logging.Formatter):
    """
    Emite uma linha JSON por registro (ndjson).

    Campos alinhados a docs/logging.md e OTel Logs (severity, attributes, event).
    """

    def __init__(self, service_name: str = "mqtt-chat") -> None:
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC)
            .isoformat()
            .replace("+00:00", "Z"),
            "severity": record.levelname,
            "logger": record.name,
            "message": redact_text(record.getMessage()),
            "service": {"name": self._service_name},
            "code": {
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "file": os.path.basename(record.pathname),
            },
        }

        event = getattr(record, "event", None)
        if event:
            payload["event"] = event

        attributes = getattr(record, "attributes", None)
        if isinstance(attributes, dict) and attributes:
            payload["attributes"] = redact_mapping(attributes)

        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            payload["exception"] = {
                "type": exc_type.__name__ if exc_type else None,
                "message": redact_text(str(exc_value)) if exc_value else None,
                "stacktrace": redact_text(
                    "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
                ),
            }

        return json.dumps(payload, ensure_ascii=False, default=str)


class TextLogFormatter(logging.Formatter):
    """Formato legível para dev local (`LOG_FORMAT=text`)."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
