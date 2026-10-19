"""Testes contrato task 017: unit obrigatório por leitura na ingestão MQTT."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from mqtt_chat.schemas.telemetry import ReadingItem, TelemetryPayload
from mqtt_chat.services import telemetry as telemetry_service
from mqtt_chat.worker.topics import ParsedDeviceTopic


class _FakeSettings:
    worker_persist_mode = "log"


def _parsed() -> ParsedDeviceTopic:
    return ParsedDeviceTopic(
        user_id="u1",
        device_id="d1",
        suffix="telemetry",
        mqtt_topic_base="tenants/u1/devices/d1",
    )


def test_reading_item_unit_required() -> None:
    with pytest.raises(ValueError):
        ReadingItem(metric="temperature", value=23.4, unit="")
    with pytest.raises(ValueError):
        ReadingItem(metric="temperature", value=23.4, unit="   ")


def test_reading_item_unit_accepts_any_non_blank_string() -> None:
    item = ReadingItem(metric="pressure", value=1.5, unit="Bar")
    assert item.unit == "Bar"


def test_expanded_readings_single_metric_requires_unit() -> None:
    payload = TelemetryPayload.model_validate({"metric": "humidity", "value": 50.0})
    assert payload.expanded_readings() == []

    payload_ok = TelemetryPayload.model_validate(
        {"metric": "humidity", "value": 50.0, "unit": "%"}
    )
    assert len(payload_ok.expanded_readings()) == 1
    assert payload_ok.expanded_readings()[0].unit == "%"


def _capture_broadcast_readings():
    captured: list[list[dict[str, Any]]] = []

    async def fake_broadcast(parsed, readings, *, device_ts, received_at):
        captured.append([{"metric": r.metric, "unit": r.unit} for r in readings])

    original = telemetry_service.realtime_broadcast.broadcast_telemetry
    telemetry_service.realtime_broadcast.broadcast_telemetry = fake_broadcast
    return captured, original


def _restore_broadcast(original) -> None:
    telemetry_service.realtime_broadcast.broadcast_telemetry = original


def test_persist_telemetry_discards_invalid_reading_keeps_valid() -> None:
    data = {
        "ts": "2026-10-18T12:00:00Z",
        "readings": [
            {"metric": "temperature", "value": 23.4, "unit": "C"},
            {"metric": "humidity", "value": 61.0},
        ],
    }
    captured, original = _capture_broadcast_readings()
    try:
        asyncio.run(
            telemetry_service.persist_telemetry(
                _parsed(),
                json.dumps(data).encode("utf-8"),
                _FakeSettings(),
                object(),
            )
        )
    finally:
        _restore_broadcast(original)

    assert captured == [[{"metric": "temperature", "unit": "C"}]]


def test_persist_telemetry_all_readings_invalid_no_write() -> None:
    data = {
        "readings": [
            {"metric": "temperature", "value": 23.4},
            {"metric": "humidity", "value": 61.0, "unit": ""},
        ],
    }
    captured, original = _capture_broadcast_readings()
    try:
        asyncio.run(
            telemetry_service.persist_telemetry(
                _parsed(),
                json.dumps(data).encode("utf-8"),
                _FakeSettings(),
                object(),
            )
        )
    finally:
        _restore_broadcast(original)

    assert captured == []


def test_persist_telemetry_legacy_single_metric_without_unit_rejected() -> None:
    data = {"metric": "humidity", "value": 50.0}
    captured, original = _capture_broadcast_readings()
    try:
        asyncio.run(
            telemetry_service.persist_telemetry(
                _parsed(),
                json.dumps(data).encode("utf-8"),
                _FakeSettings(),
                object(),
            )
        )
    finally:
        _restore_broadcast(original)

    assert captured == []
