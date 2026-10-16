"""Chat autenticado (JSON e SSE)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from google.cloud.firestore_v1 import Client as FirestoreClient
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded, UserError
from sse_starlette.sse import EventSourceResponse

from mqtt_chat.agent.chat_agent import create_chat_agent
from mqtt_chat.agent.deps import UserDeps
from mqtt_chat.api.deps import AuthenticatedUser, get_current_user, require_firestore
from mqtt_chat.config.settings import Settings, get_settings
from mqtt_chat.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatTurnResult,
    PostAdoptionActionItem,
    PostAdoptionRequest,
    PostAdoptionResponse,
)
from mqtt_chat.services.chat_turn import TurnOutcome, execute_chat_turn
from mqtt_chat.services.post_adoption_turn import PostAdoptionError, register_post_adoption_turn
from mqtt_chat.services.user_profile import ensure_user_profile

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)

_agent: Agent[UserDeps, ChatTurnResult] | None = None
_agent_model_id: str | None = None


def _get_agent(settings: Settings) -> Agent[UserDeps, ChatTurnResult]:
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
        db=db,
    )


def _raise_model_http_error(exc: ModelHTTPError) -> None:
    if exc.status_code in (404, 503):
        detail = "chat_model_busy" if exc.status_code == 503 else "chat_model_unavailable"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc
    raise exc


def _to_response(outcome: TurnOutcome, session_id: str) -> ChatResponse:
    return ChatResponse(
        reply=outcome.reply,
        session_id=session_id,
        persisted=outcome.persist,
        suggested_ui=outcome.suggested_ui,
    )


@router.post("/chat/post-adoption", response_model=PostAdoptionResponse)
async def post_chat_post_adoption(
    body: PostAdoptionRequest,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[FirestoreClient, Depends(require_firestore)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PostAdoptionResponse:
    """Turno zero após adoção commitada: foco de sessão + ações sugeridas (G8/G9)."""
    try:
        result = register_post_adoption_turn(
            db,
            user.user_id,
            body.session_id,
            body.device_id,
            settings=settings,
        )
    except PostAdoptionError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.code,
        ) from exc
    return PostAdoptionResponse(
        message=result.message,
        session_id=body.session_id,
        device_id=result.device_id,
        device_name=result.device_name,
        device_type=result.device_type,
        actions=[
            PostAdoptionActionItem(
                action_id=a.action_id,
                label=a.label,
                prompt=a.prompt,
            )
            for a in result.actions
        ],
    )


@router.post("/chat", response_model=ChatResponse)
async def post_chat(
    body: ChatRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[FirestoreClient, Depends(require_firestore)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatResponse:
    """Um turno de chat; resposta JSON."""
    agent = _get_agent(settings)
    deps = _user_deps(user, db, body.session_id)
    queue: asyncio.Queue[tuple[str, bytes]] | None = getattr(
        request.app.state,
        "publish_queue",
        None,
    )
    try:
        outcome = await execute_chat_turn(
            agent,
            db,
            deps,
            body.message,
            settings.chat_max_messages,
            publish_queue=queue,
        )
    except UsageLimitExceeded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="chat_turn_limit_exceeded",
        ) from None
    except ModelHTTPError as exc:
        _raise_model_http_error(exc)
    return _to_response(outcome, body.session_id)


@router.post("/chat/stream")
async def post_chat_stream(
    body: ChatRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[FirestoreClient, Depends(require_firestore)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> EventSourceResponse:
    """Stream SSE: eventos token (texto) e done."""
    queue: asyncio.Queue[tuple[str, bytes]] | None = getattr(
        request.app.state,
        "publish_queue",
        None,
    )

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        agent = _get_agent(settings)
        deps = _user_deps(user, db, body.session_id)
        try:
            outcome = await execute_chat_turn(
                agent,
                db,
                deps,
                body.message,
                settings.chat_max_messages,
                publish_queue=queue,
            )
        except UsageLimitExceeded:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="chat_turn_limit_exceeded",
            ) from None
        except ModelHTTPError as exc:
            _raise_model_http_error(exc)
        payload = _to_response(outcome, body.session_id)
        yield {
            "event": "message",
            "data": json.dumps(
                {"text": payload.reply, "persisted": payload.persisted},
                ensure_ascii=False,
            ),
        }
        yield {"event": "done", "data": json.dumps({"session_id": body.session_id})}

    return EventSourceResponse(event_generator())
