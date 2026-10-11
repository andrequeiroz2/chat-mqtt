"""Configuração central do root logger (único ponto de setup)."""

from __future__ import annotations

import logging
import sys
from typing import Literal

from mqtt_chat.logging.filters import SecretRedactionFilter
from mqtt_chat.logging.formatters import JsonLogFormatter, TextLogFormatter

LogFormat = Literal["json", "text"]


def setup_logging(
    *,
    level: str = "INFO",
    log_format: LogFormat = "json",
    service_name: str = "mqtt-chat",
) -> None:
    """
    Configura logging do processo (worker, API, MCP futuro).

    Deve ser chamado uma vez no entrypoint, antes de outros loggers emitirem.
    """
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(SecretRedactionFilter())

    if log_format == "json":
        handler.setFormatter(JsonLogFormatter(service_name=service_name))
    else:
        handler.setFormatter(TextLogFormatter())

    root.addHandler(handler)

    # Reduz ruído de bibliotecas HTTP/gRPC em INFO
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("grpc").setLevel(logging.WARNING)
