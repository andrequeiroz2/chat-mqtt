"""Copy de templates — UX sem device_id."""

from mqtt_chat.services.conversation_templates import (
    display_device_name,
    template_adoption_date,
    template_clarify_sensors,
    template_inventory,
    template_inventory_empty,
)


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


def test_inventory_empty_all() -> None:
    text = template_inventory_empty(None)
    assert "não tem dispositivos" in text
    assert "adoção" in text


def test_inventory_empty_sensor() -> None:
    text = template_inventory_empty("sensor")
    assert "não tem sensores" in text


def test_inventory_single_sensor() -> None:
    text = template_inventory(
        entries=[("Meu sensor", "sensor", "online")],
        device_type="sensor",
    )
    assert "**1 sensor**" in text
    assert "Meu sensor" in text
    assert "online" in text
    assert "(sensor)" not in text  # recorte único: tipo não se repete por linha


def test_inventory_mixed_lists_type_per_line() -> None:
    text = template_inventory(
        entries=[("Sala", "sensor", "online"), ("Relé", "actuator", None)],
        device_type=None,
    )
    assert "**2 dispositivos**" in text
    assert "(sensor)" in text
    assert "(atuador)" in text
    assert "sem status" in text


def test_inventory_never_shows_uuid() -> None:
    text = template_inventory(
        entries=[(None, "sensor", "online")],
        device_type="sensor",
    )
    assert "Sensor 1" in text
    assert "a1b2" not in text

def test_adoption_date_formats_pt_date() -> None:
    text = template_adoption_date(
        device_name="Meu sensor",
        device_type="sensor",
        adopted_at="2026-10-14T03:12:00+00:00",
    )
    assert "14/10/2026" in text
    assert "Meu sensor" in text
    assert "sensor" in text


def test_adoption_date_fallback_on_invalid_iso() -> None:
    text = template_adoption_date(
        device_name=None,
        device_type=None,
        adopted_at="valor-estranho",
    )
    assert "valor-estr" in text
