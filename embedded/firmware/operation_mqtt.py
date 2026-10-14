# Modo operação pós-adoição — telemetria simulada em {mqtt_topic_base}/telemetry

try:
    import ujson as json
except ImportError:
    import json

from umqtt.simple import MQTTClient

import device_profile
import sensor_sim
import time_util


class OperationClient:
    """Publica status online e telemetria periódica (sensor simulado)."""

    def __init__(self, cfg, mqtt_user=None, mqtt_pass=None):
        self.cfg = cfg
        self.topic_base = cfg.get("mqtt_topic_base") or ""
        self.telemetry_topic = self.topic_base + "/telemetry"
        self.status_topic = self.topic_base + "/status"
        self.broker_host = cfg.get("broker_host", "127.0.0.1")
        self.broker_port = int(cfg.get("broker_port", 1883))
        self.mqtt_user = mqtt_user or cfg.get("mqtt_username")
        self.mqtt_pass = mqtt_pass or cfg.get("mqtt_password")
        self._client = None
        self._last_publish_ms = 0
        self._interval_ms = device_profile.TELEMETRY_INTERVAL_MS

    def _client_id(self):
        device_id = self.cfg.get("device_id") or "dev"
        tail = device_id.replace("-", "")[-8:]
        return "mqtt-chat-op-" + tail

    def connect(self):
        kwargs = {}
        if self.mqtt_user:
            kwargs["user"] = self.mqtt_user
        if self.mqtt_pass:
            kwargs["password"] = self.mqtt_pass

        self._client = MQTTClient(
            self._client_id(),
            self.broker_host,
            self.broker_port,
            **kwargs,
        )
        self._client.connect()
        online = {
            "ts": time_util.iso_utc(),
            "operation_status": "online",
        }
        self._client.publish(
            self.status_topic,
            json.dumps(online),
            qos=1,
            retain=True,
        )
        print("operation: online ->", self.status_topic)
        self._publish_telemetry()
        print("operation: telemetry every", self._interval_ms, "ms ->", self.telemetry_topic)

    def _publish_telemetry(self):
        readings = sensor_sim.random_readings()
        if not readings:
            return
        payload = {
            "ts": time_util.iso_utc(),
            "readings": readings,
        }
        self._client.publish(self.telemetry_topic, json.dumps(payload), qos=0)
        print("operation: telemetry", readings)

    def poll(self):
        import time

        if not self._client:
            return
        self._client.check_msg()
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_publish_ms) >= self._interval_ms:
            self._last_publish_ms = now
            self._publish_telemetry()

    def disconnect(self):
        if self._client:
            try:
                self._client.disconnect()
            except OSError:
                pass
            self._client = None
