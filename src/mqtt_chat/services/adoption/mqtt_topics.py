"""Tópicos MQTT UC-A — unclaimed/devices/{mac_normalized}/."""

from __future__ import annotations

from mqtt_chat.validators.mac_address import mac_to_normalized_topic_id, normalize_mac_address


def unclaimed_topic_base(mac_address: str) -> str:
    """Prefixo handshake v1.2-dev."""
    mac_id = mac_to_normalized_topic_id(mac_address)
    return f"unclaimed/devices/{mac_id}"


def unclaimed_topic(mac_address: str, suffix: str) -> str:
    """Sufixo: challenge | info | config | ack | announce."""
    return f"{unclaimed_topic_base(mac_address)}/{suffix}"


def proposed_mqtt_topic_base(user_id: str, device_id: str) -> str:
    return f"tenants/{user_id}/devices/{device_id}"


def mac_from_unclaimed_topic(topic: str) -> str | None:
    """
    Extrai MAC canônico de unclaimed/devices/{12hex}/suffix.

    Retorna None se o tópico não for handshake unclaimed.
    """
    parts = topic.split("/")
    if len(parts) < 4 or parts[0] != "unclaimed" or parts[1] != "devices":
        return None
    mac_id = parts[2]
    if len(mac_id) != 12:
        return None
    try:
        return normalize_mac_address(mac_id)
    except ValueError:
        return None


def unclaimed_suffix(topic: str) -> str | None:
    parts = topic.split("/")
    if len(parts) < 4 or parts[0] != "unclaimed" or parts[1] != "devices":
        return None
    return parts[3]
