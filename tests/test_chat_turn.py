"""Testes do turno TomatoIA (classificação / persistência)."""

from mqtt_chat.agent.tomato_ia import OFF_TOPIC_REPLY
from mqtt_chat.schemas.chat import ChatTurnResult
from mqtt_chat.services.chat_turn import finalize_turn


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
