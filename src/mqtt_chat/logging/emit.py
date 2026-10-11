"""API de emissão: evento + atributos estruturados."""

from __future__ import annotations

import logging
from typing import Any


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str,
    *,
    exc_info: bool | BaseException | None = None,
    **attributes: Any,
) -> None:
    """
    Registra log estruturado com campo `event` e `attributes`.

    Localização (módulo, função, linha) vem do LogRecord automático.
    """
    extra: dict[str, Any] = {"event": event}
    if attributes:
        extra["attributes"] = attributes
    logger.log(level, message, extra=extra, exc_info=exc_info, stacklevel=2)
