"""Testes do RealtimeHub."""

from __future__ import annotations

import asyncio

import pytest

from mqtt_chat.realtime.hub import RealtimeHub
from mqtt_chat.schemas.realtime import RealtimeEnvelope


class _FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send_text(self, data: str) -> None:
        self.messages.append(data)


def test_hub_filters_by_device_id() -> None:
    async def _run() -> None:
        hub = RealtimeHub()
        ws_all = _FakeWebSocket()
        ws_one = _FakeWebSocket()
        sub_all = await hub.register("user-a", ws_all, device_id_filter=None)
        sub_one = await hub.register("user-a", ws_one, device_id_filter="dev-1")

        envelope = RealtimeEnvelope(type="telemetry", payload={"device_id": "dev-1"})
        await hub.publish("user-a", envelope, device_id="dev-1")
        await asyncio.sleep(0.05)

        assert len(ws_all.messages) == 1
        assert len(ws_one.messages) == 1

        ws_all.messages.clear()
        ws_one.messages.clear()
        await hub.publish("user-a", envelope, device_id="dev-2")
        await asyncio.sleep(0.05)

        assert len(ws_all.messages) == 1
        assert len(ws_one.messages) == 0

        await hub.unregister("user-a", sub_all)
        await hub.unregister("user-a", sub_one)

    asyncio.run(_run())
