"""Bootstrap de logging a partir de Settings."""

from __future__ import annotations

from mqtt_chat.config.settings import Settings
from mqtt_chat.logging.setup import setup_logging


def setup_logging_from_settings(settings: Settings) -> None:
    """Aplica LOG_LEVEL, LOG_FORMAT e LOG_SERVICE_NAME do ambiente."""
    setup_logging(
        level=settings.log_level,
        log_format=settings.log_format,
        service_name=settings.log_service_name,
    )
