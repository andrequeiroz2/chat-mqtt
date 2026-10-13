"""Orquestração handshake MQTT UC-A (v1.2-dev)."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from google.cloud.firestore_v1 import Client as FirestoreClient
from pydantic import ValidationError

from mqtt_chat.config.settings import Settings
from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.adoption import (
    AdoptionAckMqttPayload,
    AdoptionChallengeMqttPayload,
    AdoptionConfigMqttPayload,
    AdoptionSessionResponse,
    AdoptionStartRequest,
    DeviceInfoMqttPayload,
)
from mqtt_chat.services.adoption import mqtt_topics, session_store
from mqtt_chat.validators.mac_address import InvalidMacAddressError, normalize_mac_address

logger = logging.getLogger(__name__)


def _broker_url(settings: Settings) -> str:
    return f"mqtt://{settings.mqtt_host}:{settings.mqtt_port}"


def _validate_device_info(payload: DeviceInfoMqttPayload) -> str | None:
    """Retorna failure_reason ou None se OK."""
    if payload.adopted_status == 1 and payload.user_id:
        return None  # re-adopt policy handled elsewhere
    if payload.device_type == "sensor":
        if not payload.parameter_ranges:
            return "contract_rejected"
    elif payload.device_type == "actuator":
        if not payload.command_spec:
            return "contract_rejected"
    return None


async def start_adoption(
    db: FirestoreClient,
    settings: Settings,
    publish_queue: asyncio.Queue[tuple[str, bytes]],
    *,
    user_id: str,
    body: AdoptionStartRequest,
) -> AdoptionSessionResponse:
    """POST adopt/start — elegibilidade, sessão, challenge MQTT."""
    try:
        mac = normalize_mac_address(body.mac_address)
    except InvalidMacAddressError as exc:
        raise ValueError("invalid_mac_address") from exc

    existing = session_store.find_device_by_mac(db, mac)
    if existing and existing.get("user_id") and existing.get("user_id") != user_id:
        raise PermissionError("ownership_conflict")

    session_id, doc = session_store.create_session(
        db,
        settings,
        user_id=user_id,
        mac_address=mac,
        device_name=body.device_name,
    )

    challenge = AdoptionChallengeMqttPayload(
        session_id=session_id,
        nonce=doc["nonce"],
    )
    topic = mqtt_topics.unclaimed_topic(mac, "challenge")
    await publish_queue.put((topic, challenge.model_dump_json().encode("utf-8")))

    return AdoptionSessionResponse(
        session_id=session_id,
        session_status="started",
        mac_address=mac,
        expires_at=doc["expires_at"],
        device_name=body.device_name,
    )


async def handle_info_message(
    db: FirestoreClient,
    settings: Settings,
    publish_queue: asyncio.Queue[tuple[str, bytes]],
    *,
    topic_mac: str,
    payload_bytes: bytes,
) -> None:
    """Processa `{unclaimed}/info` publicado pelo device/simulador."""
    try:
        raw = json.loads(payload_bytes.decode("utf-8"))
        info = DeviceInfoMqttPayload.model_validate(raw)
    except (json.JSONDecodeError, ValidationError):
        log_event(
            logger,
            logging.WARNING,
            events.ADOPTION_MQTT_INFO,
            "Invalid adoption info payload",
        )
        return

    session = session_store.get_session(db, info.session_id)
    if session is None:
        return
    session = session_store.expire_if_needed(db, session)
    if session.get("session_status") not in session_store.ACTIVE_STATUSES:
        return

    session_mac = normalize_mac_address(session["mac_address"])
    if normalize_mac_address(info.mac_address) != session_mac:
        session_store.fail_session(db, info.session_id, failure_reason="mac_mismatch")
        return
    if topic_mac != session_mac:
        session_store.fail_session(db, info.session_id, failure_reason="mac_mismatch")
        return

    if info.adopted_status == 1 and info.user_id and info.user_id != session["user_id"]:
        session_store.fail_session(db, info.session_id, failure_reason="ownership_conflict")
        return

    contract_err = _validate_device_info(info)
    if contract_err:
        session_store.fail_session(db, info.session_id, failure_reason=contract_err)
        return

    user_id = session["user_id"]
    device_id = session["proposed_device_id"]
    topic_base = mqtt_topics.proposed_mqtt_topic_base(user_id, device_id)

    config = AdoptionConfigMqttPayload(
        session_id=info.session_id,
        nonce=session["nonce"],
        user_id=user_id,
        device_id=device_id,
        device_name=session.get("device_name") or "Meu dispositivo",
        mqtt_topic_base=topic_base,
        broker_url=_broker_url(settings),
        mqtt_username=settings.mqtt_username,
        mqtt_password=settings.mqtt_password,
    )

    config_topic = mqtt_topics.unclaimed_topic(session_mac, "config")
    await publish_queue.put((config_topic, config.model_dump_json().encode("utf-8")))

    session_store.update_session(
        db,
        info.session_id,
        {
            "session_status": "device_verified",
            "device_info_candidate": info.model_dump(),
            "contract_validation": {"ok": True},
            "proposed_mqtt_topic_base": topic_base,
        },
    )
    session_store.update_session(
        db,
        info.session_id,
        {"session_status": "awaiting_device_ack"},
    )
    log_event(
        logger,
        logging.INFO,
        events.ADOPTION_MQTT_INFO,
        "Adoption config sent",
        session_id=info.session_id,
        user_id=user_id,
    )


async def handle_ack_message(
    db: FirestoreClient,
    *,
    topic_mac: str,
    payload_bytes: bytes,
) -> None:
    """Processa `{unclaimed}/ack` — commit em devices."""
    try:
        raw = json.loads(payload_bytes.decode("utf-8"))
        ack = AdoptionAckMqttPayload.model_validate(raw)
    except (json.JSONDecodeError, ValidationError):
        log_event(
            logger,
            logging.WARNING,
            events.ADOPTION_MQTT_ACK,
            "Invalid adoption ack payload",
        )
        return

    session = session_store.get_session(db, ack.session_id)
    if session is None:
        return
    session = session_store.expire_if_needed(db, session)
    if session.get("session_status") != "awaiting_device_ack":
        session_store.fail_session(db, ack.session_id, failure_reason="invalid_ack")
        return

    session_mac = normalize_mac_address(session["mac_address"])
    if normalize_mac_address(ack.mac_address) != session_mac or topic_mac != session_mac:
        session_store.fail_session(db, ack.session_id, failure_reason="mac_mismatch")
        return
    if ack.nonce != session.get("nonce"):
        session_store.fail_session(db, ack.session_id, failure_reason="invalid_ack")
        return
    if ack.status != "adoption_complete":
        session_store.fail_session(db, ack.session_id, failure_reason="invalid_ack")
        return

    existing = session_store.find_device_by_mac(db, session_mac)
    user_id = session["user_id"]
    if existing and existing.get("user_id") not in (None, user_id):
        session_store.fail_session(db, ack.session_id, failure_reason="ownership_conflict")
        return

    info_data = session.get("device_info_candidate") or {}
    device_id = session["proposed_device_id"]
    topic_base = session.get("proposed_mqtt_topic_base") or mqtt_topics.proposed_mqtt_topic_base(
        user_id, device_id
    )
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    device_doc: dict[str, Any] = {
        "device_id": device_id,
        "user_id": user_id,
        "mac_address": session_mac,
        "mqtt_topic_base": topic_base,
        "device_type": info_data.get("device_type", "sensor"),
        "model": info_data.get("model", "unknown"),
        "sensor_type": info_data.get("sensor_type"),
        "actuator_type": info_data.get("actuator_type"),
        "parameter_ranges": info_data.get("parameter_ranges"),
        "command_spec": info_data.get("command_spec"),
        "firmware_version": ack.firmware_version or info_data.get("firmware_version"),
        "device_name": session.get("device_name"),
        "adoption_status": "adopted",
        "adopted_at": now,
        "created_at": now,
        "updated_at": now,
        "last_seen_at": None,
        "operation_status": None,
    }

    if existing and existing.get("user_id") == user_id:
        db.collection("devices").document(existing["device_id"]).update(
            {k: v for k, v in device_doc.items() if k not in ("created_at", "device_id")}
        )
        device_id = existing["device_id"]
    else:
        db.collection("devices").document(device_id).set(device_doc)

    session_store.update_session(
        db,
        ack.session_id,
        {
            "session_status": "committed",
            "user_message": "Pronto! Seu dispositivo foi adicionado.",
            "proposed_device_id": device_id,
        },
    )

    log_event(
        logger,
        logging.INFO,
        events.ADOPTION_SESSION_COMMITTED,
        "Adoption committed",
        session_id=ack.session_id,
        user_id=user_id,
        device_id=device_id,
    )


def cancel_session(db: FirestoreClient, session_id: str, user_id: str) -> bool:
    session = session_store.get_session(db, session_id)
    if session is None or session.get("user_id") != user_id:
        return False
    if session.get("session_status") in ("committed", "failed", "expired"):
        return False
    session_store.fail_session(db, session_id, failure_reason="cancelled")
    return True
