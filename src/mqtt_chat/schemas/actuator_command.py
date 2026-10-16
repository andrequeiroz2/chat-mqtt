"""Comando binário de atuador (MQTT 0/1)."""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

BinaryActuatorValue = Literal[0, 1]
PowerIntent = Literal["on", "off"]


class PendingActuatorCommand(BaseModel):
    """Comando aguardando confirmação do usuário (sessão de chat)."""

    device_id: str
    device_name: str | None = None
    binary_value: BinaryActuatorValue
    verb_pt: str = Field(min_length=1, max_length=32)


class ActuatorSetCommandPayload(BaseModel):
    """Payload publicado em `{mqtt_topic_base}/commands`."""

    action: Literal["set"] = "set"
    channel: int = Field(default=1, ge=1, le=32)
    value: BinaryActuatorValue
    command_id: str = Field(default_factory=lambda: str(uuid4()))
