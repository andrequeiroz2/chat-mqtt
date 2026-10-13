"""Orquestração de um turno de chat TomatoIA (classificação + persistência seletiva)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic_ai import Agent

from mqtt_chat.agent.chat_agent import run_chat
from mqtt_chat.agent.deps import UserDeps
from mqtt_chat.agent.tomato_ia import OFF_TOPIC_REPLY
from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.chat import ChatScope, ChatTurnResult
from mqtt_chat.services.chat_history import append_turn, load_message_history

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TurnOutcome:
    """Resposta HTTP e se o par user/assistant foi persistido."""

    reply: str
    persist: bool
    scope: ChatScope


def finalize_turn(raw: ChatTurnResult) -> TurnOutcome:
    """Aplica regras de produto: off-topic usa texto fixo e não persiste."""
    if raw.scope == "off_topic":
        return TurnOutcome(reply=OFF_TOPIC_REPLY, persist=False, scope="off_topic")
    return TurnOutcome(reply=raw.reply.strip(), persist=True, scope="product")


async def execute_chat_turn(
    agent: Agent[UserDeps, ChatTurnResult],
    db: FirestoreClient,
    deps: UserDeps,
    user_message: str,
    max_messages: int,
) -> TurnOutcome:
    """Carrega histórico, executa agente, persiste somente turnos in-scope."""
    history = load_message_history(db, deps.user_id, deps.session_id, max_messages)
    deps_with_history = UserDeps(
        user_id=deps.user_id,
        display_name=deps.display_name,
        session_id=deps.session_id,
        db=deps.db,
        history_empty=len(history) == 0,
    )
    raw = await run_chat(agent, deps_with_history, user_message, history)
    outcome = finalize_turn(raw)

    if outcome.persist:
        append_turn(
            db,
            deps.user_id,
            deps.session_id,
            user_message,
            outcome.reply,
            max_messages,
        )
    else:
        log_event(
            logger,
            logging.INFO,
            events.CHAT_TURN_OFF_TOPIC,
            "Chat turn off-topic (not persisted)",
            user_id=deps.user_id,
            session_id=deps.session_id,
        )

    return outcome
