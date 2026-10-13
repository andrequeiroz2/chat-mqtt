"""Rotas HTTP de adoção (v1.2-dev)."""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from google.cloud.firestore_v1 import Client as FirestoreClient

from mqtt_chat.api.deps import AuthenticatedUser, get_current_user, require_firestore
from mqtt_chat.schemas.adoption import AdoptionSessionResponse, AdoptionStartRequest
from mqtt_chat.services.adoption import handshake, session_store

router = APIRouter(prefix="/api/v1/devices/adopt", tags=["adoption"])


def _publish_queue(request: Request) -> asyncio.Queue[tuple[str, bytes]]:
    return request.app.state.publish_queue


@router.post("/start", response_model=AdoptionSessionResponse)
async def adopt_start(
    body: AdoptionStartRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[FirestoreClient, Depends(require_firestore)],
) -> AdoptionSessionResponse:
    """Inicia sessão de adoção e publica challenge MQTT."""
    from mqtt_chat.config.settings import get_settings

    settings = get_settings()
    queue = _publish_queue(request)
    try:
        return await handshake.start_adoption(
            db,
            settings,
            queue,
            user_id=user.user_id,
            body=body,
        )
    except ValueError as exc:
        if str(exc) == "invalid_mac_address":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="invalid_mac_address",
            ) from exc
        raise
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ownership_conflict",
        ) from exc


@router.get("/sessions/{session_id}", response_model=AdoptionSessionResponse)
async def get_adoption_session(
    session_id: str,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[FirestoreClient, Depends(require_firestore)],
) -> AdoptionSessionResponse:
    """Status da sessão para UI/chat (polling)."""
    response = session_store.get_session_response(db, session_id)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")
    session = session_store.get_session(db, session_id)
    if session and session.get("user_id") != user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")
    return response


@router.post("/sessions/{session_id}/cancel", response_model=AdoptionSessionResponse)
async def cancel_adoption_session(
    session_id: str,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[FirestoreClient, Depends(require_firestore)],
) -> AdoptionSessionResponse:
    """Aborta sessão ativa."""
    if not handshake.cancel_session(db, session_id, user.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")
    response = session_store.get_session_response(db, session_id)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")
    return response
