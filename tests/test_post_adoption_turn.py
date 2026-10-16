"""Turno zero pós-adoção (ações por device_type)."""

from mqtt_chat.services.post_adoption_turn import _build_actions


def test_post_adoption_actions_sensor() -> None:
    actions = _build_actions("sensor", operation_status="online")
    ids = {a.action_id for a in actions}
    assert "read_latest" in ids
    assert "realtime" in ids
    assert "list_devices" in ids
    realtime = next(a for a in actions if a.action_id == "realtime")
    assert realtime.disabled is False


def test_post_adoption_realtime_disabled_when_offline() -> None:
    actions = _build_actions("sensor", operation_status="offline")
    realtime = next(a for a in actions if a.action_id == "realtime")
    assert realtime.disabled is True


def test_post_adoption_actions_actuator() -> None:
    actions = _build_actions("actuator", operation_status=None)
    ids = {a.action_id for a in actions}
    assert "actuator_help" in ids
    assert "realtime" not in ids
    assert "list_devices" in ids
