"""
Entry point — WiFi fixo + adoção MQTT UC-A + telemetria simulada (pós-adoção).
"""

import time

import mac_address
import runtime_config
import wifi_sta


def _load_secrets():
    try:
        import secrets_wifi as sec
    except ImportError:
        print("main: copie secrets_wifi.example.py -> secrets_wifi.py")
        raise

    return (
        sec.WIFI_SSID,
        sec.WIFI_PASSWORD,
        sec.MQTT_BROKER_HOST,
        getattr(sec, "MQTT_BROKER_PORT", 1883),
        getattr(sec, "MQTT_USERNAME", None),
        getattr(sec, "MQTT_PASSWORD", None),
    )


def _run_operation(cfg, mqtt_user, mqtt_pass):
    import operation_mqtt

    client = operation_mqtt.OperationClient(cfg, mqtt_user, mqtt_pass)
    client.connect()
    try:
        while True:
            client.poll()
            time.sleep_ms(50)
    finally:
        client.disconnect()


def _run_adoption(mac, mac_id, broker_host, broker_port, mqtt_user, mqtt_pass):
    import adoption_mqtt

    client = adoption_mqtt.AdoptionClient(
        mac, mac_id, broker_host, broker_port, mqtt_user, mqtt_pass
    )
    client.connect()
    try:
        while True:
            client.poll()
            time.sleep_ms(100)
    finally:
        client.disconnect()


def run():
    mac, mac_id = mac_address.read_sta_mac()
    print("main: MAC", mac, "topic_id", mac_id)

    ssid, password, broker_host, broker_port, mqtt_user, mqtt_pass = _load_secrets()

    ok, ip = wifi_sta.connect_wifi(ssid, password)
    if not ok:
        print("main: WiFi failed for ssid=", ssid)
        return
    print("main: WiFi ok ip=", ip)

    if runtime_config.is_adopted():
        cfg = runtime_config.load()
        print("main: operation mode device_id=", cfg.get("device_id"))
        _run_operation(cfg, mqtt_user, mqtt_pass)
        return

    _run_adoption(mac, mac_id, broker_host, broker_port, mqtt_user, mqtt_pass)


if __name__ == "__main__":
    run()
