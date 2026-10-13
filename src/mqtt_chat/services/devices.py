"""Listagem de devices adotados (fonte única MCP + futuro agente)."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from typing import Any

from google.cloud.firestore_v1 import Client as FirestoreClient

from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.devices import DeviceSummary, ListDevicesInput, ListDevicesResult

logger = logging.getLogger(__name__)

_ADOPTED = "adopted"


class ListDevicesError(Exception):
    """Erro de validação ou cursor na listagem."""

    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        super().__init__(message or code)


def _normalize_name(value: str | None) -> str:
    return (value or "").strip().casefold()


def _filters_fingerprint(params: ListDevicesInput) -> str:
    payload = {
        "device_type": params.device_type,
        "device_name": params.device_name,
        "device_name_match": params.device_name_match,
        "device_id": params.device_id,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def _encode_cursor(
    *,
    last_device_id: str,
    last_device_name: str | None,
    filters_hash: str,
) -> str:
    body = {
        "last_device_id": last_device_id,
        "last_device_name": last_device_name,
        "filters_hash": filters_hash,
    }
    raw = json.dumps(body, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_cursor(cursor: str, *, expected_hash: str) -> tuple[str, str | None]:
    try:
        pad = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(cursor + pad)
        body = json.loads(raw.decode())
        if body.get("filters_hash") != expected_hash:
            raise ListDevicesError("invalid_cursor")
        last_id = body.get("last_device_id")
        if not isinstance(last_id, str) or not last_id:
            raise ListDevicesError("invalid_cursor")
        last_name = body.get("last_device_name")
        if last_name is not None and not isinstance(last_name, str):
            raise ListDevicesError("invalid_cursor")
        return last_id, last_name
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        raise ListDevicesError("invalid_cursor") from exc


def _doc_to_summary(data: dict[str, Any], doc_id: str) -> DeviceSummary | None:
    if data.get("adoption_status") not in (None, _ADOPTED):
        return None
    device_type = data.get("device_type")
    if device_type not in ("sensor", "actuator"):
        return None
    adopted_at = data.get("adopted_at") or data.get("created_at")
    if not adopted_at:
        return None
    model = data.get("model") or "unknown"
    return DeviceSummary(
        device_id=str(data.get("device_id") or doc_id),
        device_name=data.get("device_name"),
        device_type=device_type,
        model=str(model),
        sensor_type=data.get("sensor_type"),
        actuator_type=data.get("actuator_type"),
        firmware_version=data.get("firmware_version"),
        operation_status=data.get("operation_status"),
        last_seen_at=data.get("last_seen_at"),
        adopted_at=str(adopted_at),
    )


def _name_matches(
    device_name: str | None,
    *,
    needle: str,
    match: str,
) -> bool:
    hay = _normalize_name(device_name)
    n = _normalize_name(needle)
    if not n:
        return True
    if match == "exact":
        return hay == n
    return n in hay


def _sort_key(item: DeviceSummary) -> tuple[str, str]:
    return (_normalize_name(item.device_name), item.device_id.casefold())


def _load_candidates(
    db: FirestoreClient,
    user_id: str,
    params: ListDevicesInput,
) -> list[DeviceSummary]:
    if params.device_id:
        snap = db.collection("devices").document(params.device_id).get()
        if not snap.exists:
            return []
        data = snap.to_dict() or {}
        if data.get("user_id") != user_id:
            return []
        summary = _doc_to_summary(data, snap.id)
        return [summary] if summary else []

    query = db.collection("devices").where("user_id", "==", user_id)
    if params.device_type:
        query = query.where("device_type", "==", params.device_type)

    items: list[DeviceSummary] = []
    for snap in query.stream():
        data = snap.to_dict() or {}
        summary = _doc_to_summary(data, snap.id)
        if summary is None:
            continue
        if params.device_name and not _name_matches(
            summary.device_name,
            needle=params.device_name,
            match=params.device_name_match,
        ):
            continue
        items.append(summary)

    items.sort(key=_sort_key)
    return items


def list_devices(
    db: FirestoreClient,
    user_id: str,
    params: ListDevicesInput,
) -> ListDevicesResult:
    """
    Lista devices adotados do usuário com filtros e paginação por cursor.

    Raises:
        ListDevicesError: cursor inválido ou device_name só espaços.
    """
    if params.device_name is not None and not params.device_name.strip():
        raise ListDevicesError("invalid_device_name")

    filters_hash = _filters_fingerprint(params)
    candidates = _load_candidates(db, user_id, params)

    start_index = 0
    if params.cursor:
        last_id, last_name = _decode_cursor(params.cursor, expected_hash=filters_hash)
        cursor_key = (_normalize_name(last_name), last_id.casefold())
        for idx, item in enumerate(candidates):
            if _sort_key(item) > cursor_key:
                start_index = idx
                break
        else:
            start_index = len(candidates)

    page = candidates[start_index : start_index + params.limit]
    has_more = start_index + params.limit < len(candidates)
    next_cursor: str | None = None
    if has_more and page:
        last = page[-1]
        next_cursor = _encode_cursor(
            last_device_id=last.device_id,
            last_device_name=last.device_name,
            filters_hash=filters_hash,
        )

    log_event(
        logger,
        logging.INFO,
        events.MCP_TOOL_LIST_DEVICES,
        "list_devices completed",
        user_id=user_id,
        total_returned=len(page),
        has_more=has_more,
        device_type=params.device_type,
        filtered_by_name=bool(params.device_name),
    )

    return ListDevicesResult(
        devices=page,
        total_returned=len(page),
        has_more=has_more,
        next_cursor=next_cursor,
    )
