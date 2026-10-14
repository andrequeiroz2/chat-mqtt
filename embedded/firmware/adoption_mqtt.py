# Cliente MQTT — handshake UC-A (unclaimed/devices/{mac_id}/…)

try:
    import ujson as json
except ImportError:
    import json

from umqtt.simple import MQTTClient

import device_profile
import time_util


def _parse_broker_url(url):
    host = "127.0.0.1"
    port = 1883
    if not url:
        return host, port
    rest = url
    if rest.startswith("mqtt://"):
        rest = rest[7:]
    elif rest.startswith("mqtts://"):
        rest = rest[8:]
    if ":" in rest:
        host, port_s = rest.rsplit(":", 1)
        try:
            port = int(port_s)
        except ValueError:
            port = 1883
    else:
        host = rest
    return host, port


def _resolve_broker_host(config_host, fallback_host):
    if config_host in ("127.0.0.1", "localhost", "0.0.0.0"):
        return fallback_host
    return config_host


class AdoptionClient:
    """Modo não adotado: escuta challenge/config e publica info/ack."""

    def __init__(self, mac_normalized, mac_topic_id, broker_host, broker_port, mqtt_user, mqtt_pass):
        self.mac = mac_normalized
        self.mac_id = mac_topic_id
        self.base = "unclaimed/devices/" + mac_topic_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.mqtt_user = mqtt_user
        self.mqtt_pass = mqtt_pass
        self._client = None

    def _callback(self, topic, msg):
        topic_s = topic.decode() if isinstance(topic, bytes) else topic
        try:
            payload = json.loads(msg)
        except ValueError:
            print("adoption: json invalid on", topic_s)
            return

        if topic_s.endswith("/challenge"):
            self._on_challenge(payload)
        elif topic_s.endswith("/config"):
            self._on_config(payload)

    def _on_challenge(self, payload):
        session_id = payload.get("session_id")
        if not session_id:
            return
        print("adoption: challenge session_id=", session_id)
        info = {
            "session_id": session_id,
            "mac_address": self.mac,
            "device_type": device_profile.DEVICE_TYPE,
            "model": device_profile.MODEL,
            "adopted_status": 0,
            "sensor_type": device_profile.SENSOR_TYPE,
            "actuator_type": device_profile.ACTUATOR_TYPE,
            "parameter_ranges": device_profile.PARAMETER_RANGES,
            "command_spec": device_profile.COMMAND_SPEC,
            "firmware_version": device_profile.FIRMWARE_VERSION,
        }
        topic = self.base + "/info"
        self._client.publish(topic, json.dumps(info), qos=1)
        print("adoption: published info ->", topic)

    def _on_config(self, payload):
        session_id = payload.get("session_id")
        nonce = payload.get("nonce")
        print("adoption: config mqtt_topic_base=", payload.get("mqtt_topic_base"))

        ack = {
            "ts": time_util.iso_utc(),
            "session_id": session_id,
            "mac_address": self.mac,
            "status": "adoption_complete",
            "nonce": nonce,
            "firmware_version": device_profile.FIRMWARE_VERSION,
        }
        topic = self.base + "/ack"
        self._client.publish(topic, json.dumps(ack), qos=1)
        print("adoption: published ack ->", topic)

        cfg_host, cfg_port = _parse_broker_url(payload.get("broker_url"))
        host = _resolve_broker_host(cfg_host, self.broker_host)

        import runtime_config

        runtime_config.save(
            {
                "adopted_status": payload.get("adopted_status", 1),
                "user_id": payload.get("user_id"),
                "device_id": payload.get("device_id"),
                "device_name": payload.get("device_name"),
                "mqtt_topic_base": payload.get("mqtt_topic_base"),
                "broker_host": host,
                "broker_port": cfg_port,
                "mqtt_username": payload.get("mqtt_username"),
                "mqtt_password": payload.get("mqtt_password"),
            }
        )
        print("adoption: saved device_config.json — rebooting to operation mode")
        import time
        import machine

        time.sleep_ms(500)
        machine.soft_reset()

    def connect(self):
        client_id = "mqtt-chat-" + self.mac_id[-8:]
        kwargs = {}
        if self.mqtt_user:
            kwargs["user"] = self.mqtt_user
        if self.mqtt_pass:
            kwargs["password"] = self.mqtt_pass

        self._client = MQTTClient(client_id, self.broker_host, self.broker_port, **kwargs)
        self._client.set_callback(self._callback)
        self._client.connect()
        self._client.subscribe(self.base + "/challenge", qos=1)
        self._client.subscribe(self.base + "/config", qos=1)
        print("adoption: listening", self.base)

    def poll(self):
        if self._client:
            self._client.check_msg()

    def disconnect(self):
        if self._client:
            try:
                self._client.disconnect()
            except OSError:
                pass
            self._client = None
