"""Consultas de telemetria (MCP / agente) — somente leitura Firestore."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from google.cloud.firestore_v1 import Client as FirestoreClient

from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.chat import TelemetryChartPoint, TelemetryChartSuggestedUi
from mqtt_chat.schemas.devices import ListDevicesInput
from mqtt_chat.schemas.telemetry import ReadingItem
from mqtt_chat.schemas.telemetry_tools import (
    Connectivity,
    GetTelemetryHistoryResult,
    ReadLatestTelemetryInput,
    ReadLatestTelemetryResult,
    TelemetryHistoryInput,
)
from mqtt_chat.services import devices as devices_service
from mqtt_chat.services.device_intent_resolver import connectivity_from_status

logger = logging.getLogger(__name__)

_HISTORY_SCAN_LIMIT = 3000
_CHART_MAX_POINTS = 500


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
    device_id, device_name, _, _, _, _ = _resolve_device_id(db, user_id, params)
    return device_id, device_name


def _presence_from_doc(data: dict[str, Any]) -> tuple[str | None, str | None, Connectivity]:
    op = data.get("operation_status")
    operation_status = op if isinstance(op, str) else None
    last_raw = data.get("last_seen_at")
    last_seen_at = last_raw if isinstance(last_raw, str) else None
    return operation_status, last_seen_at, connectivity_from_status(operation_status)


def _resolve_device_id(
    db: FirestoreClient,
    user_id: str,
    params: ReadLatestTelemetryInput,
) -> tuple[str, str | None, str, str | None, str | None, Connectivity]:
    """Retorna (device_id, device_name, device_type, operation_status, last_seen_at, connectivity)."""
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
        op, last_seen, conn = _presence_from_doc(data)
        return (
            str(data.get("device_id") or snap.id),
            data.get("device_name"),
            device_type,
            op,
            last_seen,
            conn,
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
        snap = db.collection("devices").document(dev.device_id).get()
        data = snap.to_dict() if snap.exists else {}
        op, last_seen, conn = _presence_from_doc(data or {})
        return dev.device_id, dev.device_name, dev.device_type, op, last_seen, conn

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
    snap = db.collection("devices").document(dev.device_id).get()
    data = snap.to_dict() if snap.exists else {}
    op, last_seen, conn = _presence_from_doc(data or {})
    return dev.device_id, dev.device_name, dev.device_type, op, last_seen, conn


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
    device_id, device_name, device_type, operation_status, last_seen_at, connectivity = (
        _resolve_device_id(db, user_id, params)
    )
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
        connectivity=connectivity,
    )

    return ReadLatestTelemetryResult(
        device_id=device_id,
        device_name=device_name,
        device_type=device_type,  # type: ignore[arg-type]
        device_ts=device_ts,
        received_at=received_at,
        readings=readings,
        has_telemetry=bool(readings),
        operation_status=operation_status,
        last_seen_at=last_seen_at,
        connectivity=connectivity,
    )


def get_telemetry_history(
    db: FirestoreClient,
    user_id: str,
    params: TelemetryHistoryInput,
) -> tuple[GetTelemetryHistoryResult, TelemetryChartSuggestedUi | None]:
    """
    Série temporal para gráfico no chat.

    Raises:
        ReadLatestTelemetryError: resolução de device ou telemetry_history_empty.
    """
    read_params = ReadLatestTelemetryInput(
        device_id=params.device_id,
        device_name=params.device_name,
        device_name_match=params.device_name_match,
    )
    device_id, device_name, _, _, _, _ = _resolve_device_id(db, user_id, read_params)

    cutoff = datetime.now(UTC) - timedelta(days=params.days)
    cutoff_str = cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    telem_ref = db.collection("devices").document(device_id).collection("telemetry")
    query = telem_ref.order_by("received_at", direction="DESCENDING").limit(_HISTORY_SCAN_LIMIT)

    raw_rows: list[tuple[str, str, float, str | None]] = []
    for snap in query.stream():
        data = snap.to_dict() or {}
        received_at = data.get("received_at")
        if not isinstance(received_at, str):
            continue
        if received_at < cutoff_str:
            break
        metric = data.get("metric")
        value = data.get("value")
        if metric is None or value is None:
            continue
        try:
            raw_rows.append((received_at, str(metric), float(value), data.get("unit")))
        except (TypeError, ValueError):
            continue

    if not raw_rows:
        raise ReadLatestTelemetryError("telemetry_history_empty")

    target_metric = params.metric.strip() if params.metric else None
    if not target_metric:
        counts: dict[str, int] = {}
        for _, metric, _, _ in raw_rows:
            counts[metric] = counts.get(metric, 0) + 1
        target_metric = max(counts, key=counts.get)

    series = [(rec, val, unit) for rec, metric, val, unit in raw_rows if metric == target_metric]
    if not series:
        raise ReadLatestTelemetryError("telemetry_history_empty")

    unit: str | None = next((u for _, _, u in series if isinstance(u, str) and u), None)
    series.sort(key=lambda row: row[0])

    if params.last_day_with_data and series:
        last_received = max(rec for rec, _, _ in series)
        day_prefix = last_received[:10]
        series = [(rec, val, u) for rec, val, u in series if rec[:10] == day_prefix]
        if not series:
            raise ReadLatestTelemetryError("telemetry_history_empty")

    if len(series) > _CHART_MAX_POINTS:
        step = len(series) / _CHART_MAX_POINTS
        series = [series[int(i * step)] for i in range(_CHART_MAX_POINTS)]

    chart_points = [TelemetryChartPoint(received_at=rec, value=val) for rec, val, _ in series]
    values = [point.value for point in chart_points]
    period_label = "1d-last" if params.last_day_with_data else f"{params.days}d"

    log_event(
        logger,
        logging.INFO,
        events.MCP_TOOL_READ_LATEST_TELEMETRY,
        "get_telemetry_history completed",
        user_id=user_id,
        device_id=device_id,
        metric=target_metric,
        point_count=len(chart_points),
    )

    chart_ui = TelemetryChartSuggestedUi(
        device_id=device_id,
        device_name=device_name,
        metric=target_metric,
        unit=unit,
        period_label=period_label,
        points=chart_points,
    )
    result = GetTelemetryHistoryResult(
        device_id=device_id,
        device_name=device_name,
        metric=target_metric,
        unit=unit,
        period_label=period_label,
        point_count=len(chart_points),
        min_value=min(values),
        max_value=max(values),
        latest_value=values[-1],
        has_data=True,
    )
    return result, chart_ui
