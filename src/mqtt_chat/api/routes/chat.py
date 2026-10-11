"""Chat autenticado (JSON e SSE)."""

from __future__ import annotations

import json
import logging
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud.firestore_v1 import Client as FirestoreClient
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, UserError
from sse_starlette.sse import EventSourceResponse

from mqtt_chat.agent.chat_agent import create_chat_agent, run_chat
from mqtt_chat.agent.deps import UserDeps
from mqtt_chat.api.deps import AuthenticatedUser, get_current_user, require_firestore
from mqtt_chat.config.settings import Settings, get_settings
from mqtt_chat.schemas.chat import ChatRequest
from mqtt_chat.services.chat_history import append_turn, load_message_history
from mqtt_chat.services.user_profile import ensure_user_profile

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)

_agent: Agent[UserDeps, str] | None = None
_agent_model_id: str | None = None


def _get_agent(settings: Settings) -> Agent[UserDeps, str]:
    global _agent, _agent_model_id
    if _agent is None or _agent_model_id != settings.chat_model:
        _agent = None
    if _agent is None:
        if not settings.chat_model_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="chat_model_not_configured",
            )
        try:
            _agent = create_chat_agent(settings)
            _agent_model_id = settings.chat_model
        except (UserError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="chat_model_not_configured",
            ) from None
    return _agent


def _user_deps(
    user: AuthenticatedUser,
    db: FirestoreClient,
    session_id: str,
) -> UserDeps:
    profile = ensure_user_profile(db, user.decoded_token)
    return UserDeps(
        user_id=user.user_id,
        display_name=profile.display_name,
        session_id=session_id,
    )


@router.post("/chat")
async def post_chat(
    body: ChatRequest,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[FirestoreClient, Depends(require_firestore)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    """Um turno de chat; resposta JSON."""
    agent = _get_agent(settings)
    deps = _user_deps(user, db, body.session_id)
    max_msg = settings.chat_max_messages
    history = load_message_history(db, user.user_id, body.session_id, max_msg)
    try:
        reply = await run_chat(agent, deps, body.message, history)
    except ModelHTTPError as exc:
        if exc.status_code in (404, 503):
            detail = "chat_model_busy" if exc.status_code == 503 else "chat_model_unavailable"
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=detail,
            ) from exc
        raise
    append_turn(db, user.user_id, body.session_id, body.message, reply, max_msg)
    return {"reply": reply, "session_id": body.session_id}


@router.post("/chat/stream")
async def post_chat_stream(
    body: ChatRequest,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[FirestoreClient, Depends(require_firestore)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> EventSourceResponse:
    """Stream SSE: eventos token (texto) e done."""

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        agent = _get_agent(settings)
        deps = _user_deps(user, db, body.session_id)
        max_msg = settings.chat_max_messages
        history = load_message_history(db, user.user_id, body.session_id, max_msg)
        reply = await run_chat(agent, deps, body.message, history)
        append_turn(db, user.user_id, body.session_id, body.message, reply, max_msg)
        yield {"event": "message", "data": json.dumps({"text": reply}, ensure_ascii=False)}
        yield {"event": "done", "data": json.dumps({"session_id": body.session_id})}

    return EventSourceResponse(event_generator())
