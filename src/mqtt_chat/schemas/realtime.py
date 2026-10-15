"""Mensagens WebSocket tempo real (API → browser)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from mqtt_chat.schemas.telemetry import ReadingItem


class RealtimeEnvelope(BaseModel):
    """Frame JSON enviado ao cliente WebSocket."""

    type: Literal["connected", "telemetry", "device_status", "error"]
    payload: dict[str, Any] = Field(default_factory=dict)


class RealtimeTelemetryPayload(BaseModel):
    device_id: str
    device_ts: str | None = None
    received_at: str
    readings: list[ReadingItem]


class RealtimeDeviceStatusPayload(BaseModel):
    device_id: str
    operation_status: str | None = None
    last_seen_at: str | None = None
