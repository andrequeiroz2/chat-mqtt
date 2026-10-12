"""Dependências injetadas no agente de chat."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserDeps:
    """Contexto do usuário autenticado (nunca confiar em dados do LLM)."""

    user_id: str
    display_name: str
    session_id: str
    history_empty: bool = False
