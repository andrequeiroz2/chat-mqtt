"""WebSocket tempo real (telemetria / status)."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from firebase_admin import auth as firebase_auth

from mqtt_chat.api.deps import AuthenticatedUser
from mqtt_chat.clients.firebase import get_firestore_client, verify_id_token
from mqtt_chat.config.settings import get_settings
from mqtt_chat.logging import events, log_event
from mqtt_chat.realtime.hub import get_realtime_hub
from mqtt_chat.schemas.realtime import RealtimeEnvelope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/realtime", tags=["realtime"])


def _authenticate_ws_token(token: str | None) -> AuthenticatedUser:
    settings = get_settings()
    if not token or not token.strip():
        raise ValueError("missing_authentication")
    if get_firestore_client(settings) is None:
        raise ValueError("firebase_not_configured")
    try:
        decoded = verify_id_token(token.strip(), settings)
    except (
        firebase_auth.InvalidIdTokenError,
        firebase_auth.ExpiredIdTokenError,
        firebase_auth.RevokedIdTokenError,
    ) as exc:
        raise ValueError("invalid_token") from exc
    uid = decoded.get("uid")
    if not uid:
        raise ValueError("invalid_token")
    return AuthenticatedUser(user_id=str(uid), decoded_token=dict(decoded))


def _device_belongs_to_user(user_id: str, device_id: str) -> bool:
    settings = get_settings()
    db = get_firestore_client(settings)
    if db is None:
        return False
    snap = db.collection("devices").document(device_id).get()
    if not snap.exists:
        return False
    data = snap.to_dict() or {}
    return data.get("user_id") == user_id


@router.websocket("/ws")
async def realtime_websocket(
    websocket: WebSocket,
    token: Annotated[str | None, Query()] = None,
    device_id: Annotated[str | None, Query()] = None,
) -> None:
    """
    Stream JSON de telemetria/status para o usuário autenticado.

    Auth: `?token=<Firebase ID token>` (renovar no cliente quando expirar).
    Filtro opcional: `device_id` (UUID do device adotado).
    """
    try:
        user = _authenticate_ws_token(token)
    except ValueError as exc:
        await websocket.close(code=4401, reason=str(exc))
        return

    if device_id and not _device_belongs_to_user(user.user_id, device_id):
        await websocket.close(code=4404, reason="device_not_found")
        return

    await websocket.accept()
    hub = get_realtime_hub()
    sub = await hub.register(
        user.user_id,
        websocket,
        device_id_filter=device_id,
    )
    log_event(
        logger,
        logging.INFO,
        events.REALTIME_WS_CONNECTED,
        "Realtime WebSocket connected",
        user_id=user.user_id,
        device_id_filter=device_id,
    )
    await websocket.send_text(
        RealtimeEnvelope(
            type="connected",
            payload={
                "user_id": user.user_id,
                "device_id_filter": device_id,
            },
        ).model_dump_json()
    )

    try:
        while True:
            # Cliente pode enviar ping JSON opcional; ignoramos conteúdo (keep-alive).
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await hub.unregister(user.user_id, sub)
