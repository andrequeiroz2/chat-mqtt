"""Wrapper único do cliente MQTT (aiomqtt)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from aiomqtt import Client, MqttError

from mqtt_chat.config.settings import Settings
from mqtt_chat.logging import events, log_event

logger = logging.getLogger(__name__)

# Assinaturas PoC — contrato mqtt-chat v1.1
INGEST_SUBSCRIPTIONS: tuple[tuple[str, int], ...] = (
    ("tenants/+/devices/+/telemetry", 1),
    ("tenants/+/devices/+/status", 1),
    ("tenants/+/devices/+/state", 1),
    ("unclaimed/devices/+/info", 1),
    ("unclaimed/devices/+/ack", 1),
)


@dataclass(frozen=True, slots=True)
class MqttMessage:
    """Mensagem MQTT normalizada para o worker."""

    topic: str
    payload: bytes
    qos: int
    retain: bool


@asynccontextmanager
async def mqtt_session(settings: Settings) -> AsyncIterator[Client]:
    """
    Context manager de uma sessão MQTT conectada.

    Subscribe em INGEST_SUBSCRIPTIONS ao entrar.
    """
    client_kwargs: dict = {
        "hostname": settings.mqtt_host,
        "port": settings.mqtt_port,
        "identifier": settings.mqtt_client_id,
        "keepalive": settings.mqtt_keepalive,
        "timeout": settings.mqtt_connect_timeout,
        "clean_session": True,
    }
    if settings.mqtt_username:
        client_kwargs["username"] = settings.mqtt_username
    if settings.mqtt_password:
        client_kwargs["password"] = settings.mqtt_password

    async with Client(**client_kwargs) as client:
        for topic, qos in INGEST_SUBSCRIPTIONS:
            await client.subscribe(topic, qos=qos)
            log_event(
                logger,
                logging.INFO,
                events.MQTT_SUBSCRIBED,
                "MQTT subscribed",
                topic=topic,
                qos=qos,
            )
        yield client


async def publish_message(client: Client, topic: str, payload: bytes, qos: int = 1) -> None:
    """Publica payload no broker (comandos outbound — RF-WORKER-07)."""
    await client.publish(topic, payload, qos=qos)


def is_mqtt_connection_error(exc: BaseException) -> bool:
    """Indica se a exceção justifica reconexão."""
    return isinstance(exc, MqttError | ConnectionError | OSError)
