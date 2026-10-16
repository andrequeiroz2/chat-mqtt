"""Schema do contexto conversacional (Firestore chat_sessions)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from mqtt_chat.schemas.actuator_command import PendingActuatorCommand

DeviceType = Literal["sensor", "actuator"]
FocusReason = Literal["adoption", "user_mention", "ui"]
Connectivity = Literal["online", "offline", "unknown"]


class DeviceSnapshotEntry(BaseModel):
    """Entrada enxuta em device_snapshot (contrato chat-session-context §4.2)."""

    device_id: str
    device_name: str | None = None
    device_type: DeviceType
    adopted_at: str
    operation_status: str | None = None
    last_seen_at: str | None = None
    last_command: dict | None = None
    last_command_at: str | None = None
    last_reported_state: dict | None = None


class ConversationContext(BaseModel):
    """Estado de sessão para resolver e foco."""

    schema_version: int = 1
    updated_at: str
    session_focus_device_id: str | None = None
    focus_reason: FocusReason | None = None
    device_count: int = 0
    sensor_count: int = 0
    actuator_count: int = 0
    device_snapshot: list[DeviceSnapshotEntry] = Field(default_factory=list)
    pending_actuator_command: PendingActuatorCommand | None = None


class ClarifyOption(BaseModel):
    """Opção apresentada ao usuário (clarificação)."""

    device_id: str
    device_name: str | None = None
    device_type: DeviceType
