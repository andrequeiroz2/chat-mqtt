"""Persistência de telemetria e metadados de device (Firestore ou log PoC)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from mqtt_chat.config.settings import Settings
from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.telemetry import ReadingItem, StatusPayload, TelemetryPayload
from mqtt_chat.services import realtime_broadcast
from mqtt_chat.worker.topics import ParsedDeviceTopic

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient

logger = logging.getLogger(__name__)

LAST_REPORTED_STATE_MAX_BYTES = 2048


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


async def persist_telemetry(
    parsed: ParsedDeviceTopic,
    payload_bytes: bytes,
    settings: Settings,
    db: FirestoreClient | None,
) -> None:
    """Grava telemetria normalizada; falha logada, não propaga."""
    try:
        data = json.loads(payload_bytes.decode("utf-8"))
        telemetry = TelemetryPayload.model_validate(data)
    except (json.JSONDecodeError, ValueError) as exc:
        log_event(
            logger,
            logging.WARNING,
            events.TELEMETRY_PARSE_FAILED,
            "Invalid telemetry JSON",
            mqtt_topic_base=parsed.mqtt_topic_base,
            error=str(exc),
        )
        return

    readings = telemetry.expanded_readings()
    if not readings:
        logger.debug("Empty telemetry topic=%s", parsed.mqtt_topic_base)
        return

    received_at = _now_iso()
    device_ts = telemetry.ts or received_at

    log_event(
        logger,
        logging.DEBUG,
        events.TELEMETRY_PARSE_COMPLETED,
        "Telemetry parsed",
        user_id=parsed.user_id,
        device_id=parsed.device_id,
        readings_count=len(readings),
        device_ts=device_ts,
    )

    if settings.worker_persist_mode == "log" or db is None:
        log_event(
            logger,
            logging.INFO,
            events.TELEMETRY_PERSIST_COMPLETED,
            "Telemetry persisted (log mode)",
            user_id=parsed.user_id,
            device_id=parsed.device_id,
            readings_count=len(readings),
            persist_mode="log",
        )
        await realtime_broadcast.broadcast_telemetry(
            parsed,
            readings,
            device_ts=device_ts,
            received_at=received_at,
        )
        return

    try:
        _write_telemetry_firestore(db, parsed, readings, device_ts, received_at)
    except Exception:
        log_event(
            logger,
            logging.ERROR,
            events.TELEMETRY_PERSIST_FAILED,
            "Firestore telemetry write failed",
            user_id=parsed.user_id,
            device_id=parsed.device_id,
            exc_info=True,
        )
        return

    log_event(
        logger,
        logging.INFO,
        events.TELEMETRY_PERSIST_COMPLETED,
        "Telemetry persisted",
        user_id=parsed.user_id,
        device_id=parsed.device_id,
        readings_count=len(readings),
        persist_mode="firestore",
    )
    await realtime_broadcast.broadcast_telemetry(
        parsed,
        readings,
        device_ts=device_ts,
        received_at=received_at,
    )


def _write_telemetry_firestore(
    db: FirestoreClient,
    parsed: ParsedDeviceTopic,
    readings: list[ReadingItem],
    device_ts: str,
    received_at: str,
) -> None:
    device_ref = db.collection("devices").document(parsed.device_id)
    batch = db.batch()
    telem_col = device_ref.collection("telemetry")

    for item in readings:
        doc_ref = telem_col.document()
        batch.set(
            doc_ref,
            {
                "user_id": parsed.user_id,
                "device_id": parsed.device_id,
                "mqtt_topic_base": parsed.mqtt_topic_base,
                "metric": item.metric,
                "value": item.value,
                "unit": item.unit,
                "device_ts": device_ts,
                "received_at": received_at,
            },
        )

    batch.set(
        device_ref,
        {
            "user_id": parsed.user_id,
            "device_id": parsed.device_id,
            "mqtt_topic_base": parsed.mqtt_topic_base,
            "last_seen_at": received_at,
        },
        merge=True,
    )
    batch.commit()


async def persist_status(
    parsed: ParsedDeviceTopic,
    payload_bytes: bytes,
    settings: Settings,
    db: FirestoreClient | None,
) -> None:
    """Atualiza operation_status / last_seen."""
    try:
        data = json.loads(payload_bytes.decode("utf-8"))
        status = StatusPayload.model_validate(data)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Invalid status JSON topic=%s error=%s", parsed.mqtt_topic_base, exc)
        return

    received_at = _now_iso()
    op = status.operation_status

    if settings.worker_persist_mode == "log" or db is None:
        logger.info(
            "status user_id=%s device_id=%s operation_status=%s ts=%s",
            parsed.user_id,
            parsed.device_id,
            op,
            status.ts or received_at,
        )
        await realtime_broadcast.broadcast_device_status(
            parsed,
            operation_status=op,
            last_seen_at=received_at,
        )
        return

    device_ref = db.collection("devices").document(parsed.device_id)
    patch: dict = {
        "user_id": parsed.user_id,
        "device_id": parsed.device_id,
        "mqtt_topic_base": parsed.mqtt_topic_base,
        "last_seen_at": received_at,
    }
    if op is not None:
        patch["operation_status"] = op
    device_ref.set(patch, merge=True)
    await realtime_broadcast.broadcast_device_status(
        parsed,
        operation_status=op,
        last_seen_at=received_at,
    )


def summarize_state_payload(raw: dict) -> dict:
    """
    Reduz payload MQTT state para `last_reported_state` (cap 2 KiB — contrato 011-d).

    Precedência na copy TomatoIA: `last_command` (plataforma) descreve intenção enviada;
    `last_reported_state` reflete ACK/estado reportado pelo firmware.
    """
    encoded = json.dumps(raw, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) <= LAST_REPORTED_STATE_MAX_BYTES:
        return raw
    slim_keys = ("action", "channel", "value", "state", "status", "command_id")
    slim = {k: raw[k] for k in slim_keys if k in raw}
    slim["_truncated"] = True
    return slim


async def persist_state(
    parsed: ParsedDeviceTopic,
    payload_bytes: bytes,
    settings: Settings,
    db: FirestoreClient | None,
) -> None:
    """Persiste state MQTT em evento + espelho `last_reported_state` no device."""
    received_at = _now_iso()
    try:
        raw = json.loads(payload_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Invalid state JSON topic=%s error=%s", parsed.mqtt_topic_base, exc)
        return

    if not isinstance(raw, dict):
        logger.warning("Invalid state payload (not object) topic=%s", parsed.mqtt_topic_base)
        return

    summary = summarize_state_payload(raw)

    if settings.worker_persist_mode == "log" or db is None:
        logger.info(
            "state user_id=%s device_id=%s payload=%s",
            parsed.user_id,
            parsed.device_id,
            summary,
        )
        return

    device_ref = db.collection("devices").document(parsed.device_id)
    device_ref.collection("state_events").add(
        {
            "user_id": parsed.user_id,
            "device_id": parsed.device_id,
            "payload": raw,
            "received_at": received_at,
        }
    )
    device_ref.set(
        {
            "user_id": parsed.user_id,
            "device_id": parsed.device_id,
            "mqtt_topic_base": parsed.mqtt_topic_base,
            "last_seen_at": received_at,
            "last_reported_state": summary,
            "last_reported_state_at": received_at,
        },
        merge=True,
    )
    log_event(
        logger,
        logging.INFO,
        events.DEVICE_METADATA_UPDATED,
        "Device last_reported_state updated",
        user_id=parsed.user_id,
        device_id=parsed.device_id,
    )
