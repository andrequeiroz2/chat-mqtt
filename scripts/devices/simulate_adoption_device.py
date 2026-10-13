#!/usr/bin/env python3
"""Simula device em fábrica (UC-A) — handshake unclaimed/devices/{mac}/."""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from datetime import UTC, datetime

import paho.mqtt.client as mqtt

from mqtt_chat.validators.mac_address import mac_to_normalized_topic_id, normalize_mac_address


def _ts() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulador adoção UC-A (unclaimed MQTT)")
    parser.add_argument("--mac", required=True, help="MAC AA:BB:... ou 12 hex")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()

    mac = normalize_mac_address(args.mac)
    mac_id = mac_to_normalized_topic_id(mac)
    base = f"unclaimed/devices/{mac_id}"

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"adopt-sim-{mac_id[-6:]}")
    client.connect(args.host, args.port, keepalive=60)

    def on_message(_client, _userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            print(f"ignore non-json topic={topic}")
            return

        if topic.endswith("/challenge"):
            session_id = payload.get("session_id")
            print(f"challenge session_id={session_id}")
            info = {
                "session_id": session_id,
                "mac_address": mac,
                "device_type": "sensor",
                "model": "ESP32",
                "adopted_status": 0,
                "sensor_type": "DHT11",
                "parameter_ranges": {
                    "temperature": {"unit": "C", "min_reading": 0, "max_reading": 50},
                    "humidity": {"unit": "%", "min_reading": 0, "max_reading": 100},
                },
                "firmware_version": "1.0.0-sim",
            }
            info_topic = f"{base}/info"
            client.publish(info_topic, json.dumps(info), qos=1)
            print(f"published info -> {info_topic}")

        elif topic.endswith("/config"):
            session_id = payload.get("session_id")
            nonce = payload.get("nonce")
            print(f"config mqtt_topic_base={payload.get('mqtt_topic_base')}")
            ack = {
                "ts": _ts(),
                "session_id": session_id,
                "mac_address": mac,
                "status": "adoption_complete",
                "nonce": nonce,
                "firmware_version": "1.0.0-sim",
            }
            ack_topic = f"{base}/ack"
            client.publish(ack_topic, json.dumps(ack), qos=1)
            print(f"published ack -> {ack_topic}")

    client.on_message = on_message
    client.subscribe(f"{base}/challenge", qos=1)
    client.subscribe(f"{base}/config", qos=1)
    client.loop_start()
    print(f"listening {base}/challenge and /config (MAC {mac})")

    def _stop(*_args):
        client.loop_stop()
        client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
