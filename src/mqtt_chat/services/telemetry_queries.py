"""Consultas de telemetria (MCP / agente) — somente leitura Firestore."""

from __future__ import annotations

import logging
from typing import Any

from google.cloud.firestore_v1 import Client as FirestoreClient

from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.devices import ListDevicesInput
from mqtt_chat.schemas.telemetry import ReadingItem
from mqtt_chat.schemas.telemetry_tools import ReadLatestTelemetryInput, ReadLatestTelemetryResult
from mqtt_chat.services import devices as devices_service

logger = logging.getLogger(__name__)


class ReadLatestTelemetryError(Exception):
    """Erro de resolução de device ou consulta."""

    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        super().__init__(message or code)


def resolve_device_for_telemetry(
    db: FirestoreClient,
    user_id: str,
    params: ReadLatestTelemetryInput,
) -> tuple[str, str | None]:
    """Resolve device_id e device_name para telemetria (MCP / agente)."""
    device_id, device_name, _ = _resolve_device_id(db, user_id, params)
    return device_id, device_name


def _resolve_device_id(
    db: FirestoreClient,
    user_id: str,
    params: ReadLatestTelemetryInput,
) -> tuple[str, str | None, str]:
    """Retorna (device_id, device_name, device_type)."""
    if params.device_id:
        snap = db.collection("devices").document(params.device_id).get()
        if not snap.exists:
            raise ReadLatestTelemetryError("device_not_found")
        data = snap.to_dict() or {}
        if data.get("user_id") != user_id:
            raise ReadLatestTelemetryError("device_not_found")
        device_type = data.get("device_type")
        if device_type not in ("sensor", "actuator"):
            raise ReadLatestTelemetryError("device_not_found")
        return (
            str(data.get("device_id") or snap.id),
            data.get("device_name"),
            device_type,
        )

    if params.device_name and not params.device_name.strip():
        raise ReadLatestTelemetryError("device_not_found")

    if params.device_name:
        listed = devices_service.list_devices(
            db,
            user_id,
            ListDevicesInput(
                device_name=params.device_name,
                device_name_match=params.device_name_match,
                limit=2,
            ),
        )
        if listed.total_returned == 0:
            raise ReadLatestTelemetryError("device_not_found")
        if listed.total_returned > 1 or listed.has_more:
            raise ReadLatestTelemetryError("device_ambiguous")
        dev = listed.devices[0]
        return dev.device_id, dev.device_name, dev.device_type

    listed = devices_service.list_devices(
        db,
        user_id,
        ListDevicesInput(limit=2),
    )
    if listed.total_returned == 0:
        raise ReadLatestTelemetryError("device_not_found")
    if listed.total_returned > 1 or listed.has_more:
        raise ReadLatestTelemetryError("device_required")
    dev = listed.devices[0]
    return dev.device_id, dev.device_name, dev.device_type


def _latest_readings_batch(
    db: FirestoreClient,
    device_id: str,
    *,
    scan_limit: int = 32,
) -> tuple[str | None, str | None, list[ReadingItem]]:
    """
    Busca documentos mais recentes e agrupa pelo `received_at` do primeiro.

    Retorna (device_ts, received_at, readings).
    """
    telem_ref = db.collection("devices").document(device_id).collection("telemetry")
    query = telem_ref.order_by("received_at", direction="DESCENDING").limit(scan_limit)
    docs = list(query.stream())
    if not docs:
        return None, None, []

    first = docs[0].to_dict() or {}
    anchor_received = first.get("received_at")
    if not anchor_received:
        return None, None, []

    readings: list[ReadingItem] = []
    device_ts: str | None = None
    for snap in docs:
        data = snap.to_dict() or {}
        if data.get("received_at") != anchor_received:
            break
        metric = data.get("metric")
        value = data.get("value")
        if metric is None or value is None:
            continue
        if device_ts is None:
            device_ts = data.get("device_ts")
        try:
            readings.append(
                ReadingItem(
                    metric=str(metric),
                    value=float(value),
                    unit=data.get("unit"),
                )
            )
        except (TypeError, ValueError):
            continue

    return device_ts, str(anchor_received), readings


def read_latest_telemetry(
    db: FirestoreClient,
    user_id: str,
    params: ReadLatestTelemetryInput,
) -> ReadLatestTelemetryResult:
    """
    Último lote de telemetria de um device adotado do usuário.

    Raises:
        ReadLatestTelemetryError: device_not_found, device_ambiguous, device_required.
    """
    device_id, device_name, device_type = _resolve_device_id(db, user_id, params)
    device_ts, received_at, readings = _latest_readings_batch(db, device_id)

    log_event(
        logger,
        logging.INFO,
        events.MCP_TOOL_READ_LATEST_TELEMETRY,
        "read_latest_telemetry completed",
        user_id=user_id,
        device_id=device_id,
        readings_count=len(readings),
        has_telemetry=bool(readings),
    )

    return ReadLatestTelemetryResult(
        device_id=device_id,
        device_name=device_name,
        device_type=device_type,  # type: ignore[arg-type]
        device_ts=device_ts,
        received_at=received_at,
        readings=readings,
        has_telemetry=bool(readings),
    )
