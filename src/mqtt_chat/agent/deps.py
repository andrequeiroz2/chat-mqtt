"""Dependências injetadas no agente de chat."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient


@dataclass(frozen=True, slots=True)
class UserDeps:
    """Contexto do usuário autenticado (nunca confiar em dados do LLM)."""

    user_id: str
    display_name: str
    session_id: str
    db: FirestoreClient
    history_empty: bool = False
