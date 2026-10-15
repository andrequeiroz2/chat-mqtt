"""Filtros de logging (redação de segredos)."""

from __future__ import annotations

import logging
import re
from typing import Any

# Chaves cujos valores devem ser mascarados em mensagens e atributos serializados.
SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|secret|token|private_key|authorization|api_key|credential)",
    re.IGNORECASE,
)

REDACTED = "[REDACTED]"


def redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Retorna cópia do dict com valores sensíveis mascarados."""
    out: dict[str, Any] = {}
    for key, value in data.items():
        if SENSITIVE_KEY_PATTERN.search(key):
            out[key] = REDACTED
        elif isinstance(value, dict):
            out[key] = redact_mapping(value)
        else:
            out[key] = value
    return out


def redact_text(text: str) -> str:
    """Mascara padrões password= / token= em strings (incl. query WebSocket)."""
    text = re.sub(
        r"(?i)(password|secret|token|api_key)\s*[:=]\s*\S+",
        r"\1=" + REDACTED,
        text,
    )
    text = re.sub(
        r"(?i)([?&]token=)[^&\s\"']+",
        r"\1" + REDACTED,
        text,
    )
    return text


class SecretRedactionFilter(logging.Filter):
    """Filtro que redige segredos na mensagem antes da formatação."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg)
        if record.args:
            record.args = tuple(
                redact_text(arg) if isinstance(arg, str) else arg for arg in record.args
            )
        attrs = getattr(record, "attributes", None)
        if isinstance(attrs, dict):
            record.attributes = redact_mapping(attrs)
        return True
