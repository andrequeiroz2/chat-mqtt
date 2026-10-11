"""Payloads de telemetria e presença (contrato §6)."""

from pydantic import BaseModel, ConfigDict


class ReadingItem(BaseModel):
    """Uma leitura dentro de telemetria multi-métrica."""

    metric: str
    value: float
    unit: str | None = None


class TelemetryPayload(BaseModel):
    """Telemetria: single-metric (PoC) ou array readings (v1.1)."""

    ts: str | None = None
    metric: str | None = None
    value: float | None = None
    unit: str | None = None
    readings: list[ReadingItem] | None = None

    def expanded_readings(self) -> list[ReadingItem]:
        """Normaliza para lista de leituras."""
        if self.readings:
            return self.readings
        if self.metric is not None and self.value is not None:
            return [ReadingItem(metric=self.metric, value=self.value, unit=self.unit)]
        return []


class StatusPayload(BaseModel):
    """Presença em .../status."""

    ts: str | None = None
    operation_status: str | None = None


class StatePayload(BaseModel):
    """Estado / ACK em .../state (campos extras permitidos)."""

    model_config = ConfigDict(extra="allow")

    ts: str | None = None
