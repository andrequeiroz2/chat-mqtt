#!/usr/bin/env python3
"""Simulador de device MQTT para PoC (sensor ou actuator).

Base de tópicos (placeholders `{user_id}` e `{device_id}` vêm da CLI):

    tenants/{user_id}/devices/{device_id}/<suffix>

Tópicos e payloads (JSON, chaves em inglês — ver docs/glossary.md):

    telemetry  — PUBLICA (sensor, loop periódico)
        ts       (string ISO-8601 UTC, sufixo Z)
        metric   (string, ex.: humidity)
        value    (number)
        unit     (string, ex.: %)

    commands   — ASSINA (sensor e actuator); backend/usuário PUBLICA aqui
        action       (string, actuator: "set")
        channel      (number, opcional, ex.: 1)
        value        (0 | 1 | boolean, actuator: off/on — ver actuator-binary-command.md)
        command_id   (string, opcional, idempotência)

    state      — PUBLICA (resposta a command ou heartbeat do actuator)
        Sensor (ACK após command):
            ts, command_id, status ("ack" | "received"), raw (string do payload)
        Actuator (ACK após "set"):
            ts, command_id, status ("applied"), value (boolean)
        Actuator (loop periódico, retain):
            ts, channel, value (boolean)

    status     — PUBLICA ao conectar/desligar (retain) + LWT offline (retain)
        ts                 (string ISO-8601)
        operation_status   (string, "online" | "offline")

QoS usado neste script: 1 em publish/subscribe; retain em status e state do actuator.
"""

from __future__ import annotations

import argparse
import json
import random
import signal
import sys
import time
from datetime import UTC, datetime
from typing import Any

import paho.mqtt.client as mqtt

from mqtt_chat.services.actuator_command_language import mqtt_set_value_to_bool

DEFAULT_USER_ID = "dev-user"
DEFAULT_DEVICE_ID = "sim-1"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 1883
DEFAULT_INTERVAL_SEC = 10.0


def topic_base(user_id: str, device_id: str) -> str:
    """Prefixo comum: tenants/{user_id}/devices/{device_id}."""
    return f"tenants/{user_id}/devices/{device_id}"


def topic_telemetry(user_id: str, device_id: str) -> str:
    """Sufixo /telemetry — device PUBLICA leituras (sensor)."""
    return f"{topic_base(user_id, device_id)}/telemetry"


def topic_commands(user_id: str, device_id: str) -> str:
    """Sufixo /commands — device ASSINA; cloud PUBLICA comandos."""
    return f"{topic_base(user_id, device_id)}/commands"


def topic_state(user_id: str, device_id: str) -> str:
    """Sufixo /state — device PUBLICA ACK ou estado (actuator)."""
    return f"{topic_base(user_id, device_id)}/state"


def topic_status(user_id: str, device_id: str) -> str:
    """Sufixo /status — device PUBLICA presença (retain)."""
    return f"{topic_base(user_id, device_id)}/status"


def print_connection_contract(args: argparse.Namespace) -> None:
    """Exibe broker, tópicos (publish/subscribe) e formato de payload na subida."""
    uid, did = args.user_id, args.device_id
    print("=== Contrato MQTT (simulador) ===")
    print(f"Broker: {args.host}:{args.port}  (MQTT TCP)")
    print(f"device_type: {args.device_type}")
    print()

    rows = [
        (
            "SUBSCRIBE",
            topic_commands(uid, did),
            '{"action":"set","channel":1,"value":0|1|true|false,"command_id":"..."}  '
            "(actuator; sensor só ACK se receber)",
        ),
        (
            "PUBLISH",
            topic_status(uid, did),
            '{"ts":"<ISO8601Z>","operation_status":"online"}  (retain, ao conectar)',
        ),
        (
            "PUBLISH",
            topic_state(uid, did),
            "ACK: {ts, command_id, status, raw[, value]} | actuator loop: {ts, channel, value} (retain)",
        ),
    ]
    if args.device_type == "sensor":
        rows.insert(
            0,
            (
                "PUBLISH",
                topic_telemetry(uid, did),
                f'{{"ts":"<ISO8601Z>","metric":"{args.metric}","value":<number>,"unit":"{args.unit}"}}  '
                f"(a cada {args.interval}s)",
            ),
        )
    else:
        rows.insert(
            0,
            (
                "PUBLISH",
                topic_state(uid, did),
                '{"ts":"<ISO8601Z>","channel":1,"value":<bool>}  (heartbeat, retain)',
            ),
        )

    for role, topic, payload in rows:
        print(f"  [{role:10}] {topic}")
        print(f"             payload: {payload}")
    print("================================")
    print()


def iso_timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def build_sensor_payload(metric: str, value: float, unit: str) -> str:
    body: dict[str, Any] = {
        "ts": iso_timestamp(),
        "metric": metric,
        "value": round(value, 2),
        "unit": unit,
    }
    return json.dumps(body, ensure_ascii=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simula um device MQTT (PoC mqtt-chat)."
    )
    parser.add_argument(
        "--device-type",
        choices=("sensor", "actuator"),
        default="sensor",
        help="Tipo do device (device_type).",
    )
    parser.add_argument("--user-id", default=DEFAULT_USER_ID, help="user_id no tópico.")
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID, help="device_id no tópico.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host do broker MQTT.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta TCP do broker.")
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_SEC,
        help="Intervalo entre telemetrias (sensor) em segundos.",
    )
    parser.add_argument(
        "--metric",
        default="humidity",
        help="Nome da métrica (sensor).",
    )
    parser.add_argument(
        "--unit",
        default="%",
        help="Unidade da métrica (sensor).",
    )
    return parser.parse_args()


class DeviceSimulator:
    """Cliente MQTT que simula telemetria e resposta a comandos."""

    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args
        self._running = True
        self._humidity = 55.0
        self._relay_on = False
        client_id = f"sim-{args.device_id}-{int(time.time())}"
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            protocol=mqtt.MQTTv311,
        )
        # Task 023-03: LWT no contrato .../status (retain, QoS 1) — sem will,
        # parada abrupta do simulador deixava o retained "online" eterno.
        self._client.will_set(
            topic_status(args.user_id, args.device_id),
            payload=json.dumps({"ts": iso_timestamp(), "operation_status": "offline"}),
            qos=1,
            retain=True,
        )
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        connect_flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        if reason_code.is_failure:
            print(f"Falha ao conectar: {reason_code}", file=sys.stderr)
            return
        cmd_topic = topic_commands(self._args.user_id, self._args.device_id)
        client.subscribe(cmd_topic, qos=1)
        print(f"Conectado; assinando {cmd_topic}")

        # /status — presença (retain); atributos: ts, operation_status
        online = json.dumps({"ts": iso_timestamp(), "operation_status": "online"})
        client.publish(
            topic_status(self._args.user_id, self._args.device_id),
            online,
            qos=1,
            retain=True,
        )

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        raw = message.payload.decode("utf-8", errors="replace")
        print(f"Comando recebido em {message.topic}: {raw}")

        # /state — ACK do comando; atributos: ts, command_id, status, raw; actuator + value
        state_topic = topic_state(self._args.user_id, self._args.device_id)
        ack: dict[str, Any] = {
            "ts": iso_timestamp(),
            "command_id": None,
            "status": "received",
            "raw": raw,
        }

        if self._args.device_type == "actuator":
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {}
            if payload.get("action") == "set":
                try:
                    self._relay_on = mqtt_set_value_to_bool(payload.get("value", 0))
                except ValueError:
                    ack["status"] = "rejected"
                    ack["command_id"] = payload.get("command_id")
                else:
                    ack["status"] = "applied"
                    ack["command_id"] = payload.get("command_id")
                    ack["value"] = self._relay_on
        else:
            ack["status"] = "ack"

        client.publish(state_topic, json.dumps(ack), qos=1)

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        args = self._args
        self._client.connect(args.host, args.port, keepalive=60)
        self._client.loop_start()

        try:
            while self._running:
                if args.device_type == "sensor":
                    # /telemetry — ts, metric, value, unit
                    self._humidity += random.uniform(-1.5, 1.5)
                    self._humidity = max(30.0, min(90.0, self._humidity))
                    payload = build_sensor_payload(args.metric, self._humidity, args.unit)
                    tel_topic = topic_telemetry(args.user_id, args.device_id)
                    self._client.publish(tel_topic, payload, qos=1)
                    print(f"Telemetria → {tel_topic}: {payload}")
                else:
                    # /state (actuator, retain) — ts, channel, value
                    state = json.dumps(
                        {
                            "ts": iso_timestamp(),
                            "channel": 1,
                            "value": self._relay_on,
                        }
                    )
                    self._client.publish(
                        topic_state(args.user_id, args.device_id),
                        state,
                        qos=1,
                        retain=True,
                    )
                    print(f"Estado (actuator): {state}")

                time.sleep(args.interval)
        finally:
            # Task 023-03: parada graciosa nao dispara LWT — publicar offline
            # retained e garantir entrega antes de desligar o loop.
            try:
                offline = json.dumps(
                    {"ts": iso_timestamp(), "operation_status": "offline"}
                )
                info = self._client.publish(
                    topic_status(args.user_id, args.device_id),
                    offline,
                    qos=1,
                    retain=True,
                )
                info.wait_for_publish(timeout=5)
            except (OSError, ValueError, RuntimeError) as exc:
                print(f"Aviso: falha ao publicar offline na saida: {exc}", file=sys.stderr)
            self._client.loop_stop()
            self._client.disconnect()


def main() -> None:
    args = parse_args()
    print_connection_contract(args)
    simulator = DeviceSimulator(args)

    def handle_signal(_signum: int, _frame: Any) -> None:
        print("\nEncerrando simulador…")
        simulator.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    simulator.run()


if __name__ == "__main__":
    main()
