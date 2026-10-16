"""Testes de mapeamento NL → 0/1."""

import pytest

from mqtt_chat.services.actuator_command_language import (
    mqtt_set_value_to_bool,
    parse_power_intent,
    power_to_binary_value,
    utterance_has_actuator_command_verbs,
)


def test_parse_on_verbs() -> None:
    assert parse_power_intent("por favor liga o relé da garagem") == "on"
    assert parse_power_intent("ativar o motor") == "on"
    assert parse_power_intent("abrir a válvula") == "on"
    assert power_to_binary_value("on") == 1


def test_parse_off_verbs() -> None:
    assert parse_power_intent("desliga o relé") == "off"
    assert parse_power_intent("fechar portão") == "off"
    assert power_to_binary_value("off") == 0


def test_conflicting_verbs() -> None:
    assert parse_power_intent("liga e desliga") is None


def test_mqtt_set_value_to_bool() -> None:
    assert mqtt_set_value_to_bool(True) is True
    assert mqtt_set_value_to_bool(False) is False
    assert mqtt_set_value_to_bool(1) is True
    assert mqtt_set_value_to_bool(0) is False
    assert mqtt_set_value_to_bool(1.0) is True
    with pytest.raises(ValueError):
        mqtt_set_value_to_bool(2)


def test_detect_command_verbs() -> None:
    assert utterance_has_actuator_command_verbs("ligar relé")
    assert not utterance_has_actuator_command_verbs("última leitura")
