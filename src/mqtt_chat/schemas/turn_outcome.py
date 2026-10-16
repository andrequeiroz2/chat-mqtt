"""Resultado de um turno de chat (HTTP / serviços)."""

from __future__ import annotations

from dataclasses import dataclass

from mqtt_chat.schemas.chat import ChatScope, SuggestedUiAction


@dataclass(frozen=True, slots=True)
class TurnOutcome:
    """Resposta HTTP e se o par user/assistant foi persistido."""

    reply: str
    persist: bool
    scope: ChatScope
    suggested_ui: SuggestedUiAction | None = None
