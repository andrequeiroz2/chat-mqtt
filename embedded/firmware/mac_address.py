# MAC normalizado para payloads (AA:BB:...) e tópico (12 hex uppercase)


def mac_bytes_to_normalized(mac_bytes):
    """bytes 6 octets → AA:BB:CC:DD:EE:FF"""
    parts = ["%02X" % b for b in mac_bytes]
    return ":".join(parts)


def mac_to_topic_id(mac_normalized):
    """Remove ':' e garante uppercase (UC-A)."""
    return mac_normalized.replace(":", "").upper()


def read_sta_mac():
    import network

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    raw = wlan.config("mac")
    normalized = mac_bytes_to_normalized(raw)
    return normalized, mac_to_topic_id(normalized)
