"""Schemas da tool MCP read_latest_telemetry."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from mqtt_chat.schemas.telemetry import ReadingItem

Connectivity = Literal["online", "offline", "unknown"]


class ReadLatestTelemetryInput(BaseModel):
    """Parâmetros opcionais para localizar o device."""

    device_id: str | None = None
    device_name: str | None = None
    device_name_match: Literal["contains", "exact"] = "contains"


class StartRealtimeTelemetryResult(BaseModel):
    """Confirmação para o LLM após pedido de stream ao vivo no chat."""

    device_id: str
    device_name: str | None = None


class TelemetryHistoryInput(BaseModel):
    """Parâmetros para histórico / gráfico."""

    device_id: str | None = None
    device_name: str | None = None
    device_name_match: Literal["contains", "exact"] = "contains"
    metric: str | None = None
    days: int = Field(default=7, ge=1, le=30)
    """Se True, restringe ao dia calendário (UTC) da leitura mais recente no scan."""
    last_day_with_data: bool = False


class GetTelemetryHistoryResult(BaseModel):
    """Resumo para o LLM após consulta de histórico."""

    device_id: str
    device_name: str | None = None
    metric: str
    unit: str | None = None
    period_label: str
    point_count: int = 0
    min_value: float | None = None
    max_value: float | None = None
    latest_value: float | None = None
    has_data: bool = False


class ReadLatestTelemetryResult(BaseModel):
    """Último lote de leituras persistidas para um device."""

    device_id: str
    device_name: str | None = None
    device_type: Literal["sensor", "actuator"]
    device_ts: str | None = None
    received_at: str | None = None
    readings: list[ReadingItem] = Field(default_factory=list)
    has_telemetry: bool = False
    operation_status: str | None = None
    last_seen_at: str | None = None
    connectivity: Connectivity = "unknown"
