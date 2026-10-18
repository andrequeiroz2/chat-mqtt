"""Testes get_telemetry_history (Firestore mock)."""

from __future__ import annotations

from typing import Any

import pytest

from mqtt_chat.schemas.telemetry_tools import TelemetryHistoryInput
from mqtt_chat.services.telemetry_queries import ReadLatestTelemetryError, get_telemetry_history


class _FakeSnapshot:
    def __init__(self, doc_id: str, data: dict[str, Any]) -> None:
        self.id = doc_id
        self._data = data
        self.exists = True

    def to_dict(self) -> dict[str, Any]:
        return self._data


class _FakeQuery:
    def __init__(self, docs: list[_FakeSnapshot]) -> None:
        self._docs = sorted(
            docs,
            key=lambda d: d.to_dict().get("received_at") or "",
            reverse=True,
        )

    def order_by(self, field: str, direction: str = "ASCENDING") -> _FakeQuery:
        return self

    def limit(self, n: int) -> _FakeQuery:
        return _FakeQuery(self._docs[:n])

    def stream(self):
        return iter(self._docs)


class _FakeTelemetryCollection:
    def __init__(self, docs: list[_FakeSnapshot]) -> None:
        self._docs = docs

    def order_by(self, field: str, direction: str = "DESCENDING") -> _FakeQuery:
        return _FakeQuery(self._docs)


class _FakeDocRef:
    def __init__(
        self,
        snap: _FakeSnapshot | None,
        telemetry: list[_FakeSnapshot] | None = None,
    ) -> None:
        self._snap = snap
        self._telemetry = telemetry or []

    def get(self) -> _FakeSnapshot:
        if self._snap is None:
            missing = _FakeSnapshot("", {})
            missing.exists = False
            return missing
        return self._snap

    def collection(self, name: str) -> _FakeTelemetryCollection:
        assert name == "telemetry"
        return _FakeTelemetryCollection(self._telemetry)


class _FakeDb:
    def __init__(self, devices: dict[str, _FakeDocRef]) -> None:
        self._devices = devices

    def collection(self, name: str):
        assert name == "devices"

        class _Devices:
            def __init__(self, outer: _FakeDb) -> None:
                self._outer = outer

            def document(self, doc_id: str) -> _FakeDocRef:
                return self._outer._devices[doc_id]

        return _Devices(self)


def test_get_telemetry_history_builds_chart() -> None:
    device_id = "dev-1"
    telem = [
        _FakeSnapshot(
            "t1",
            {
                "received_at": "2026-10-10T12:00:00Z",
                "metric": "temperature",
                "value": 20.0,
                "unit": "C",
            },
        ),
        _FakeSnapshot(
            "t2",
            {
                "received_at": "2026-10-11T12:00:00Z",
                "metric": "temperature",
                "value": 22.0,
                "unit": "C",
            },
        ),
    ]
    db = _FakeDb(
        {
            device_id: _FakeDocRef(
                _FakeSnapshot(
                    device_id,
                    {
                        "user_id": "user-1",
                        "device_id": device_id,
                        "device_type": "sensor",
                        "device_name": "Sala",
                    },
                ),
                telem,
            ),
        },
    )

    result, chart = get_telemetry_history(
        db,  # type: ignore[arg-type]
        "user-1",
        TelemetryHistoryInput(device_id=device_id, days=30),
    )

    assert result.has_data
    assert result.point_count == 2
    assert chart is not None
    assert chart.kind == "telemetry_chart"
    assert chart.metric == "temperature"
    assert len(chart.points) == 2
    assert chart.points[0].value == 20.0


def test_get_telemetry_history_empty_raises() -> None:
    device_id = "dev-2"
    db = _FakeDb(
        {
            device_id: _FakeDocRef(
                _FakeSnapshot(
                    device_id,
                    {
                        "user_id": "user-1",
                        "device_id": device_id,
                        "device_type": "sensor",
                    },
                ),
                [],
            ),
        },
    )

    with pytest.raises(ReadLatestTelemetryError) as exc:
        get_telemetry_history(
            db,  # type: ignore[arg-type]
            "user-1",
            TelemetryHistoryInput(device_id=device_id),
        )
    assert exc.value.code == "telemetry_history_empty"


def test_get_telemetry_history_last_day_with_data() -> None:
    device_id = "dev-3"
    telem = [
        _FakeSnapshot(
            "t1",
            {
                "received_at": "2026-10-10T08:00:00Z",
                "metric": "temperature",
                "value": 18.0,
                "unit": "C",
            },
        ),
        _FakeSnapshot(
            "t2",
            {
                "received_at": "2026-10-14T04:41:08Z",
                "metric": "temperature",
                "value": 17.5,
                "unit": "C",
            },
        ),
        _FakeSnapshot(
            "t3",
            {
                "received_at": "2026-10-14T05:00:00Z",
                "metric": "temperature",
                "value": 18.0,
                "unit": "C",
            },
        ),
    ]
    db = _FakeDb(
        {
            device_id: _FakeDocRef(
                _FakeSnapshot(
                    device_id,
                    {
                        "user_id": "user-1",
                        "device_id": device_id,
                        "device_type": "sensor",
                    },
                ),
                telem,
            ),
        },
    )

    result, chart = get_telemetry_history(
        db,  # type: ignore[arg-type]
        "user-1",
        TelemetryHistoryInput(device_id=device_id, days=30, last_day_with_data=True),
    )

    assert result.point_count == 2
    assert chart is not None
    assert all(p.received_at.startswith("2026-10-14") for p in chart.points)
