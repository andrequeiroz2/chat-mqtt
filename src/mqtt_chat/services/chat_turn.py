"""Orquestração de um turno de chat TomatoIA (classificação + persistência seletiva)."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from pydantic_ai import Agent

from mqtt_chat.agent.chat_agent import run_chat
from mqtt_chat.agent.deps import UserDeps
from mqtt_chat.agent.tomato_ia import OFF_TOPIC_REPLY
from mqtt_chat.config.settings import get_settings
from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.chat import ChatTurnResult, SuggestedUiAction
from mqtt_chat.schemas.turn_outcome import TurnOutcome
from mqtt_chat.services.chat_history import append_turn, load_message_history
from mqtt_chat.services.conversation_context import ensure_conversation_context
from mqtt_chat.services.device_intent_resolver import resolve_device_intent
from mqtt_chat.services.resolver_turn import (
    execute_pending_actuator_command,
    execute_resolver_turn,
)

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient

logger = logging.getLogger(__name__)


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
    publish_queue: asyncio.Queue[tuple[str, bytes]] | None = None,
) -> TurnOutcome:
    """Carrega histórico, executa agente, persiste somente turnos in-scope."""
    settings = get_settings()
    cap = settings.chat_device_snapshot_cap
    context = ensure_conversation_context(db, deps.user_id, deps.session_id, cap=cap)

    pending_outcome = await execute_pending_actuator_command(
        db,
        deps,
        user_message,
        context,
        max_messages,
        publish_queue,
    )
    if pending_outcome is not None:
        return pending_outcome

    resolved = resolve_device_intent(user_message, context)
    if resolved.short_circuit and resolved.outcome != "pass_through":
        return execute_resolver_turn(
            db,
            deps,
            user_message,
            context,
            resolved,
            max_messages,
        )

    history = load_message_history(db, deps.user_id, deps.session_id, max_messages)
    deps.history_empty = len(history) == 0
    # 018-04: invariante — zera antes do run; tools atribuem durante o turno;
    # propagado à resposta apenas se scope == "product" (ver abaixo).
    deps.suggested_ui = None
    raw = await run_chat(
        agent,
        deps,
        user_message,
        history,
        request_limit=settings.chat_agent_request_limit,
    )
    outcome = finalize_turn(raw)
    suggested_ui = deps.suggested_ui if outcome.scope == "product" else None
    outcome = TurnOutcome(
        reply=outcome.reply,
        persist=outcome.persist,
        scope=outcome.scope,
        suggested_ui=suggested_ui,
    )

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
