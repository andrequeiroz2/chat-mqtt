"""Testes do turno TomatoIA (classificação / persistência)."""

from mqtt_chat.agent.tomato_ia import OFF_TOPIC_REPLY
from mqtt_chat.schemas.chat import (
    ChatTurnResult,
    RealtimeTelemetrySuggestedUi,
    TelemetryChartPoint,
    TelemetryChartSuggestedUi,
)
from mqtt_chat.services.chat_turn import finalize_turn, gate_suggested_ui_by_intent


def test_finalize_off_topic_uses_fixed_reply_and_no_persist() -> None:
    raw = ChatTurnResult(scope="off_topic", reply="Bitcoin está em alta hoje")
    outcome = finalize_turn(raw)
    assert outcome.persist is False
    assert outcome.scope == "off_topic"
    assert outcome.reply == OFF_TOPIC_REPLY
    assert "Bitcoin" not in outcome.reply


def test_finalize_product_persists_model_reply() -> None:
    raw = ChatTurnResult(scope="product", reply="  Um sensor publica telemetria MQTT.  ")
    outcome = finalize_turn(raw)
    assert outcome.persist is True
    assert outcome.reply == "Um sensor publica telemetria MQTT."


def _chart_ui() -> TelemetryChartSuggestedUi:
    return TelemetryChartSuggestedUi(
        device_id="dev1",
        metric="temperature",
        period_label="7d",
        points=[TelemetryChartPoint(received_at="2026-10-14T00:00:00Z", value=21.5)],
    )


def _realtime_ui() -> RealtimeTelemetrySuggestedUi:
    return RealtimeTelemetrySuggestedUi(device_id="dev1")


def test_gate_drops_chart_on_metadata_question() -> None:
    """022-02: gráfico de tool proativa não propaga em pergunta de metadado."""
    ui = gate_suggested_ui_by_intent(_chart_ui(), "que dia meu sensor foi registrado?")
    assert ui is None


def test_gate_keeps_chart_on_history_question() -> None:
    chart = _chart_ui()
    ui = gate_suggested_ui_by_intent(chart, "histórico de temperatura dos últimos 7 dias")
    assert ui is chart


def test_gate_drops_realtime_on_inventory_question() -> None:
    ui = gate_suggested_ui_by_intent(_realtime_ui(), "quais dispositivos eu tenho?")
    assert ui is None


def test_gate_keeps_realtime_on_realtime_question() -> None:
    ui = gate_suggested_ui_by_intent(_realtime_ui(), "acompanhar ao vivo")
    assert ui is not None


def test_gate_none_passthrough() -> None:
    assert gate_suggested_ui_by_intent(None, "qualquer coisa") is None
