"""Task 023-04 — simulador desktop: LWT offline + offline na parada graciosa."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

_SIMULATOR_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "devices" / "simulate_device.py"
)


def _load_simulator_module():
    spec = importlib.util.spec_from_file_location("simulate_device", _SIMULATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakePublishInfo:
    def wait_for_publish(self, timeout: float | None = None) -> None:
        return None


class _FakeMqttClient:
    """Client paho fake: registra chamadas em ordem."""

    def __init__(self, *args, **kwargs) -> None:
        self.calls: list[tuple] = []

    def will_set(self, topic, payload=None, qos=0, retain=False) -> None:
        self.calls.append(("will_set", topic, payload, qos, retain))

    def connect(self, *args, **kwargs) -> None:
        self.calls.append(("connect",))

    def loop_start(self) -> None:
        self.calls.append(("loop_start",))

    def publish(self, topic, payload=None, qos=0, retain=False) -> _FakePublishInfo:
        self.calls.append(("publish", topic, payload, qos, retain))
        return _FakePublishInfo()

    def loop_stop(self) -> None:
        self.calls.append(("loop_stop",))

    def disconnect(self) -> None:
        self.calls.append(("disconnect",))


def _args() -> argparse.Namespace:
    return argparse.Namespace(
        user_id="dev-user",
        device_id="sim-1",
        host="127.0.0.1",
        port=1883,
        interval=10.0,
        device_type="sensor",
        metric="humidity",
        unit="%",
    )


def test_simulator_sets_lwt_offline_retained(monkeypatch) -> None:
    mod = _load_simulator_module()
    monkeypatch.setattr(mod.mqtt, "Client", _FakeMqttClient)

    sim = mod.DeviceSimulator(_args())
    client = sim._client

    will = [c for c in client.calls if c[0] == "will_set"]
    assert len(will) == 1
    _, topic, payload, qos, retain = will[0]
    assert topic == mod.topic_status("dev-user", "sim-1")
    assert json.loads(payload)["operation_status"] == "offline"
    assert qos == 1
    assert retain is True


def test_simulator_publishes_offline_on_graceful_stop(monkeypatch) -> None:
    mod = _load_simulator_module()
    monkeypatch.setattr(mod.mqtt, "Client", _FakeMqttClient)

    sim = mod.DeviceSimulator(_args())
    sim._running = False  # sai do loop imediatamente → executa o finally
    sim.run()

    client = sim._client
    offline_publishes = [
        c
        for c in client.calls
        if c[0] == "publish"
        and c[1] == mod.topic_status("dev-user", "sim-1")
        and json.loads(c[2])["operation_status"] == "offline"
    ]
    assert len(offline_publishes) == 1
    assert offline_publishes[0][3] == 1  # qos
    assert offline_publishes[0][4] is True  # retain

    # ordem: offline → loop_stop → disconnect (LWT não dispara em parada limpa)
    kinds = [c[0] for c in client.calls]
    idx_offline = kinds.index("publish") if "publish" in kinds else -1
    assert idx_offline < kinds.index("loop_stop") < kinds.index("disconnect")
