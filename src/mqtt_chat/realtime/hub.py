"""Hub in-process: fan-out de eventos MQTT → WebSockets por user_id."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from fastapi import WebSocket

from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.realtime import RealtimeEnvelope

logger = logging.getLogger(__name__)

_hub: RealtimeHub | None = None


def get_realtime_hub() -> RealtimeHub:
    global _hub
    if _hub is None:
        _hub = RealtimeHub()
    return _hub


@dataclass
class _Subscription:
    websocket: WebSocket
    device_id_filter: str | None = None
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class RealtimeHub:
    """Assinantes WebSocket agrupados por user_id (tenant)."""

    def __init__(self) -> None:
        self._by_user: dict[str, list[_Subscription]] = {}
        self._gate = asyncio.Lock()

    async def register(
        self,
        user_id: str,
        websocket: WebSocket,
        *,
        device_id_filter: str | None = None,
    ) -> _Subscription:
        sub = _Subscription(websocket=websocket, device_id_filter=device_id_filter)
        async with self._gate:
            self._by_user.setdefault(user_id, []).append(sub)
        return sub

    async def unregister(self, user_id: str, sub: _Subscription) -> None:
        async with self._gate:
            bucket = self._by_user.get(user_id)
            if not bucket:
                return
            try:
                bucket.remove(sub)
            except ValueError:
                return
            if not bucket:
                del self._by_user[user_id]

    async def publish(self, user_id: str, envelope: RealtimeEnvelope, *, device_id: str) -> None:
        async with self._gate:
            subs = list(self._by_user.get(user_id, []))

        if not subs:
            return

        raw = envelope.model_dump_json()
        for sub in subs:
            if sub.device_id_filter is not None and sub.device_id_filter != device_id:
                continue
            asyncio.create_task(
                _safe_send(sub, raw, user_id=user_id, device_id=device_id),
                name="realtime-ws-send",
            )


async def _safe_send(sub: _Subscription, raw: str, *, user_id: str, device_id: str) -> None:
    async with sub.send_lock:
        try:
            await sub.websocket.send_text(raw)
        except Exception as exc:
            log_event(
                logger,
                logging.DEBUG,
                events.REALTIME_WS_SEND_FAILED,
                "Realtime WebSocket send failed",
                user_id=user_id,
                device_id=device_id,
                error=str(exc),
            )
