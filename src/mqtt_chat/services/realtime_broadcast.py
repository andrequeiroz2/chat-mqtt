"""Publicação de eventos MQTT ingestados no hub WebSocket."""

from __future__ import annotations

import logging

from mqtt_chat.logging import events, log_event
from mqtt_chat.realtime.hub import get_realtime_hub
from mqtt_chat.schemas.realtime import (
    RealtimeDeviceStatusPayload,
    RealtimeEnvelope,
    RealtimeTelemetryPayload,
)
from mqtt_chat.schemas.telemetry import ReadingItem
from mqtt_chat.worker.topics import ParsedDeviceTopic

logger = logging.getLogger(__name__)


async def broadcast_telemetry(
    parsed: ParsedDeviceTopic,
    readings: list[ReadingItem],
    *,
    device_ts: str,
    received_at: str,
) -> None:
    if not readings:
        return
    payload = RealtimeTelemetryPayload(
        device_id=parsed.device_id,
        device_ts=device_ts,
        received_at=received_at,
        readings=readings,
    )
    envelope = RealtimeEnvelope(type="telemetry", payload=payload.model_dump())
    await get_realtime_hub().publish(
        parsed.user_id,
        envelope,
        device_id=parsed.device_id,
    )
    log_event(
        logger,
        logging.DEBUG,
        events.REALTIME_EVENT_PUBLISHED,
        "Realtime telemetry published",
        user_id=parsed.user_id,
        device_id=parsed.device_id,
        readings_count=len(readings),
    )


async def broadcast_device_status(
    parsed: ParsedDeviceTopic,
    *,
    operation_status: str | None,
    last_seen_at: str,
) -> None:
    payload = RealtimeDeviceStatusPayload(
        device_id=parsed.device_id,
        operation_status=operation_status,
        last_seen_at=last_seen_at,
    )
    envelope = RealtimeEnvelope(type="device_status", payload=payload.model_dump())
    await get_realtime_hub().publish(
        parsed.user_id,
        envelope,
        device_id=parsed.device_id,
    )
