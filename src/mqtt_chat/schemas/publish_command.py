"""Schemas da tool MCP publish_command."""

from __future__ import annotations

from pydantic import BaseModel, Field

from mqtt_chat.schemas.actuator_command import ActuatorSetCommandPayload, BinaryActuatorValue


class PublishCommandInput(BaseModel):
    """Parâmetros para publicar comando binário em atuador."""

    device_id: str = Field(min_length=1, max_length=128)
    value: BinaryActuatorValue
    channel: int = Field(default=1, ge=1, le=32)


class PublishCommandResult(BaseModel):
    """Confirmação após publish MQTT + persistência last_command*."""

    device_id: str
    topic_suffix: str = "commands"
    payload: ActuatorSetCommandPayload
    last_command_at: str
