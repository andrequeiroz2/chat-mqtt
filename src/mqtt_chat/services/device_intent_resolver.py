"""Resolver determinístico de intenção e device (policy G1–G12)."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from mqtt_chat.schemas.conversation_context import (
    ClarifyOption,
    Connectivity,
    ConversationContext,
    DeviceSnapshotEntry,
    DeviceType,
)
from mqtt_chat.schemas.device_intent import ChatIntent, DeviceIntentResolverResult
from mqtt_chat.services.actuator_command_language import (
    parse_power_intent,
    power_to_binary_value,
    power_verb_pt,
    utterance_has_actuator_command_verbs,
    utterance_suggests_actuator_target,
)

_HISTORY_PATTERNS = (
    r"grafico",
    r"historico",
    r"tendencia",
    r"ultimos\s+\d+\s+dias",
    r"ultima\s+semana",
    r"evolucao",
    r"\bchart\b",
    r"plot",
    r"serie\s+temporal",
)
_READ_PATTERNS = (
    r"últim[a]?\s+leitura",
    r"ultim[a]?\s+leitura",
    r"telemetria",
    r"temperatura",
    r"umidade",
    r"leitura",
    r"últim[a]?\s+temperatura",
    r"ultim[a]?\s+temperatura",
    r"valor(es)?\s+(atual|registrad)",
)
_REALTIME_PATTERNS = (
    r"tempo\s+real",
    r"ao\s+vivo",
    r"acompanhar",
    r"stream",
    r"monitorar",
    r"enquanto\s+convers",
)
# Inventário (G13): "quantos devices tenho?", "quais são os meus sensores?",
# "tenho algum sensor registrado?", "liste meus devices".
_INVENTORY_PATTERNS = (
    r"quant(os|as)\b.{0,25}\b(dispositivo|device|sensor|atuador)",
    r"quais\s+(sao\s+)?(os\s+)?(meus\s+)?(dispositivos|devices|sensores|atuadores)",
    r"\b(tenho|possuo|temos|tem)\s+(algum|alguma|alguns|algumas|um|uma)?\s*"
    r"(dispositivo|device|sensor|atuador)",
    r"\b(liste|listar|listar|mostre|mostrar|ver)\s+(os\s+)?(meus\s+)?"
    r"(dispositivos|devices|sensores|atuadores)",
)
# Metadado de adoção (G14): "que dia ele foi registrado?", "quando adotei?",
# "em que data cadastrei o sensor?".
_METADATA_ADOPTION_PATTERNS = (
    r"(que dia|quando|em que data)\b.{0,30}\b(registr|adot|cadastr)",
    r"\bdata\s+(de|da)\s+(adocao|registro|cadastro)",
)


def detect_adoption_date_question(message: str) -> bool:
    """Pergunta sobre data de adoção/registro do device (G14)."""
    text = _normalize_text(message)
    return any(re.search(p, text) for p in _METADATA_ADOPTION_PATTERNS)
_DEVICE_IDENTITY_QUESTION_PATTERNS = (
    re.compile(r"\bmac\b", re.IGNORECASE),
    re.compile(r"endere[cç]o\s+mac", re.IGNORECASE),
    re.compile(r"mac\s*address", re.IGNORECASE),
    re.compile(r"endere[cç]o\s+f[ií]sico", re.IGNORECASE),
    re.compile(r"\bip\b", re.IGNORECASE),
    re.compile(r"endere[cç]o\s+ip", re.IGNORECASE),
    re.compile(r"\bipv4\b", re.IGNORECASE),
    re.compile(r"qual\s+(o\s+)?ip", re.IGNORECASE),
    re.compile(r"ip\s+do\s+(meu\s+)?(sensor|atuador|dispositivo)", re.IGNORECASE),
)


def is_device_identity_not_in_chat_question(message: str) -> bool:
    """MAC/IP local — não exposto em list_devices (contrato MCP v1)."""
    return any(p.search(message) for p in _DEVICE_IDENTITY_QUESTION_PATTERNS)


def is_mac_address_question(message: str) -> bool:
    """Alias retrocompatível para testes."""
    return is_device_identity_not_in_chat_question(message)


_MQTT_TOPIC_QUESTION_PATTERNS = (
    re.compile(r"\bt[oó]pico\b", re.IGNORECASE),
    re.compile(r"\btopic\b", re.IGNORECASE),
    re.compile(r"\bmqtt_topic_base\b", re.IGNORECASE),
    re.compile(r"base\s+(de\s+)?t[oó]pic", re.IGNORECASE),
)


def is_mqtt_topic_question(message: str) -> bool:
    """Pergunta sobre tópicos MQTT do device (não confundir com MAC/IP)."""
    if is_device_identity_not_in_chat_question(message):
        return False
    return any(p.search(message) for p in _MQTT_TOPIC_QUESTION_PATTERNS)


def _device_type_hint_from_message(message: str) -> DeviceType | None:
    """Atuador vs sensor explícito na frase (ex.: tópico do meu atuador)."""
    text = _normalize_text(message)
    wants_actuator = bool(re.search(r"\batuador(es)?\b|\bactuator\b|\brele\b|\brel[eé]\b", text))
    wants_sensor = bool(re.search(r"\bsensor(es)?\b", text))
    if wants_actuator and not wants_sensor:
        return "actuator"
    if wants_sensor and not wants_actuator:
        return "sensor"
    return None


def _resolve_single_device_for_topic(
    message: str,
    context: ConversationContext,
) -> (
    DeviceSnapshotEntry
    | list[DeviceSnapshotEntry]
    | tuple[Literal["missing_type"], DeviceType]
    | None
):
    """
    Um device alvo, None se inventário vazio, lista se ambíguo, ou missing_type.
    """
    snapshot = context.device_snapshot
    type_hint = _device_type_hint_from_message(message)
    pool = snapshot
    if type_hint == "actuator":
        pool = _actuators(snapshot)
        if not pool:
            return ("missing_type", "actuator")
    elif type_hint == "sensor":
        pool = _sensors(snapshot)
        if not pool:
            return ("missing_type", "sensor")

    named = _devices_named_in_message(pool, message)
    if len(named) == 1:
        return named[0]
    if len(named) > 1:
        return named

    focus = _entry_by_id(pool, context.session_focus_device_id)
    if focus is not None:
        return focus
    if len(pool) == 1:
        return pool[0]
    if len(pool) >= 2:
        return pool
    return None


def _normalize_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in folded if not unicodedata.combining(ch))


def detect_inventory_hint(message: str) -> DeviceType | Literal["all"] | None:
    """
    Pergunta de inventário (quantos/quais/tenho devices/sensores/atuadores)?

    Retorna o recorte pedido ("sensor", "actuator" ou "all"); None se não for
    pergunta de inventário. Padrões exigem o tipo explícito para não roubar
    intents de leitura (ex.: "qual a última leitura do meu sensor?").
    """
    text = _normalize_text(message)
    if not any(re.search(p, text) for p in _INVENTORY_PATTERNS):
        return None
    return _device_type_hint_from_message(message) or "all"


def detect_chat_intent(message: str) -> ChatIntent | None:
    """Heurística MVP para intenções cobertas pelo resolver."""
    text = _normalize_text(message)
    history = any(re.search(p, text) for p in _HISTORY_PATTERNS)
    if history:
        return "telemetry_history"
    realtime = any(re.search(p, text) for p in _REALTIME_PATTERNS)
    read = any(re.search(p, text) for p in _READ_PATTERNS)
    if realtime and not read:
        return "realtime"
    if read and not realtime:
        return "read_telemetry"
    if realtime and read:
        if re.search(r"tempo\s+real|ao\s+vivo", text):
            return "realtime"
        return "read_telemetry"
    return None


def connectivity_from_status(operation_status: str | None) -> Connectivity:
    if operation_status == "online":
        return "online"
    if operation_status == "offline":
        return "offline"
    return "unknown"


def _name_in_utterance(device_name: str | None, message: str) -> bool:
    if not device_name or len(device_name.strip()) < 2:
        return False
    return _normalize_text(device_name.strip()) in _normalize_text(message)


def _devices_named_in_message(
    snapshot: list[DeviceSnapshotEntry],
    message: str,
) -> list[DeviceSnapshotEntry]:
    return [d for d in snapshot if _name_in_utterance(d.device_name, message)]


def _sensors(snapshot: list[DeviceSnapshotEntry]) -> list[DeviceSnapshotEntry]:
    return [d for d in snapshot if d.device_type == "sensor"]


def _actuators(snapshot: list[DeviceSnapshotEntry]) -> list[DeviceSnapshotEntry]:
    return [d for d in snapshot if d.device_type == "actuator"]


def _entry_by_id(
    snapshot: list[DeviceSnapshotEntry],
    device_id: str | None,
) -> DeviceSnapshotEntry | None:
    if not device_id:
        return None
    for item in snapshot:
        if item.device_id == device_id:
            return item
    return None


def _clarify_from_entries(
    entries: list[DeviceSnapshotEntry],
    *,
    trigger_id: str,
) -> DeviceIntentResolverResult:
    return DeviceIntentResolverResult(
        outcome="clarify",
        trigger_id=trigger_id,
        clarify_options=[
            ClarifyOption(
                device_id=e.device_id,
                device_name=e.device_name,
                device_type=e.device_type,
            )
            for e in entries
        ],
    )


def _execute_sensor(
    entry: DeviceSnapshotEntry,
    intent: ChatIntent,
    *,
    trigger_id: str,
) -> DeviceIntentResolverResult:
    conn = connectivity_from_status(entry.operation_status)
    if intent == "realtime" and conn != "online":
        template = "T5" if conn == "offline" else "T6"
        trigger = "G12"
        return DeviceIntentResolverResult(
            outcome="instruct",
            intent=intent,
            trigger_id=trigger,
            template_id=template,
            device_id=entry.device_id,
            device_name=entry.device_name,
            device_type="sensor",
            connectivity=conn,
            instruct_kind=None,
        )
    return DeviceIntentResolverResult(
        outcome="execute",
        intent=intent,
        trigger_id=trigger_id,
        device_id=entry.device_id,
        device_name=entry.device_name,
        device_type="sensor",
        connectivity=conn,
        template_id="T1" if intent == "read_telemetry" and conn == "offline" else None,
    )


def _resolve_actuator_command(
    message: str,
    context: ConversationContext,
) -> DeviceIntentResolverResult:
    """G10 — comando binário 0/1 com confirmação pendente."""
    snapshot = context.device_snapshot
    actuators = _actuators(snapshot)
    named = _devices_named_in_message(snapshot, message)
    named_actuators = [d for d in named if d.device_type == "actuator"]

    target: DeviceSnapshotEntry | None = None
    if len(named_actuators) == 1:
        target = named_actuators[0]
    elif len(named_actuators) > 1:
        return _clarify_from_entries(named_actuators, trigger_id="G5")

    if target is None and len(actuators) == 1:
        target = actuators[0]

    if target is None:
        focus = _entry_by_id(snapshot, context.session_focus_device_id)
        if focus and focus.device_type == "actuator":
            target = focus

    if target is None and len(actuators) >= 2:
        return _clarify_from_entries(actuators, trigger_id="G3")

    if target is None:
        return DeviceIntentResolverResult(outcome="pass_through", intent="actuator_command")

    power = parse_power_intent(message)
    if power is None:
        return DeviceIntentResolverResult(
            outcome="instruct",
            intent="actuator_command",
            trigger_id="G10",
            template_id="T-COMMAND-POWER-ASK",
            device_id=target.device_id,
            device_name=target.device_name,
            device_type="actuator",
            instruct_kind="actuator_power_unknown",
        )

    binary = power_to_binary_value(power)
    return DeviceIntentResolverResult(
        outcome="instruct",
        intent="actuator_command",
        trigger_id="G10",
        template_id="T-COMMAND-CONFIRM",
        device_id=target.device_id,
        device_name=target.device_name,
        device_type="actuator",
        binary_value=binary,
        verb_pt=power_verb_pt(power),
    )


def _resolve_adoption_date(
    message: str,
    context: ConversationContext,
) -> DeviceIntentResolverResult:
    """G14 — alvo: nome citado → foco de sessão → device único; ≥2 sem alvo → clarify."""
    snapshot = context.device_snapshot
    named = _devices_named_in_message(snapshot, message)

    target: DeviceSnapshotEntry | None = None
    if len(named) == 1:
        target = named[0]
    elif len(named) > 1:
        return _clarify_from_entries(named, trigger_id="G14")

    if target is None:
        target = _entry_by_id(snapshot, context.session_focus_device_id)
    if target is None and len(snapshot) == 1:
        target = snapshot[0]
    if target is None and len(snapshot) >= 2:
        return _clarify_from_entries(snapshot, trigger_id="G14")

    if target is None:
        return DeviceIntentResolverResult(
            outcome="execute",
            intent="device_metadata",
            trigger_id="G14",
        )
    return DeviceIntentResolverResult(
        outcome="execute",
        intent="device_metadata",
        trigger_id="G14",
        device_id=target.device_id,
        device_name=target.device_name,
        device_type=target.device_type,
    )


def resolve_device_intent(
    message: str,
    context: ConversationContext,
) -> DeviceIntentResolverResult:
    """
    Aplica gatilhos G1–G12 + G10 (comando atuador) sobre snapshot + foco.

    Retorna pass_through se nenhuma intenção reconhecida.
    """
    if is_device_identity_not_in_chat_question(message):
        return DeviceIntentResolverResult(
            outcome="instruct",
            trigger_id="NETWORK-NOT-IN-CHAT",
            template_id="T-NETWORK-NOT-IN-CHAT",
        )

    if is_mqtt_topic_question(message):
        target = _resolve_single_device_for_topic(message, context)
        if (
            isinstance(target, tuple)
            and len(target) == 2
            and target[0] == "missing_type"
        ):
            missing = target[1]
            return DeviceIntentResolverResult(
                outcome="instruct",
                trigger_id="MQTT-TOPIC",
                template_id="T-MQTT-TOPICS-TYPE-MISSING",
                device_type=missing,
            )
        if isinstance(target, list):
            return _clarify_from_entries(target, trigger_id="MQTT-TOPIC")
        if target is None:
            return DeviceIntentResolverResult(
                outcome="instruct",
                trigger_id="MQTT-TOPIC",
                template_id="T-MQTT-TOPICS-NO-DEVICE",
            )
        return DeviceIntentResolverResult(
            outcome="instruct",
            trigger_id="MQTT-TOPIC",
            template_id="T-MQTT-TOPICS",
            device_id=target.device_id,
            device_name=target.device_name,
            device_type=target.device_type,
        )

    # G13 — inventário: resposta 100% a partir do snapshot (sem LLM, sem tools).
    inventory_hint = detect_inventory_hint(message)
    if inventory_hint is not None:
        return DeviceIntentResolverResult(
            outcome="execute",
            intent="list_devices",
            trigger_id="G13",
            device_type=None if inventory_hint == "all" else inventory_hint,
        )

    # G14 — metadado de adoção: resposta do snapshot (adopted_at), sem LLM.
    if detect_adoption_date_question(message):
        return _resolve_adoption_date(message, context)

    intent = detect_chat_intent(message)
    if intent is None:
        if utterance_suggests_actuator_target(message) or utterance_has_actuator_command_verbs(
            message
        ):
            return _resolve_actuator_command(message, context)
        return DeviceIntentResolverResult(outcome="pass_through")

    snapshot = context.device_snapshot
    sensors = _sensors(snapshot)
    actuators = _actuators(snapshot)
    named = _devices_named_in_message(snapshot, message)

    if intent in ("read_telemetry", "telemetry_history"):
        named_sensors = [d for d in named if d.device_type == "sensor"]
        named_actuators = [d for d in named if d.device_type == "actuator"]

        if len(named) == 1 and named_actuators and not named_sensors:
            entry = named_actuators[0]
            return DeviceIntentResolverResult(
                outcome="instruct",
                intent=intent,
                trigger_id="G7",
                template_id=None,
                device_id=entry.device_id,
                device_name=entry.device_name,
                device_type="actuator",
                instruct_kind="actuator_no_telemetry",
            )

        if len(named_sensors) == 1 and len(named) == 1:
            return _execute_sensor(named_sensors[0], intent, trigger_id="G4")

        if len(named_sensors) > 1 or (len(named) > 1 and named_sensors):
            return _clarify_from_entries(named_sensors or named, trigger_id="G5")

        if len(sensors) == 1 and len(actuators) >= 1:
            return DeviceIntentResolverResult(
                outcome="clarify",
                intent=intent,
                trigger_id="G2",
                template_id="T-INTENT-MIXED",
                device_id=sensors[0].device_id,
                device_name=sensors[0].device_name,
                device_type="sensor",
                clarify_options=[
                    ClarifyOption(
                        device_id=sensors[0].device_id,
                        device_name=sensors[0].device_name,
                        device_type="sensor",
                    ),
                    *[
                        ClarifyOption(
                            device_id=a.device_id,
                            device_name=a.device_name,
                            device_type="actuator",
                        )
                        for a in actuators
                    ],
                ],
            )

        if len(sensors) == 1 and len(actuators) == 0:
            return _execute_sensor(sensors[0], intent, trigger_id="G1")

        focus = _entry_by_id(snapshot, context.session_focus_device_id)
        if (
            focus
            and focus.device_type == "sensor"
            and len(named) == 0
            and len(sensors) >= 2
        ):
            return _execute_sensor(focus, intent, trigger_id="G6")

        if len(sensors) >= 2:
            return _clarify_from_entries(sensors, trigger_id="G3")

        if len(sensors) == 0:
            return DeviceIntentResolverResult(
                outcome="pass_through",
                intent=intent,
            )

    if intent == "realtime":
        named_sensors = [d for d in named if d.device_type == "sensor"]
        if len(named_sensors) == 1:
            return _execute_sensor(named_sensors[0], intent, trigger_id="G4")
        if len(named_sensors) > 1:
            return _clarify_from_entries(named_sensors, trigger_id="G5")

        focus = _entry_by_id(snapshot, context.session_focus_device_id)
        if focus and focus.device_type == "sensor" and len(named) == 0 and len(sensors) >= 2:
            return _execute_sensor(focus, intent, trigger_id="G6")

        if len(sensors) == 1:
            return _execute_sensor(sensors[0], intent, trigger_id="G1")

        if len(sensors) >= 2:
            return _clarify_from_entries(sensors, trigger_id="G3")

    if utterance_has_actuator_command_verbs(message):
        return _resolve_actuator_command(message, context)

    return DeviceIntentResolverResult(outcome="pass_through", intent=intent)
