"""Validação MAC e tópicos unclaimed."""

import pytest

from mqtt_chat.services.adoption.mqtt_topics import mac_from_unclaimed_topic, unclaimed_topic_base
from mqtt_chat.validators.mac_address import InvalidMacAddressError, normalize_mac_address


def test_normalize_mac_colon():
    assert normalize_mac_address("3c:71:bf:4d:db:0c") == "3C:71:BF:4D:DB:0C"


def test_normalize_mac_compact():
    assert normalize_mac_address("3C71BF4DDB0C") == "3C:71:BF:4D:DB:0C"


def test_unclaimed_topic_base():
    assert unclaimed_topic_base("3C:71:BF:4D:DB:0C") == "unclaimed/devices/3C71BF4DDB0C"


def test_mac_from_topic():
    mac = mac_from_unclaimed_topic("unclaimed/devices/3C71BF4DDB0C/info")
    assert mac == "3C:71:BF:4D:DB:0C"


def test_invalid_mac():
    with pytest.raises(InvalidMacAddressError):
        normalize_mac_address("not-a-mac")
