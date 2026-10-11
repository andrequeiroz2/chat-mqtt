"""Parse de tópicos tenants/{user_id}/devices/{device_id}/suffix."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParsedDeviceTopic:
    """Tópico de device pós-adoção (namespace PoC)."""

    user_id: str
    device_id: str
    suffix: str
    mqtt_topic_base: str


def parse_device_topic(topic: str) -> ParsedDeviceTopic | None:
    """
    Interpreta tenants/{user_id}/devices/{device_id}/{suffix}.

    Retorna None se o formato não bater.
    """
    parts = topic.split("/")
    if len(parts) != 5:
        return None
    prefix, user_id, devices_literal, device_id, suffix = parts
    if prefix != "tenants" or devices_literal != "devices":
        return None
    if not user_id or not device_id or not suffix:
        return None
    base = f"tenants/{user_id}/devices/{device_id}"
    return ParsedDeviceTopic(
        user_id=user_id,
        device_id=device_id,
        suffix=suffix,
        mqtt_topic_base=base,
    )
