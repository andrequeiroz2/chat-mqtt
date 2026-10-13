"""Persistência adoption_sessions (Firestore Admin)."""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from google.cloud.firestore_v1 import Client as FirestoreClient

from mqtt_chat.config.settings import Settings
from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.adoption import AdoptionSessionResponse, SessionStatus
from mqtt_chat.services.adoption.user_messages import user_message_for_failure
from mqtt_chat.validators.mac_address import normalize_mac_address

logger = logging.getLogger(__name__)

COLLECTION = "adoption_sessions"
ACTIVE_STATUSES: frozenset[str] = frozenset(
    {
        "started",
        "device_verified",
        "config_sent",
        "awaiting_device_ack",
    }
)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _doc_to_response(doc_id: str, data: dict[str, Any]) -> AdoptionSessionResponse:
    status = data.get("session_status", "failed")
    user_msg = data.get("user_message")
    if status in ("failed", "expired") and not user_msg:
        user_msg = user_message_for_failure(data.get("failure_reason"))
    return AdoptionSessionResponse(
        session_id=doc_id,
        session_status=status,  # type: ignore[arg-type]
        mac_address=data.get("mac_address", ""),
        expires_at=data.get("expires_at", ""),
        user_message=user_msg,
        failure_reason=data.get("failure_reason"),
        device_id=data.get("proposed_device_id"),
        device_name=data.get("device_name"),
    )


def find_device_by_mac(db: FirestoreClient, mac_address: str) -> dict[str, Any] | None:
    """Primeiro documento em devices com este MAC."""
    canonical = normalize_mac_address(mac_address)
    query = db.collection("devices").where("mac_address", "==", canonical).limit(1)
    for snap in query.stream():
        data = snap.to_dict() or {}
        data["device_id"] = snap.id
        return data
    return None


def create_session(
    db: FirestoreClient,
    settings: Settings,
    *,
    user_id: str,
    mac_address: str,
    device_name: str,
) -> tuple[str, dict[str, Any]]:
    """Cria adoption_sessions; retorna (session_id, doc data)."""
    session_id = str(uuid.uuid4())
    proposed_device_id = str(uuid.uuid4())
    nonce = secrets.token_hex(4)
    started = datetime.now(UTC)
    expires = started + timedelta(seconds=settings.adoption_handshake_timeout_sec)

    doc = {
        "session_id": session_id,
        "user_id": user_id,
        "mac_address": normalize_mac_address(mac_address),
        "device_name": device_name,
        "claim_token": None,
        "session_status": "started",
        "device_info_candidate": None,
        "contract_validation": None,
        "proposed_device_id": proposed_device_id,
        "proposed_mqtt_topic_base": None,
        "nonce": nonce,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "expires_at": expires.isoformat().replace("+00:00", "Z"),
        "failure_reason": None,
        "user_message": None,
    }
    db.collection(COLLECTION).document(session_id).set(doc)
    log_event(
        logger,
        logging.INFO,
        events.ADOPTION_SESSION_STARTED,
        "Adoption session started",
        session_id=session_id,
        user_id=user_id,
    )
    return session_id, doc


def get_session(db: FirestoreClient, session_id: str) -> dict[str, Any] | None:
    snap = db.collection(COLLECTION).document(session_id).get()
    if not snap.exists:
        return None
    data = snap.to_dict() or {}
    data["session_id"] = session_id
    return data


def update_session(db: FirestoreClient, session_id: str, fields: dict[str, Any]) -> None:
    fields = {**fields, "updated_at": _now_iso()}
    db.collection(COLLECTION).document(session_id).update(fields)


def fail_session(
    db: FirestoreClient,
    session_id: str,
    *,
    failure_reason: str,
    session_status: SessionStatus = "failed",
) -> None:
    user_message = user_message_for_failure(failure_reason)
    update_session(
        db,
        session_id,
        {
            "session_status": session_status,
            "failure_reason": failure_reason,
            "user_message": user_message,
        },
    )
    log_event(
        logger,
        logging.WARNING,
        events.ADOPTION_SESSION_FAILED,
        "Adoption session failed",
        session_id=session_id,
        failure_reason=failure_reason,
    )


def expire_if_needed(db: FirestoreClient, session: dict[str, Any]) -> dict[str, Any]:
    """Marca expired se passou expires_at e ainda ativa."""
    status = session.get("session_status")
    if status not in ACTIVE_STATUSES:
        return session
    expires_at = session.get("expires_at")
    if not expires_at:
        return session
    try:
        exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return session
    if datetime.now(UTC) > exp:
        sid = session["session_id"]
        fail_session(db, sid, failure_reason="handshake_timeout", session_status="expired")
        session = get_session(db, sid) or session
    return session


def get_session_response(db: FirestoreClient, session_id: str) -> AdoptionSessionResponse | None:
    data = get_session(db, session_id)
    if data is None:
        return None
    data = expire_if_needed(db, data)
    return _doc_to_response(session_id, data)
