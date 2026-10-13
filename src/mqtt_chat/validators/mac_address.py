"""Normalização e validação de MAC (contrato adoção)."""

from __future__ import annotations

import re

_MAC_COLON_RE = re.compile(
    r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$",
)
_MAC_HEX12_RE = re.compile(r"^[0-9A-Fa-f]{12}$")


class InvalidMacAddressError(ValueError):
    """MAC inválido ou vazio."""


def normalize_mac_address(raw: str) -> str:
    """
    Formato canônico AA:BB:CC:DD:EE:FF (uppercase, dois-pontos).

    Aceita 12 hex contínuos ou já formatado com ':'.
    """
    text = raw.strip()
    if not text:
        raise InvalidMacAddressError("empty")

    if _MAC_COLON_RE.match(text):
        return text.upper()

    compact = text.replace(":", "").replace("-", "").upper()
    if not _MAC_HEX12_RE.match(compact):
        raise InvalidMacAddressError(raw)

    pairs = [compact[i : i + 2] for i in range(0, 12, 2)]
    return ":".join(pairs)


def mac_to_normalized_topic_id(mac_address: str) -> str:
    """12 hex uppercase sem ':' — sufixo UC-A unclaimed/devices/{id}."""
    canonical = normalize_mac_address(mac_address)
    return canonical.replace(":", "")
