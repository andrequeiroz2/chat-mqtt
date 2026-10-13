"""Contratos HTTP e payloads MQTT de adoção (v1.2-dev UC-A)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

SessionStatus = Literal[
    "started",
    "device_verified",
    "config_sent",
    "awaiting_device_ack",
    "committed",
    "failed",
    "expired",
]


class AdoptionStartRequest(BaseModel):
    """Início de sessão — QR-A / dev: MAC explícito."""

    mac_address: str = Field(min_length=1, max_length=32)
    device_name: str = Field(default="Meu dispositivo", min_length=1, max_length=120)


class AdoptionSessionResponse(BaseModel):
    """Estado exposto à UI / chat (sem secrets)."""

    session_id: str
    session_status: SessionStatus
    mac_address: str
    expires_at: str
    user_message: str | None = None
    failure_reason: str | None = None
    device_id: str | None = None
    device_name: str | None = None


class DeviceInfoMqttPayload(BaseModel):
    """Device → backend em `{unclaimed}/info` (espelho §6.5)."""

    session_id: str
    mac_address: str
    device_type: Literal["sensor", "actuator"]
    model: str = Field(min_length=1)
    adopted_status: int = Field(default=0, ge=0, le=1)
    sensor_type: str | None = None
    actuator_type: str | None = None
    parameter_ranges: dict[str, Any] | None = None
    command_spec: dict[str, Any] | None = None
    firmware_version: str | None = None
    user_id: str | None = None


class AdoptionChallengeMqttPayload(BaseModel):
    """Backend → device `{unclaimed}/challenge`."""

    session_id: str
    nonce: str


class AdoptionConfigMqttPayload(BaseModel):
    """Backend → device `{unclaimed}/config`."""

    session_id: str
    nonce: str
    user_id: str
    device_id: str
    device_name: str
    mqtt_topic_base: str
    broker_url: str
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    adopted_status: int = 1


class AdoptionAckMqttPayload(BaseModel):
    """Device → backend `{unclaimed}/ack` (§6.7)."""

    ts: str
    session_id: str
    mac_address: str
    status: Literal["adoption_complete"]
    nonce: str
    firmware_version: str | None = None
