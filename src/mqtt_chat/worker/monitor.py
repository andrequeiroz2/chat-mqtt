"""Loop de monitoramento MQTT com reconexão (espelho device_app collector)."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from aiomqtt import Client

from mqtt_chat.clients.firebase import get_firestore
from mqtt_chat.clients.mqtt import is_mqtt_connection_error, mqtt_session, publish_message
from mqtt_chat.config.settings import Settings
from mqtt_chat.logging import events, log_event
from mqtt_chat.worker.handler import handle_mqtt_message

logger = logging.getLogger(__name__)

PublishRequest = tuple[str, bytes]


@dataclass
class WorkerHealth:
    """Estado exposto para health check."""

    mqtt_connected: bool = False
    reconnect_count: int = 0
    last_error: str | None = None


@dataclass
class _MonitorContext:
    """Contexto compartilhado da task de monitor."""

    health: WorkerHealth
    publish_queue: asyncio.Queue[PublishRequest] = field(
        default_factory=lambda: asyncio.Queue(maxsize=32)
    )


async def run_with_reconnect(
    settings: Settings,
    stop_event: asyncio.Event,
    health: WorkerHealth | None = None,
    publish_queue: asyncio.Queue[PublishRequest] | None = None,
) -> None:
    """
    Executa loop externo com backoff até stop_event.

    Espelha run_monitor_with_reconnect do device_app (Rust).
    """
    ctx = _MonitorContext(
        health=health or WorkerHealth(),
        publish_queue=publish_queue or asyncio.Queue(maxsize=32),
    )
    db = get_firestore(settings)
    backoff = settings.mqtt_backoff_initial
    is_reconnect = False

    while not stop_event.is_set():
        try:
            stopped = await _try_connect_and_monitor(
                settings,
                stop_event,
                ctx,
                db,
                is_reconnect,
            )
            if stopped:
                break
            log_event(
                logger,
                logging.WARNING,
                events.MQTT_CONNECTION_LOST,
                "MQTT connection closed unexpectedly",
            )
            ctx.health.mqtt_connected = False
            is_reconnect = True
            ctx.health.reconnect_count += 1
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if not is_mqtt_connection_error(exc):
                logger.exception("Unexpected worker error")
            else:
                logger.error("MQTT connection error: %s. Reconnecting...", exc)
            ctx.health.mqtt_connected = False
            ctx.health.last_error = str(exc)
            if not is_reconnect:
                logger.critical("Initial MQTT connection failed: %s", exc)
            is_reconnect = True
            ctx.health.reconnect_count += 1

        if stop_event.is_set():
            break

        delay = min(backoff, settings.mqtt_backoff_max)
        log_event(
            logger,
            logging.INFO,
            events.MQTT_BACKOFF,
            "MQTT reconnect backoff",
            backoff_sec=delay,
        )
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=delay)
            break
        except TimeoutError:
            pass
        backoff = min(backoff * 2, settings.mqtt_backoff_max)

    ctx.health.mqtt_connected = False
    log_event(logger, logging.INFO, events.MQTT_WORKER_STOPPED, "MQTT worker stopped")


async def _try_connect_and_monitor(
    settings: Settings,
    stop_event: asyncio.Event,
    ctx: _MonitorContext,
    db,
    is_reconnect: bool,
) -> bool:
    """
    Uma sessão conectada. Retorna True se parada graceful (stop_event).

    Retorna False se conexão caiu (reconectar).
    """
    async with mqtt_session(settings) as client:
        ctx.health.mqtt_connected = True
        ctx.health.last_error = None
        pump_task = asyncio.create_task(
            _publish_queue_pump(client, ctx.publish_queue, stop_event),
            name="mqtt-publish-pump",
        )
        if is_reconnect:
            log_event(
                logger,
                logging.INFO,
                events.MQTT_CONNECTION_RESTORED,
                "MQTT connection restored",
                mqtt_host=settings.mqtt_host,
                mqtt_port=settings.mqtt_port,
            )
        else:
            log_event(
                logger,
                logging.INFO,
                events.MQTT_CONNECTED,
                "MQTT connected",
                mqtt_host=settings.mqtt_host,
                mqtt_port=settings.mqtt_port,
            )

        try:
            await _drain_publish_queue(client, ctx.publish_queue)
            async for message in client.messages:
                if stop_event.is_set():
                    return True

                await _drain_publish_queue(client, ctx.publish_queue)

                await handle_mqtt_message(
                    str(message.topic),
                    message.payload,
                    settings,
                    db,
                    ctx.publish_queue,
                )

            return False
        finally:
            pump_task.cancel()
            try:
                await pump_task
            except asyncio.CancelledError:
                pass


async def _publish_queue_pump(
    client: Client,
    queue: asyncio.Queue[PublishRequest],
    stop_event: asyncio.Event,
) -> None:
    """
    Esvazia a fila outbound mesmo sem tráfego inbound.

    Adoção publica challenge/config via HTTP → fila; o device só responde depois
    do challenge — sem pump, a fila nunca era drenada (deadlock).
    """
    while not stop_event.is_set():
        await _drain_publish_queue(client, queue)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=0.15)
            break
        except TimeoutError:
            continue


async def _drain_publish_queue(client: Client, queue: asyncio.Queue[PublishRequest]) -> None:
    """Publica mensagens pendentes na fila outbound."""
    while True:
        try:
            topic, payload = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        try:
            await publish_message(client, topic, payload)
            if topic.startswith("unclaimed/devices/"):
                log_event(
                    logger,
                    logging.INFO,
                    events.MQTT_PUBLISHED,
                    "MQTT published",
                    topic=topic,
                    payload_bytes=len(payload),
                )
        except Exception as exc:
            logger.error("Publish failed topic=%s error=%s", topic, exc)


async def enqueue_publish(
    queue: asyncio.Queue[PublishRequest],
    topic: str,
    payload: bytes,
) -> None:
    """Enfileira publish para o monitor conectado (RF-WORKER-07)."""
    await queue.put((topic, payload))
