"""Testes do resolver determinístico (G1–G12)."""

from mqtt_chat.schemas.conversation_context import ConversationContext, DeviceSnapshotEntry
from mqtt_chat.services.device_intent_resolver import (
    connectivity_from_status,
    detect_chat_intent,
    resolve_device_intent,
)


def _ctx(
    *,
    snapshot: list[DeviceSnapshotEntry],
    focus: str | None = None,
) -> ConversationContext:
    sensors = sum(1 for s in snapshot if s.device_type == "sensor")
    actuators = sum(1 for s in snapshot if s.device_type == "actuator")
    return ConversationContext(
        updated_at="2026-10-16T00:00:00Z",
        session_focus_device_id=focus,
        device_count=len(snapshot),
        sensor_count=sensors,
        actuator_count=actuators,
        device_snapshot=snapshot,
    )


def _sensor(
    did: str,
    name: str,
    *,
    status: str | None = "online",
) -> DeviceSnapshotEntry:
    return DeviceSnapshotEntry(
        device_id=did,
        device_name=name,
        device_type="sensor",
        adopted_at="2026-10-15T12:00:00Z",
        operation_status=status,
    )


def _actuator(did: str, name: str) -> DeviceSnapshotEntry:
    return DeviceSnapshotEntry(
        device_id=did,
        device_name=name,
        device_type="actuator",
        adopted_at="2026-10-14T12:00:00Z",
    )


def test_detect_read_and_realtime_intents() -> None:
    assert detect_chat_intent("me mostre a última leitura") == "read_telemetry"
    assert detect_chat_intent("quero tempo real no sensor") == "realtime"
    assert detect_chat_intent("como está o bitcoin") is None


def test_detect_telemetry_history_before_read() -> None:
    assert (
        detect_chat_intent("mostra um gráfico da temperatura dos últimos 7 dias")
        == "telemetry_history"
    )
    assert detect_chat_intent("histórico de umidade na última semana") == "telemetry_history"


def test_g1_single_sensor_history() -> None:
    snap = [_sensor("s1", "Meu sensor")]
    result = resolve_device_intent(
        "mostra um gráfico da temperatura dos últimos 7 dias",
        _ctx(snapshot=snap),
    )
    assert result.outcome == "execute"
    assert result.intent == "telemetry_history"
    assert result.trigger_id == "G1"
    assert result.device_id == "s1"


def test_connectivity_unknown_when_status_missing() -> None:
    assert connectivity_from_status(None) == "unknown"
    assert connectivity_from_status("online") == "online"
    assert connectivity_from_status("offline") == "offline"


def test_g1_single_sensor() -> None:
    snap = [_sensor("s1", "Sala")]
    result = resolve_device_intent("última leitura", _ctx(snapshot=snap))
    assert result.outcome == "execute"
    assert result.trigger_id == "G1"
    assert result.device_id == "s1"


def test_g2_mixed_fleet() -> None:
    snap = [_sensor("s1", "Sala"), _actuator("a1", "Relé")]
    result = resolve_device_intent("última leitura", _ctx(snapshot=snap))
    assert result.outcome == "clarify"
    assert result.trigger_id == "G2"
    assert result.template_id == "T-INTENT-MIXED"


def test_g3_two_sensors_clarify() -> None:
    snap = [_sensor("s1", "Sala"), _sensor("s2", "Quintal")]
    result = resolve_device_intent("temperatura agora", _ctx(snapshot=snap))
    assert result.outcome == "clarify"
    assert result.trigger_id == "G3"


def test_g6_focus_with_two_sensors() -> None:
    snap = [_sensor("s1", "Sala"), _sensor("s2", "Quintal")]
    result = resolve_device_intent(
        "última leitura",
        _ctx(snapshot=snap, focus="s2"),
    )
    assert result.outcome == "execute"
    assert result.trigger_id == "G6"
    assert result.device_id == "s2"


def test_g12_realtime_offline_instruct() -> None:
    snap = [_sensor("s1", "Sala", status="offline")]
    result = resolve_device_intent("tempo real", _ctx(snapshot=snap))
    assert result.outcome == "instruct"
    assert result.trigger_id == "G12"
    assert result.template_id == "T5"


def test_g10_actuator_ligar_confirm_path() -> None:
    snap = [_actuator("a1", "Garagem")]
    result = resolve_device_intent("liga o relé Garagem", _ctx(snapshot=snap))
    assert result.outcome == "instruct"
    assert result.trigger_id == "G10"
    assert result.template_id == "T-COMMAND-CONFIRM"
    assert result.binary_value == 1
    assert result.verb_pt == "ligar"


def test_g4_name_match_single_sensor() -> None:
    snap = [_sensor("s1", "Sala"), _sensor("s2", "Quintal")]
    result = resolve_device_intent("leitura do sensor Quintal", _ctx(snapshot=snap))
    assert result.outcome == "execute"
    assert result.trigger_id == "G4"
    assert result.device_id == "s2"


def test_mac_address_question_instruct_without_llm() -> None:
    result = resolve_device_intent(
        "qual o mac address do meu sensor?",
        _ctx(snapshot=[_sensor("s1", "Sala")]),
    )
    assert result.outcome == "instruct"
    assert result.template_id == "T-NETWORK-NOT-IN-CHAT"
    assert result.short_circuit is True


def test_mqtt_topic_question_instruct() -> None:
    result = resolve_device_intent(
        "me informe o topico do dispositivo",
        _ctx(snapshot=[_sensor("s1", "Meu sensor")]),
    )
    assert result.outcome == "instruct"
    assert result.template_id == "T-MQTT-TOPICS"
    assert result.device_id == "s1"
    assert result.short_circuit is True


def test_mqtt_topic_actuator_not_sensor_focus() -> None:
    snap = [_sensor("s1", "Meu sensor"), _actuator("a1", "Meu relé")]
    result = resolve_device_intent(
        "qual e o topico mqtt do meu atuador?",
        _ctx(snapshot=snap, focus="s1"),
    )
    assert result.template_id == "T-MQTT-TOPICS"
    assert result.device_id == "a1"
    assert result.device_type == "actuator"


def test_mqtt_topic_actuator_missing() -> None:
    result = resolve_device_intent(
        "topico mqtt do atuador",
        _ctx(snapshot=[_sensor("s1", "Meu sensor")]),
    )
    assert result.template_id == "T-MQTT-TOPICS-TYPE-MISSING"
    assert result.device_type == "actuator"


def test_ip_address_question_instruct_without_llm() -> None:
    result = resolve_device_intent(
        "qual o ip do meu sensor?",
        _ctx(snapshot=[_sensor("s1", "Meu sensor")]),
    )
    assert result.outcome == "instruct"
    assert result.template_id == "T-NETWORK-NOT-IN-CHAT"
    assert result.short_circuit is True
