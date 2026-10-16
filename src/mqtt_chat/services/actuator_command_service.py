"""Publicação de comando binário em atuador (MQTT via fila do worker)."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.actuator_command import ActuatorSetCommandPayload, BinaryActuatorValue

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient

logger = logging.getLogger(__name__)


class ActuatorCommandError(Exception):
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        super().__init__(message or code)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def build_set_payload(*, binary_value: BinaryActuatorValue, channel: int = 1) -> ActuatorSetCommandPayload:
    return ActuatorSetCommandPayload(channel=channel, value=binary_value)


async def publish_actuator_command(
    db: FirestoreClient,
    user_id: str,
    device_id: str,
    binary_value: BinaryActuatorValue,
    publish_queue: asyncio.Queue[tuple[str, bytes]] | None,
    *,
    channel: int = 1,
) -> ActuatorSetCommandPayload:
    """
    Publica comando set na fila MQTT e persiste last_command no device.

    Raises:
        ActuatorCommandError: device_not_found, not_actuator, mqtt_unavailable.
    """
    snap = db.collection("devices").document(device_id).get()
    if not snap.exists:
        raise ActuatorCommandError("device_not_found")
    data = snap.to_dict() or {}
    if data.get("user_id") != user_id:
        raise ActuatorCommandError("device_not_found")
    if data.get("device_type") != "actuator":
        raise ActuatorCommandError("not_actuator")

    topic_base = data.get("mqtt_topic_base")
    if not isinstance(topic_base, str) or not topic_base.strip():
        raise ActuatorCommandError("device_topic_missing")

    payload = build_set_payload(binary_value=binary_value, channel=channel)
    body = payload.model_dump(mode="json")
    topic = f"{topic_base.rstrip('/')}/commands"

    if publish_queue is None:
        raise ActuatorCommandError("mqtt_unavailable")

    await publish_queue.put((topic, json.dumps(body, separators=(",", ":")).encode("utf-8")))

    now = _now_iso()
    snap.reference.set(
        {
            "last_command": body,
            "last_command_at": now,
        },
        merge=True,
    )

    log_event(
        logger,
        logging.INFO,
        events.MCP_TOOL_CALL,
        "actuator command published",
        tool="publish_command",
        user_id=user_id,
        device_id=device_id,
        binary_value=binary_value,
    )
    return payload
