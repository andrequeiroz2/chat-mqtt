"""Payloads de telemetria e presença (contrato §6)."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReadingItem(BaseModel):
    """Uma leitura dentro de telemetria multi-métrica.

    Task 017: `unit` é obrigatório (string não vazia após trim) — sem vocabulário
    fechado de unidades.
    """

    metric: str
    value: float
    unit: str = Field(..., min_length=1)

    @field_validator("unit")
    @classmethod
    def unit_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("unit must be a non-empty string")
        return v


class TelemetryPayload(BaseModel):
    """Telemetria: single-metric (PoC) ou array readings (v1.1).

    O worker deve validar leituras individualmente: itens sem `unit` válido são
    descartados (task 017), não o payload inteiro.
    """

    ts: str | None = None
    metric: str | None = None
    value: float | None = None
    unit: str | None = None
    # O worker valida cada item contra ReadingItem; aqui mantemos dicts para
    # não rejeitar o lote inteiro quando só uma leitura está sem `unit` (task 017).
    readings: list[dict] | None = None

    def expanded_readings(self) -> list[ReadingItem]:
        """Normaliza para lista de leituras (apenas single-metric legado)."""
        if self.readings:
            return [r for r in (self._try_reading(item) for item in self.readings) if r is not None]
        if self.metric is not None and self.value is not None and self.unit is not None:
            return [ReadingItem(metric=self.metric, value=self.value, unit=self.unit)]
        return []

    @staticmethod
    def _try_reading(raw: dict) -> ReadingItem | None:
        try:
            return ReadingItem.model_validate(raw)
        except ValueError:
            return None


class StatusPayload(BaseModel):
    """Presença em .../status."""

    ts: str | None = None
    operation_status: str | None = None


class StatePayload(BaseModel):
    """Estado / ACK em .../state (campos extras permitidos)."""

    model_config = ConfigDict(extra="allow")

    ts: str | None = None
