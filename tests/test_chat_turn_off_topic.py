"""Regras de turno — off-topic não propaga UI."""

from mqtt_chat.agent.tomato_ia import OFF_TOPIC_REPLY
from mqtt_chat.schemas.chat import ChatTurnResult, RealtimeTelemetrySuggestedUi
from mqtt_chat.services.chat_turn import finalize_turn


def test_finalize_turn_off_topic_strips_suggested_ui_at_call_site() -> None:
    raw = ChatTurnResult(scope="off_topic", reply="bitcoin price")
    outcome = finalize_turn(raw)
    assert outcome.scope == "off_topic"
    assert outcome.reply == OFF_TOPIC_REPLY
    assert outcome.persist is False
    suggested_ui = (
        RealtimeTelemetrySuggestedUi(device_id="x", device_name="Meu sensor")
        if outcome.scope == "product"
        else None
    )
    assert suggested_ui is None
