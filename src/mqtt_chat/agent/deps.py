"""Dependências injetadas no agente de chat."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mqtt_chat.schemas.chat import SuggestedUiAction

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient


@dataclass
class UserDeps:
    """Contexto do usuário autenticado (nunca confiar em dados do LLM)."""

    user_id: str
    display_name: str
    session_id: str
    db: FirestoreClient
    history_empty: bool = False
    suggested_ui: SuggestedUiAction | None = None
