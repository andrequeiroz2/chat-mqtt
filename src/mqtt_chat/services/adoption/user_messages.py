"""Mapeamento failure_reason → user_message (PT, seguro)."""

from __future__ import annotations

GENERIC_FAILURE = (
    "A adoção não foi concluída. Nada foi salvo na sua conta. Você pode tentar outra vez."
)

_USER_MESSAGES: dict[str, str] = {
    "handshake_timeout": (
        "Não concluímos a adoção a tempo. Deixe o dispositivo ligado e conectado "
        "e escaneie o QR novamente."
    ),
    "ownership_conflict": "Este dispositivo já está vinculado a outra conta.",
    "contract_rejected": (
        "Não foi possível validar este dispositivo. Confira o QR ou o manual do produto."
    ),
    "device_not_responding": (
        "O dispositivo não respondeu no passo de pareamento. Verifique Wi‑Fi e energia e tente de novo."
    ),
    "invalid_ack": GENERIC_FAILURE,
    "invalid_info": GENERIC_FAILURE,
    "session_not_found": GENERIC_FAILURE,
    "mac_mismatch": GENERIC_FAILURE,
    "already_adopted": "Este dispositivo já está vinculado a outra conta.",
    "cancelled": "Adoção cancelada.",
}


def user_message_for_failure(reason: str | None) -> str:
    """Texto canônico para UI/chat; nunca expõe reason bruto."""
    if not reason:
        return GENERIC_FAILURE
    return _USER_MESSAGES.get(reason, GENERIC_FAILURE)


def progress_message_for_status(status: str) -> str | None:
    """Copy amigável durante polling (task 009)."""
    mapping = {
        "started": "Iniciando pareamento…",
        "device_verified": "Dispositivo reconhecido, validando…",
        "config_sent": "Enviando configuração ao dispositivo…",
        "awaiting_device_ack": "Aguardando confirmação do dispositivo…",
        "committed": "Pronto! Seu dispositivo foi adicionado.",
    }
    return mapping.get(status)
