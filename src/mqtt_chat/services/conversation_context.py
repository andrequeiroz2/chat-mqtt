"""Load/save/refresh de conversation_context no Firestore."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.conversation_context import (
    ConversationContext,
    DeviceSnapshotEntry,
    FocusReason,
)
from mqtt_chat.services import devices as devices_service

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient

logger = logging.getLogger(__name__)

CONTEXT_SCHEMA_VERSION = 1


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _session_ref(db: FirestoreClient, user_id: str, session_id: str):
    return (
        db.collection("users")
        .document(user_id)
        .collection("chat_sessions")
        .document(session_id)
    )


def _summary_to_entry(summary, data: dict[str, Any] | None) -> DeviceSnapshotEntry:
    extra = data or {}
    return DeviceSnapshotEntry(
        device_id=summary.device_id,
        device_name=summary.device_name,
        device_type=summary.device_type,
        adopted_at=summary.adopted_at,
        operation_status=summary.operation_status,
        last_seen_at=summary.last_seen_at,
        last_command=extra.get("last_command"),
        last_command_at=extra.get("last_command_at"),
        last_reported_state=extra.get("last_reported_state"),
    )


def build_snapshot_from_db(
    db: FirestoreClient,
    user_id: str,
    *,
    cap: int,
) -> ConversationContext:
    """Monta snapshot ordenado por adoção recente (limit cap)."""
    candidates = devices_service.list_all_adopted_summaries(db, user_id)
    sensors = sum(1 for c in candidates if c.device_type == "sensor")
    actuators = sum(1 for c in candidates if c.device_type == "actuator")
    sorted_items = sorted(candidates, key=lambda c: c.adopted_at, reverse=True)
    top = sorted_items[:cap]

    entries: list[DeviceSnapshotEntry] = []
    for summary in top:
        snap = db.collection("devices").document(summary.device_id).get()
        data = snap.to_dict() if snap.exists else None
        entries.append(_summary_to_entry(summary, data))

    return ConversationContext(
        schema_version=CONTEXT_SCHEMA_VERSION,
        updated_at=_now_iso(),
        device_count=len(candidates),
        sensor_count=sensors,
        actuator_count=actuators,
        device_snapshot=entries,
    )


def load_conversation_context(
    db: FirestoreClient,
    user_id: str,
    session_id: str,
) -> ConversationContext | None:
    ref = _session_ref(db, user_id, session_id)
    doc = ref.get()
    if not doc.exists:
        return None
    raw = doc.to_dict() or {}
    payload = raw.get("conversation_context")
    if not isinstance(payload, dict):
        return None
    try:
        return ConversationContext.model_validate(payload)
    except Exception:
        log_event(
            logger,
            logging.WARNING,
            events.HANDLER_FAILED,
            "Invalid conversation_context in Firestore",
            user_id=user_id,
            session_id=session_id,
        )
        return None


def save_conversation_context(
    db: FirestoreClient,
    user_id: str,
    session_id: str,
    context: ConversationContext,
) -> None:
    context.updated_at = _now_iso()
    ref = _session_ref(db, user_id, session_id)
    ref.set(
        {
            "session_id": session_id,
            "conversation_context": context.model_dump(mode="json"),
            "updated_at": context.updated_at,
        },
        merge=True,
    )


def ensure_conversation_context(
    db: FirestoreClient,
    user_id: str,
    session_id: str,
    *,
    cap: int,
) -> ConversationContext:
    existing = load_conversation_context(db, user_id, session_id)
    if existing is not None:
        return existing
    built = build_snapshot_from_db(db, user_id, cap=cap)
    save_conversation_context(db, user_id, session_id, built)
    return built


def refresh_conversation_context(
    db: FirestoreClient,
    user_id: str,
    session_id: str,
    *,
    cap: int,
    keep_focus: bool = True,
) -> ConversationContext:
    previous = load_conversation_context(db, user_id, session_id)
    built = build_snapshot_from_db(db, user_id, cap=cap)
    if keep_focus and previous:
        built.session_focus_device_id = previous.session_focus_device_id
        built.focus_reason = previous.focus_reason
    save_conversation_context(db, user_id, session_id, built)
    return built


def set_session_focus(
    context: ConversationContext,
    device_id: str,
    reason: FocusReason,
) -> None:
    context.session_focus_device_id = device_id
    context.focus_reason = reason


def set_focus_after_adoption(
    db: FirestoreClient,
    user_id: str,
    session_id: str,
    device_id: str,
    *,
    cap: int,
) -> ConversationContext:
    """RF-CHAT-CTX-04 — foco pós-adoção (chamada UI/API)."""
    context = refresh_conversation_context(
        db,
        user_id,
        session_id,
        cap=cap,
        keep_focus=False,
    )
    set_session_focus(context, device_id, "adoption")
    save_conversation_context(db, user_id, session_id, context)
    return context
