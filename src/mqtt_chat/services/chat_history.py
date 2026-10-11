"""Histórico de chat no Firestore (buffer de 15 turnos)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from mqtt_chat.logging import events, log_event

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient

logger = logging.getLogger(__name__)

Role = Literal["user", "assistant"]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _messages_collection(db: FirestoreClient, user_id: str, session_id: str):
    return (
        db.collection("users")
        .document(user_id)
        .collection("chat_sessions")
        .document(session_id)
        .collection("messages")
    )


def load_message_history(
    db: FirestoreClient,
    user_id: str,
    session_id: str,
    max_messages: int,
) -> list[tuple[Role, str]]:
    """Últimas mensagens ordenadas por tempo (limite via CHAT_MAX_TURNS)."""
    col = _messages_collection(db, user_id, session_id)
    # limit_to_last() não suporta stream — ver Firestore SDK.
    snapshot = col.order_by("created_at").limit_to_last(max_messages).get()
    out: list[tuple[Role, str]] = []
    for doc in snapshot:
        data = doc.to_dict() or {}
        role = data.get("role")
        content = data.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            out.append((role, content))
    return out


def append_turn(
    db: FirestoreClient,
    user_id: str,
    session_id: str,
    user_content: str,
    assistant_content: str,
    max_messages: int,
) -> None:
    """Persiste par user/assistant e remove excedentes além do limite configurado."""
    col = _messages_collection(db, user_id, session_id)
    session_ref = col.parent
    now = _now_iso()
    session_ref.set(
        {"session_id": session_id, "updated_at": now},
        merge=True,
    )
    col.document().set(
        {"role": "user", "content": user_content, "created_at": now},
    )
    col.document().set(
        {
            "role": "assistant",
            "content": assistant_content,
            "created_at": _now_iso(),
        },
    )

    all_docs = list(col.order_by("created_at").stream())
    excess = len(all_docs) - max_messages
    if excess > 0:
        for doc in all_docs[:excess]:
            doc.reference.delete()

    log_event(
        logger,
        logging.DEBUG,
        events.CHAT_TURN_PERSISTED,
        "Chat turn persisted",
        user_id=user_id,
        session_id=session_id,
        messages_kept=min(len(all_docs), max_messages),
    )
