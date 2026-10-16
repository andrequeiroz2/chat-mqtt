"""Copy de templates — UX sem device_id."""

from mqtt_chat.services.conversation_templates import display_device_name, template_clarify_sensors


def test_display_name_never_uses_uuid() -> None:
    assert display_device_name(None, device_type="sensor") == "seu sensor"
    assert display_device_name("", device_type="actuator") == "seu atuador"
    assert display_device_name("Sala", device_type="sensor") == "Sala"
    assert "a1b2" not in display_device_name(None, device_type="sensor", list_index=2)
    assert display_device_name(None, device_type="sensor", list_index=2) == "Sensor 2"


def test_clarify_sensors_without_names() -> None:
    text = template_clarify_sensors([None, "Quintal"])
    assert "Sensor 1" in text
    assert "Quintal" in text
    assert "a1b2" not in text
