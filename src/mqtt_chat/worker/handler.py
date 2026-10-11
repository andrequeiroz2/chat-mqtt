"""Roteamento de mensagens MQTT por sufixo de tópico."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mqtt_chat.config.settings import Settings
from mqtt_chat.logging import events, log_event
from mqtt_chat.services import telemetry as telemetry_service
from mqtt_chat.worker.topics import parse_device_topic

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient

logger = logging.getLogger(__name__)


async def handle_mqtt_message(
    topic: str,
    payload: bytes,
    settings: Settings,
    db: FirestoreClient | None,
) -> None:
    """
    Processa uma mensagem ingestada (telemetry, status, state).

    Erros de persistência são logados; não interrompem o loop MQTT.
    """
    log_event(
        logger,
        logging.DEBUG,
        events.MQTT_MESSAGE_RECEIVED,
        "MQTT message received",
        topic=topic,
        payload_bytes=len(payload),
    )

    parsed = parse_device_topic(topic)
    if parsed is None:
        logger.debug("Ignoring non-device topic=%s", topic)
        return

    log_event(
        logger,
        logging.DEBUG,
        events.DEVICE_TOPIC_PARSED,
        "Device topic parsed",
        user_id=parsed.user_id,
        device_id=parsed.device_id,
        topic_suffix=parsed.suffix,
        mqtt_topic_base=parsed.mqtt_topic_base,
    )

    try:
        if parsed.suffix == "telemetry":
            await telemetry_service.persist_telemetry(parsed, payload, settings, db)
        elif parsed.suffix == "status":
            await telemetry_service.persist_status(parsed, payload, settings, db)
        elif parsed.suffix == "state":
            await telemetry_service.persist_state(parsed, payload, settings, db)
        else:
            logger.debug("Unhandled suffix=%s topic=%s", parsed.suffix, topic)
    except Exception:
        log_event(
            logger,
            logging.ERROR,
            events.HANDLER_FAILED,
            "Handler failed",
            topic=topic,
            exc_info=True,
        )
