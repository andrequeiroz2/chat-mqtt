"""Schemas de listagem de devices (MCP / services)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DeviceType = Literal["sensor", "actuator"]
DeviceNameMatch = Literal["contains", "exact"]


class ListDevicesInput(BaseModel):
    """Filtros opcionais para list_devices (contrato mcp-list-devices.md §3)."""

    device_type: DeviceType | None = None
    device_name: str | None = Field(default=None, max_length=120)
    device_name_match: DeviceNameMatch = "contains"
    device_id: str | None = Field(default=None, max_length=128)
    limit: int = Field(default=50, ge=1, le=100)
    cursor: str | None = None


class DeviceSummary(BaseModel):
    """Resumo exposto ao LLM (sem secrets MQTT)."""

    device_id: str
    device_name: str | None
    device_type: DeviceType
    model: str
    sensor_type: str | None = None
    actuator_type: str | None = None
    firmware_version: str | None = None
    operation_status: str | None = None
    last_seen_at: str | None = None
    adopted_at: str


class ListDevicesResult(BaseModel):
    """Resposta paginada de list_devices."""

    devices: list[DeviceSummary]
    total_returned: int
    has_more: bool
    next_cursor: str | None = None
