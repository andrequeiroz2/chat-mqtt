"""Turno de chat curto-circuitado pelo resolver (policy 011)."""

from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from typing import TYPE_CHECKING

from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.chat import ChatScope, RealtimeTelemetrySuggestedUi, SuggestedUiAction
from mqtt_chat.schemas.actuator_command import PendingActuatorCommand
from mqtt_chat.schemas.conversation_context import ConversationContext, DeviceSnapshotEntry
from mqtt_chat.schemas.device_intent import DeviceIntentResolverResult
from mqtt_chat.schemas.telemetry_tools import ReadLatestTelemetryInput, TelemetryHistoryInput
from mqtt_chat.services import conversation_templates as templates
from mqtt_chat.services import telemetry_queries as telemetry_queries_service
from mqtt_chat.schemas.turn_outcome import TurnOutcome
from mqtt_chat.services.conversation_context import (
    refresh_conversation_context,
    save_conversation_context,
    set_session_focus,
)
from mqtt_chat.services.actuator_command_service import (
    ActuatorCommandError,
    publish_actuator_command,
)
from mqtt_chat.services.chat_history import append_turn

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient

    from mqtt_chat.agent.deps import UserDeps

logger = logging.getLogger(__name__)


def _find_entry(
    context: ConversationContext,
    device_id: str | None,
) -> DeviceSnapshotEntry | None:
    if not device_id:
        return None
    for item in context.device_snapshot:
        if item.device_id == device_id:
            return item
    return None


def _apply_focus(
    context: ConversationContext,
    device_id: str | None,
    *,
    user_message: str,
    entry: DeviceSnapshotEntry | None,
) -> None:
    if not device_id:
        return
    reason = "user_mention"
    if entry and entry.device_name and entry.device_name.lower() in user_message.lower():
        reason = "user_mention"
    set_session_focus(context, device_id, reason)  # type: ignore[arg-type]


def _reply_from_clarify(resolved: DeviceIntentResolverResult) -> str:
    if resolved.template_id == "T-INTENT-MIXED" and resolved.clarify_options:
        sensor_opt = next(
            (o for o in resolved.clarify_options if o.device_type == "sensor"),
            None,
        )
        actuators = [
            templates.display_device_name(o.device_name, device_type="actuator")
            for o in resolved.clarify_options
            if o.device_type == "actuator"
        ]
        if sensor_opt:
            return templates.template_intent_mixed(
                sensor_name=sensor_opt.device_name,
                actuator_labels=actuators,
            )
    options = [(o.device_name, o.device_type) for o in resolved.clarify_options]
    if options and all(o[1] == "sensor" for o in options):
        return templates.template_clarify_sensors([o[0] for o in options])
    return templates.template_clarify_devices(options)


def _reply_mqtt_topics(
    db: FirestoreClient,
    user_id: str,
    entry: DeviceSnapshotEntry | None,
) -> str:
    if entry is None:
        return templates.template_mqtt_topics_no_device()
    snap = db.collection("devices").document(entry.device_id).get()
    if not snap.exists:
        return templates.template_mqtt_topics_no_device()
    data = snap.to_dict() or {}
    if data.get("user_id") != user_id:
        return templates.template_mqtt_topics_no_device()
    readings_block: str | None = None
    if entry.device_type == "sensor":
        try:
            result = telemetry_queries_service.read_latest_telemetry(
                db,
                user_id,
                ReadLatestTelemetryInput(device_id=entry.device_id),
            )
            if result.has_telemetry:
                readings_block = templates.format_readings_block(result.readings)
        except telemetry_queries_service.ReadLatestTelemetryError:
            readings_block = None
    return templates.template_mqtt_topics(
        device_name=entry.device_name,
        device_type=entry.device_type,
        mqtt_topic_base=data.get("mqtt_topic_base")
        if isinstance(data.get("mqtt_topic_base"), str)
        else None,
        model=data.get("model") if isinstance(data.get("model"), str) else None,
        operation_status=entry.operation_status,
        readings_block=readings_block,
    )


def _normalize_resolver_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in folded if not unicodedata.combining(ch))


def _history_days_from_message(message: str) -> int:
    text = _normalize_resolver_text(message)
    match = re.search(r"ultimos\s+(\d+)\s+dias", text)
    if match:
        return max(1, min(30, int(match.group(1))))
    if re.search(r"ultim[oa]\s+dia\b", text):
        return 1
    if "semana" in text or "7 dias" in text:
        return 7
    return 7


def _history_last_day_with_data(message: str) -> bool:
    text = _normalize_resolver_text(message)
    return bool(
        re.search(r"ultim[oa]\s+dia.*registr", text)
        or re.search(r"dia em que existem registr", text)
        or re.search(r"ultim[oa]\s+dia em que", text)
    )


def _history_metric_from_message(message: str) -> str | None:
    text = _normalize_resolver_text(message)
    if "temperatura" in text or "temperature" in text:
        return "temperature"
    if "umidade" in text or "humidity" in text:
        return "humidity"
    return None


def _reply_from_history_execute(
    db: FirestoreClient,
    user_id: str,
    resolved: DeviceIntentResolverResult,
    user_message: str,
) -> tuple[SuggestedUiAction | None, str]:
    last_day = _history_last_day_with_data(user_message)
    params = TelemetryHistoryInput(
        device_id=resolved.device_id,
        metric=_history_metric_from_message(user_message),
        days=30 if last_day else _history_days_from_message(user_message),
        last_day_with_data=last_day,
    )
    try:
        result, chart_ui = telemetry_queries_service.get_telemetry_history(
            db,
            user_id,
            params,
        )
    except telemetry_queries_service.ReadLatestTelemetryError as exc:
        if exc.code == "telemetry_history_empty":
            label = templates.display_device_name(resolved.device_name, device_type="sensor")
            return (
                None,
                f"Não há leituras no período para montar o gráfico do sensor **{label}**. "
                "Confirme se o simulador ou device já enviou telemetria nos últimos dias.",
            )
        return (
            None,
            "Não consegui obter o histórico desse dispositivo. "
            "Verifique o nome na sua lista ou tente de novo.",
        )

    label = templates.display_device_name(result.device_name, device_type="sensor")
    metric_pt = {"temperature": "temperatura", "humidity": "umidade"}.get(
        result.metric,
        result.metric,
    )
    unit_suffix = f" {result.unit}" if result.unit else ""
    reply = (
        f"Abri o gráfico de **{metric_pt}{unit_suffix}** do sensor **{label}** "
        f"({result.period_label}, {result.point_count} pontos)."
    )
    return chart_ui, reply


def _reply_from_read_execute(
    db: FirestoreClient,
    user_id: str,
    resolved: DeviceIntentResolverResult,
    entry: DeviceSnapshotEntry | None,
) -> str:
    params = ReadLatestTelemetryInput(device_id=resolved.device_id)
    try:
        result = telemetry_queries_service.read_latest_telemetry(db, user_id, params)
    except telemetry_queries_service.ReadLatestTelemetryError:
        return (
            "Não consegui ler a telemetria desse dispositivo. "
            "Verifique o nome na sua lista ou tente de novo."
        )

    conn = result.connectivity
    readings_block = templates.format_readings_block(result.readings)
    name = result.device_name
    last_seen = result.last_seen_at or (entry.last_seen_at if entry else None)

    if conn == "offline":
        if result.has_telemetry and result.received_at:
            return templates.template_t1(
                device_name=name,
                received_at=result.received_at,
                readings_block=readings_block,
                last_seen_at=last_seen,
            )
        return templates.template_t2(
            device_name=name,
            last_seen_at=last_seen,
        )
    if conn == "unknown":
        if result.has_telemetry and result.received_at:
            return templates.template_t3(
                device_name=name,
                received_at=result.received_at,
                readings_block=readings_block,
            )
        return templates.template_t4(device_name=name)

    if not result.has_telemetry:
        label = templates.display_device_name(name, device_type="sensor")
        return (
            f"O sensor **{label}** está online, mas **ainda não há leituras registradas** "
            f"na plataforma."
        )
    received = result.received_at or "—"
    label = templates.display_device_name(name, device_type="sensor")
    return (
        f"**Última leitura registrada** do sensor **{label}** (em **{received}**): "
        f"{readings_block}."
    )


def execute_resolver_turn(
    db: FirestoreClient,
    deps: UserDeps,
    user_message: str,
    context: ConversationContext,
    resolved: DeviceIntentResolverResult,
    max_messages: int,
) -> TurnOutcome:
    """Materializa clarify/instruct/execute sem chamar o LLM."""
    log_event(
        logger,
        logging.INFO,
        events.CHAT_RESOLVER_OUTCOME,
        "Chat resolver short-circuit",
        user_id=deps.user_id,
        session_id=deps.session_id,
        outcome=resolved.outcome,
        trigger_id=resolved.trigger_id,
        intent=resolved.intent,
    )

    entry = _find_entry(context, resolved.device_id)
    suggested: SuggestedUiAction | None = None
    reply = ""

    if resolved.outcome == "clarify":
        reply = _reply_from_clarify(resolved)
    elif resolved.outcome == "instruct":
        if resolved.template_id == "T5":
            reply = templates.template_t5(
                device_name=resolved.device_name,
                last_seen_at=entry.last_seen_at if entry else None,
            )
        elif resolved.template_id == "T6":
            reply = templates.template_t6(device_name=resolved.device_name)
        elif resolved.instruct_kind == "actuator_no_telemetry":
            reply = templates.template_actuator_instruct(device_name=resolved.device_name)
        elif resolved.template_id == "T-COMMAND-CONFIRM":
            assert resolved.binary_value is not None and resolved.verb_pt
            context.pending_actuator_command = PendingActuatorCommand(
                device_id=resolved.device_id or "",
                device_name=resolved.device_name,
                binary_value=resolved.binary_value,
                verb_pt=resolved.verb_pt,
            )
            reply = templates.template_command_confirm(
                device_name=resolved.device_name,
                verb_pt=resolved.verb_pt,
                binary_value=resolved.binary_value,
            )
        elif resolved.template_id == "T-COMMAND-POWER-ASK":
            reply = templates.template_command_power_ask(device_name=resolved.device_name)
        elif resolved.template_id in ("T-MAC-NOT-IN-CHAT", "T-NETWORK-NOT-IN-CHAT"):
            reply = templates.template_network_not_in_chat()
        elif resolved.template_id == "T-MQTT-TOPICS-NO-DEVICE":
            reply = templates.template_mqtt_topics_no_device()
        elif resolved.template_id == "T-MQTT-TOPICS-TYPE-MISSING":
            dtype = resolved.device_type or "sensor"
            reply = templates.template_mqtt_topics_type_missing(dtype)  # type: ignore[arg-type]
        elif resolved.template_id == "T-MQTT-TOPICS":
            reply = _reply_mqtt_topics(db, deps.user_id, entry)
        else:
            reply = _reply_from_clarify(resolved)
    elif resolved.outcome == "execute" and resolved.intent == "read_telemetry":
        reply = _reply_from_read_execute(db, deps.user_id, resolved, entry)
    elif resolved.outcome == "execute" and resolved.intent == "telemetry_history":
        suggested, reply = _reply_from_history_execute(
            db,
            deps.user_id,
            resolved,
            user_message,
        )
    elif resolved.outcome == "execute" and resolved.intent == "realtime":
        suggested = RealtimeTelemetrySuggestedUi(
            device_id=resolved.device_id or "",
            device_name=resolved.device_name,
        )
        reply = templates.template_realtime_started(device_name=resolved.device_name)
    else:
        reply = "Não foi possível concluir o pedido. Tente especificar o sensor."

    _apply_focus(context, resolved.device_id, user_message=user_message, entry=entry)
    save_conversation_context(db, deps.user_id, deps.session_id, context)

    append_turn(
        db,
        deps.user_id,
        deps.session_id,
        user_message,
        reply,
        max_messages,
    )
    scope: ChatScope = "product"
    return TurnOutcome(
        reply=reply,
        persist=True,
        scope=scope,
        suggested_ui=suggested,
    )


async def execute_pending_actuator_command(
    db: FirestoreClient,
    deps: UserDeps,
    user_message: str,
    context: ConversationContext,
    max_messages: int,
    publish_queue: asyncio.Queue[tuple[str, bytes]] | None,
) -> TurnOutcome | None:
    """Confirma ou cancela pending_actuator_command; None se não aplicável."""
    pending = context.pending_actuator_command
    if pending is None:
        return None

    from mqtt_chat.services.actuator_command_language import (
        is_cancellation_utterance,
        is_confirmation_utterance,
    )

    if is_cancellation_utterance(user_message):
        context.pending_actuator_command = None
        save_conversation_context(db, deps.user_id, deps.session_id, context)
        reply = templates.template_command_cancelled()
        append_turn(db, deps.user_id, deps.session_id, user_message, reply, max_messages)
        return TurnOutcome(reply=reply, persist=True, scope="product")

    if not is_confirmation_utterance(user_message):
        return None

    try:
        await publish_actuator_command(
            db,
            deps.user_id,
            pending.device_id,
            pending.binary_value,
            publish_queue,
        )
    except ActuatorCommandError:
        context.pending_actuator_command = None
        save_conversation_context(db, deps.user_id, deps.session_id, context)
        reply = "Não foi possível enviar o comando agora. Tente de novo em instantes."
        append_turn(db, deps.user_id, deps.session_id, user_message, reply, max_messages)
        return TurnOutcome(reply=reply, persist=True, scope="product")

    reply = templates.template_command_sent(
        device_name=pending.device_name,
        verb_pt=pending.verb_pt,
        binary_value=pending.binary_value,
    )
    set_session_focus(context, pending.device_id, "user_mention")
    context.pending_actuator_command = None
    save_conversation_context(db, deps.user_id, deps.session_id, context)
    from mqtt_chat.config.settings import get_settings

    cap = get_settings().chat_device_snapshot_cap
    refresh_conversation_context(
        db,
        deps.user_id,
        deps.session_id,
        cap=cap,
        keep_focus=True,
    )
    append_turn(db, deps.user_id, deps.session_id, user_message, reply, max_messages)
    return TurnOutcome(reply=reply, persist=True, scope="product")
