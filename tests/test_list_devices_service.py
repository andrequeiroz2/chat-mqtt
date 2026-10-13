"""Testes do service list_devices (sem Firestore real)."""

from __future__ import annotations

from typing import Any

import pytest

from mqtt_chat.schemas.devices import ListDevicesInput
from mqtt_chat.services.devices import ListDevicesError, list_devices


class _FakeSnapshot:
    def __init__(self, doc_id: str, data: dict[str, Any]) -> None:
        self.id = doc_id
        self._data = data
        self.exists = True

    def to_dict(self) -> dict[str, Any]:
        return self._data


class _FakeQuery:
    def __init__(self, docs: list[_FakeSnapshot]) -> None:
        self._docs = docs

    def where(self, field: str, op: str, value: Any) -> _FakeQuery:
        if field == "device_type":
            filtered = [
                d for d in self._docs if (d.to_dict().get("device_type") == value)
            ]
            return _FakeQuery(filtered)
        return self

    def stream(self):
        return iter(self._docs)


class _FakeCollection:
    def __init__(self, by_id: dict[str, _FakeSnapshot]) -> None:
        self._by_id = by_id
        self._all = list(by_id.values())

    def document(self, doc_id: str):
        return _FakeDocRef(self._by_id.get(doc_id))

    def where(self, field: str, op: str, value: Any) -> _FakeQuery:
        if field != "user_id" or op != "==":
            raise NotImplementedError
        filtered = [d for d in self._all if d.to_dict().get("user_id") == value]
        return _FakeQuery(filtered)


class _FakeDocRef:
    def __init__(self, snap: _FakeSnapshot | None) -> None:
        self._snap = snap

    def get(self) -> _FakeSnapshot:
        if self._snap is None:
            missing = _FakeSnapshot("", {})
            missing.exists = False  # type: ignore[misc]
            return missing
        return self._snap


class _FakeDb:
    def __init__(self, docs: list[_FakeSnapshot]) -> None:
        self._collection = _FakeCollection({d.id: d for d in docs})

    def collection(self, name: str) -> _FakeCollection:
        assert name == "devices"
        return self._collection


def _device(
    doc_id: str,
    *,
    user_id: str = "user-a",
    name: str,
    device_type: str = "sensor",
) -> _FakeSnapshot:
    return _FakeSnapshot(
        doc_id,
        {
            "device_id": doc_id,
            "user_id": user_id,
            "device_name": name,
            "device_type": device_type,
            "model": "ESP32",
            "adoption_status": "adopted",
            "adopted_at": "2026-01-01T00:00:00Z",
        },
    )


def test_list_all_for_user() -> None:
    db = _FakeDb(
        [
            _device("id-1", name="Alpha"),
            _device("id-2", name="Beta"),
            _device("id-x", user_id="other", name="Other"),
        ]
    )
    result = list_devices(db, "user-a", ListDevicesInput())  # type: ignore[arg-type]
    assert result.total_returned == 2
    assert [d.device_name for d in result.devices] == ["Alpha", "Beta"]


def test_filter_device_type() -> None:
    db = _FakeDb(
        [
            _device("s1", name="S1", device_type="sensor"),
            _device("a1", name="A1", device_type="actuator"),
        ]
    )
    result = list_devices(
        db,  # type: ignore[arg-type]
        "user-a",
        ListDevicesInput(device_type="actuator"),
    )
    assert result.total_returned == 1
    assert result.devices[0].device_id == "a1"


def test_filter_name_contains() -> None:
    db = _FakeDb([_device("1", name="Sensor Sala"), _device("2", name="Garagem")])
    result = list_devices(
        db,  # type: ignore[arg-type]
        "user-a",
        ListDevicesInput(device_name="sala"),
    )
    assert result.total_returned == 1
    assert result.devices[0].device_name == "Sensor Sala"


def test_device_id_other_user_returns_empty() -> None:
    db = _FakeDb([_device("secret", user_id="user-b", name="X")])
    result = list_devices(
        db,  # type: ignore[arg-type]
        "user-a",
        ListDevicesInput(device_id="secret"),
    )
    assert result.devices == []


def test_pagination_cursor() -> None:
    db = _FakeDb(
        [
            _device("1", name="A"),
            _device("2", name="B"),
            _device("3", name="C"),
        ]
    )
    page1 = list_devices(db, "user-a", ListDevicesInput(limit=2))  # type: ignore[arg-type]
    assert page1.has_more is True
    assert page1.next_cursor

    page2 = list_devices(
        db,  # type: ignore[arg-type]
        "user-a",
        ListDevicesInput(limit=2, cursor=page1.next_cursor),
    )
    assert page2.total_returned == 1
    assert page2.devices[0].device_name == "C"
    assert page2.has_more is False


def test_invalid_cursor() -> None:
    db = _FakeDb([_device("1", name="A")])
    with pytest.raises(ListDevicesError) as exc:
        list_devices(
            db,  # type: ignore[arg-type]
            "user-a",
            ListDevicesInput(cursor="not-valid!!!"),
        )
    assert exc.value.code == "invalid_cursor"
