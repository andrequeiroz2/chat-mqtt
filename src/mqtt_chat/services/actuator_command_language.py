"""Mapeamento PT → comando binário 0/1 (contrato actuator-binary-command)."""

from __future__ import annotations

import re
import unicodedata

from mqtt_chat.schemas.actuator_command import BinaryActuatorValue, PowerIntent

_ON_PATTERNS = (
    r"\bligar\b",
    r"\bliga\b",
    r"\bligue\b",
    r"\bativar\b",
    r"\bativa\b",
    r"\bacionar\b",
    r"\baciona\b",
    r"\babrir\b",
    r"\babre\b",
    r"\benergizar\b",
    r"\benergiza\b",
)
_OFF_PATTERNS = (
    r"\bdesligar\b",
    r"\bdesliga\b",
    r"\bdesligue\b",
    r"\bdesativar\b",
    r"\bdesativa\b",
    r"\bfechar\b",
    r"\bfecha\b",
    r"\bfeche\b",
    r"\bcortar\b",
    r"\bcorta\b",
)
_COMMAND_CONTEXT = (
    r"\b(rele|relay|atuador|actuator|motor|lampada|lâmpada|portao|portão|valvula|válvula)\b",
    r"\bo\s+\w+\s+(rele|relé|motor)\b",
)


def _normalize_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in folded if not unicodedata.combining(ch))


def utterance_has_actuator_command_verbs(message: str) -> bool:
    """True se a frase contém verbo de ligar/desligar (potência)."""
    text = _normalize_text(message)
    return any(re.search(p, text) for p in _ON_PATTERNS + _OFF_PATTERNS)


def utterance_suggests_actuator_target(message: str) -> bool:
    """Heurística: menção a atuador ou foco implícito em comando."""
    text = _normalize_text(message)
    if any(re.search(p, text) for p in _COMMAND_CONTEXT):
        return True
    return utterance_has_actuator_command_verbs(message)


def parse_power_intent(message: str) -> PowerIntent | None:
    """Deriva on/off a partir de verbos PT; None se conflito ou ausência."""
    text = _normalize_text(message)
    on = any(re.search(p, text) for p in _ON_PATTERNS)
    off = any(re.search(p, text) for p in _OFF_PATTERNS)
    if on and off:
        return None
    if on:
        return "on"
    if off:
        return "off"
    return None


def power_to_binary_value(power: PowerIntent) -> BinaryActuatorValue:
    return 1 if power == "on" else 0


def power_verb_pt(power: PowerIntent) -> str:
    return "ligar" if power == "on" else "desligar"


def is_confirmation_utterance(message: str) -> bool:
    text = _normalize_text(message.strip())
    return text in {
        "sim",
        "s",
        "confirmo",
        "confirmar",
        "ok",
        "pode",
        "pode enviar",
        "manda",
        "envia",
        "yes",
    } or text.startswith("sim ")


def mqtt_set_value_to_bool(value: object) -> bool:
    """
    Normaliza `value` de comando MQTT (contrato actuator-binary-command).

    Aceita boolean, integer 0|1 ou float 0.0|1.0.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, float) and value in (0.0, 1.0):
        return bool(int(value))
    raise ValueError("invalid_actuator_command_value")


def is_cancellation_utterance(message: str) -> bool:
    text = _normalize_text(message.strip())
    return text in {"nao", "não", "n", "cancelar", "cancela", "pare", "stop"} or text.startswith(
        "nao "
    )
