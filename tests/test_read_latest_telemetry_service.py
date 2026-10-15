"""Testes read_latest_telemetry (Firestore mock)."""

from __future__ import annotations

from typing import Any

import pytest

from mqtt_chat.schemas.telemetry_tools import ReadLatestTelemetryInput
from mqtt_chat.services.telemetry_queries import ReadLatestTelemetryError, read_latest_telemetry


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

    def order_by(self, field: str, direction: str = "ASCENDING") -> _FakeQuery:
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
            missing.exists = False  # type: ignore[misc]
            return missing
        return self._snap

    def collection(self, name: str) -> _FakeTelemetryCollection:
        assert name == "telemetry"
        return _FakeTelemetryCollection(self._telemetry)


class _ListDevicesQuery:
    def __init__(self, docs: list[_FakeSnapshot]) -> None:
        self._docs = docs

    def where(self, field: str, op: str, value: Any) -> _ListDevicesQuery:
        if field == "device_type":
            filtered = [d for d in self._docs if d.to_dict().get("device_type") == value]
            return _ListDevicesQuery(filtered)
        return self

    def stream(self):
        return iter(self._docs)


class _FakeDevicesCollection:
    def __init__(self, by_id: dict[str, _FakeDocRef]) -> None:
        self._by_id = by_id
        self._all = list(by_id.values())

    def document(self, doc_id: str) -> _FakeDocRef:
        return self._by_id[doc_id]

    def where(self, field: str, op: str, value: Any) -> _ListDevicesQuery:
        filtered = [
            _FakeSnapshot(ref.get().id, ref.get().to_dict())
            for ref in self._all
            if ref.get().exists and ref.get().to_dict().get(field) == value
        ]
        return _ListDevicesQuery(filtered)


class _FakeDb:
    def __init__(self, devices: _FakeDevicesCollection) -> None:
        self._devices = devices

    def collection(self, name: str) -> _FakeDevicesCollection:
        assert name == "devices"
        return self._devices


def _adopted_device(
    doc_id: str,
    *,
    user_id: str = "user-a",
    name: str = "Meu sensor",
    telemetry: list[_FakeSnapshot] | None = None,
) -> _FakeDocRef:
    snap = _FakeSnapshot(
        doc_id,
        {
            "user_id": user_id,
            "device_id": doc_id,
            "device_name": name,
            "device_type": "sensor",
            "model": "X",
            "adopted_at": "2026-10-14T00:00:00Z",
            "adoption_status": "adopted",
        },
    )
    return _FakeDocRef(snap, telemetry)


def test_read_latest_by_device_name_groups_same_received_at() -> None:
    telem = [
        _FakeSnapshot(
            "t1",
            {
                "metric": "temperature",
                "value": 22.5,
                "unit": "C",
                "device_ts": "2026-10-14T03:00:00Z",
                "received_at": "2026-10-14T03:00:01Z",
            },
        ),
        _FakeSnapshot(
            "t2",
            {
                "metric": "humidity",
                "value": 55.0,
                "unit": "%",
                "device_ts": "2026-10-14T03:00:00Z",
                "received_at": "2026-10-14T03:00:01Z",
            },
        ),
        _FakeSnapshot(
            "t0",
            {
                "metric": "temperature",
                "value": 20.0,
                "unit": "C",
                "received_at": "2026-10-14T02:00:00Z",
            },
        ),
    ]
    db = _FakeDb(_FakeDevicesCollection({"dev-1": _adopted_device("dev-1", telemetry=telem)}))
    result = read_latest_telemetry(
        db,  # type: ignore[arg-type]
        "user-a",
        ReadLatestTelemetryInput(device_name="sensor"),
    )
    assert result.has_telemetry is True
    assert len(result.readings) == 2
    metrics = {r.metric for r in result.readings}
    assert metrics == {"temperature", "humidity"}
    assert result.received_at == "2026-10-14T03:00:01Z"


def test_read_latest_single_device_auto_resolve() -> None:
    db = _FakeDb(
        _FakeDevicesCollection(
            {
                "only-one": _adopted_device(
                    "only-one",
                    telemetry=[
                        _FakeSnapshot(
                            "x",
                            {
                                "metric": "temperature",
                                "value": 1.0,
                                "received_at": "2026-10-14T04:00:00Z",
                            },
                        )
                    ],
                )
            }
        )
    )
    result = read_latest_telemetry(
        db,  # type: ignore[arg-type]
        "user-a",
        ReadLatestTelemetryInput(),
    )
    assert result.device_id == "only-one"
    assert result.readings[0].value == 1.0


def test_read_latest_no_telemetry() -> None:
    db = _FakeDb(_FakeDevicesCollection({"dev-1": _adopted_device("dev-1", telemetry=[])}))
    result = read_latest_telemetry(
        db,  # type: ignore[arg-type]
        "user-a",
        ReadLatestTelemetryInput(device_id="dev-1"),
    )
    assert result.has_telemetry is False
    assert result.readings == []


def test_read_latest_device_required() -> None:
    db = _FakeDb(
        _FakeDevicesCollection(
            {
                "a": _adopted_device("a", name="A"),
                "b": _adopted_device("b", name="B"),
            }
        )
    )
    with pytest.raises(ReadLatestTelemetryError) as exc:
        read_latest_telemetry(db, "user-a", ReadLatestTelemetryInput())  # type: ignore[arg-type]
    assert exc.value.code == "device_required"


def test_read_latest_wrong_user() -> None:
    db = _FakeDb(_FakeDevicesCollection({"dev-1": _adopted_device("dev-1", user_id="other")}))
    with pytest.raises(ReadLatestTelemetryError) as exc:
        read_latest_telemetry(
            db,  # type: ignore[arg-type]
            "user-a",
            ReadLatestTelemetryInput(device_id="dev-1"),
        )
    assert exc.value.code == "device_not_found"
