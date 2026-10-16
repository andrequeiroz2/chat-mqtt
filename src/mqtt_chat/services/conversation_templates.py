"""Templates PT fixos (docs/chat-conversational-policy.md §8)."""

from __future__ import annotations

from typing import Literal

from mqtt_chat.schemas.telemetry import ReadingItem

DeviceTypeLabel = Literal["sensor", "actuator"]


def display_device_name(
    name: str | None,
    *,
    device_type: DeviceTypeLabel | None = None,
    list_index: int | None = None,
) -> str:
    """
    Rótulo amigável para o usuário.

    Nunca expõe ``device_id`` (UUID); ver policy UX.
    """
    cleaned = (name or "").strip()
    if cleaned:
        return cleaned
    if list_index is not None:
        kind = (
            "Sensor"
            if device_type == "sensor"
            else "Atuador"
            if device_type == "actuator"
            else "Dispositivo"
        )
        return f"{kind} {list_index}"
    if device_type == "sensor":
        return "seu sensor"
    if device_type == "actuator":
        return "seu atuador"
    return "seu dispositivo"


def _last_seen_suffix(last_seen_at: str | None) -> str:
    if not last_seen_at:
        return ""
    return f" (última atividade em **{last_seen_at}**)"


def format_readings_block(readings: list[ReadingItem]) -> str:
    """Resumo curto de métricas para templates."""
    parts: list[str] = []
    for item in readings:
        unit = f" {item.unit}" if item.unit else ""
        parts.append(f"{item.metric} {item.value:g}{unit}".replace("_", " "))
    return ", ".join(parts) if parts else "—"


def template_t1(
    *,
    device_name: str | None,
    received_at: str,
    readings_block: str,
    last_seen_at: str | None,
) -> str:
    name = display_device_name(device_name, device_type="sensor")
    suffix = _last_seen_suffix(last_seen_at)
    return (
        f"**Última leitura registrada** do sensor **{name}** (em **{received_at}**): "
        f"{readings_block}.\n"
        f"**Atenção:** o sensor está **offline** no momento{suffix}. "
        f"Esse valor **não** é ao vivo."
    )


def template_t2(
    *,
    device_name: str | None,
    last_seen_at: str | None,
) -> str:
    name = display_device_name(device_name, device_type="sensor")
    suffix = _last_seen_suffix(last_seen_at)
    return (
        f"O sensor **{name}** está **offline**{suffix} e **ainda não há leituras registradas** "
        f"na plataforma (ou nenhuma foi guardada). Quando o sensor voltar a publicar, "
        f"as leituras aparecerão aqui."
    )


def template_t3(
    *,
    device_name: str | None,
    received_at: str,
    readings_block: str,
) -> str:
    name = display_device_name(device_name, device_type="sensor")
    return (
        f"**Não sei se o sensor **{name}** está conectado agora** (sem status de presença).\n"
        f"**Última leitura registrada** (em **{received_at}**): {readings_block}. "
        f"Esse valor **pode não** refletir o momento atual."
    )


def template_t4(*, device_name: str | None) -> str:
    name = display_device_name(device_name, device_type="sensor")
    return (
        f"**Não sei se o sensor **{name}** está conectado** e **não há leituras registradas** "
        f"ainda. Verifique energia e Wi‑Fi no dispositivo ou aguarde a primeira publicação."
    )


def template_t5(
    *,
    device_name: str | None,
    last_seen_at: str | None,
) -> str:
    name = display_device_name(device_name, device_type="sensor")
    suffix = _last_seen_suffix(last_seen_at)
    return (
        f"O sensor **{name}** está **offline**{suffix}. "
        f"**Não dá para acompanhar leituras em tempo real** agora.\n"
        f"Quer ver a **última leitura registrada**?"
    )


def template_t6(*, device_name: str | None) -> str:
    name = display_device_name(device_name, device_type="sensor")
    return (
        f"**Não sei se o sensor **{name}** está conectado** (sem status de presença). "
        f"**Não vou abrir o acompanhamento em tempo real** até haver confirmação de que "
        f"está online.\n"
        f"Posso mostrar a **última leitura registrada**, se existir."
    )


def template_intent_mixed(
    *,
    sensor_name: str | None,
    actuator_labels: list[str],
) -> str:
    sensor = display_device_name(sensor_name, device_type="sensor")
    actuators = ", ".join(f"**{label}**" for label in actuator_labels) if actuator_labels else "—"
    return (
        f"Você quer a **última leitura do sensor** **{sensor}** ou saber o **estado de um atuador** "
        f"(relé, etc.)?\n"
        f"• Sensor: **{sensor}**\n"
        f"• Atuadores: {actuators}"
    )


def template_clarify_sensors(options: list[str | None]) -> str:
    lines = ["Qual sensor você quer consultar?"]
    for i, name in enumerate(options, start=1):
        idx = i if not (name or "").strip() else None
        lines.append(
            f"• **{display_device_name(name, device_type='sensor', list_index=idx)}**"
        )
    return "\n".join(lines)


def template_clarify_devices(options: list[tuple[str | None, DeviceTypeLabel]]) -> str:
    lines = ["Qual dispositivo você quer?", ""]
    sensor_n = 0
    actuator_n = 0
    for name, dtype in options:
        if dtype == "sensor":
            sensor_n += 1
            idx = sensor_n if not (name or "").strip() else None
            label_pt = "sensor"
            shown = display_device_name(name, device_type="sensor", list_index=idx)
        else:
            actuator_n += 1
            idx = actuator_n if not (name or "").strip() else None
            label_pt = "atuador"
            shown = display_device_name(name, device_type="actuator", list_index=idx)
        lines.append(f"• **{shown}** ({label_pt})")
    return "\n".join(lines)


def template_actuator_instruct(*, device_name: str | None) -> str:
    name = display_device_name(device_name, device_type="actuator")
    return (
        f"O **{name}** é um **atuador** — não publica leituras de sensor como temperatura ou umidade. "
        f"Posso ajudar com o **estado reportado** ou com **comandos** (quando disponíveis). "
        f"O que você prefere?"
    )


def template_command_confirm(
    *,
    device_name: str | None,
    verb_pt: str,
    binary_value: int,
) -> str:
    name = display_device_name(device_name, device_type="actuator")
    return (
        f"Vou **{verb_pt}** o atuador **{name}** (comando digital **{binary_value}** — "
        f"**0** = desligado, **1** = ligado).\n"
        f"Responda **sim** para confirmar ou **não** para cancelar."
    )


def template_command_power_ask(*, device_name: str | None) -> str:
    name = display_device_name(device_name, device_type="actuator")
    return f"Quer **ligar (1)** ou **desligar (0)** o atuador **{name}**?"


def template_command_sent(
    *,
    device_name: str | None,
    verb_pt: str,
    binary_value: int,
) -> str:
    name = display_device_name(device_name, device_type="actuator")
    return f"Comando enviado: **{verb_pt}** **{name}** (valor **{binary_value}**)."


def template_command_cancelled() -> str:
    return "Comando cancelado. Nada foi enviado ao atuador."


def template_realtime_started(*, device_name: str | None) -> str:
    name = display_device_name(device_name, device_type="sensor")
    return f"Abrindo o acompanhamento **em tempo real** do sensor **{name}** no chat."


def template_post_adopt(*, device_name: str | None, device_type_pt: str) -> str:
    """T-POST-ADOPT — turno zero após adoção commitada."""
    dtype = device_type_pt.strip() or "dispositivo"
    if device_name and device_name.strip():
        return (
            f"Pronto! O dispositivo **{device_name.strip()}** ({dtype}) foi adicionado à sua conta. "
            f"**O que você quer fazer agora?**"
        )
    label = "seu sensor" if dtype == "sensor" else "seu atuador" if dtype == "atuador" else "seu dispositivo"
    return (
        f"Pronto! **{label.capitalize()}** ({dtype}) foi adicionado à sua conta. "
        f"**O que você quer fazer agora?**"
    )


def template_mac_not_in_chat() -> str:
    """Retrocompat — use ``template_network_not_in_chat``."""
    return template_network_not_in_chat()


def template_mqtt_topics_no_device() -> str:
    return (
        "Não encontrei dispositivos adotados na sua conta para informar tópicos MQTT. "
        "Adote um device pela interface e pergunte de novo, ou diga o **nome** do dispositivo."
    )


def template_mqtt_topics_type_missing(device_type: DeviceTypeLabel) -> str:
    kind = "atuador" if device_type == "actuator" else "sensor"
    other = "sensor" if device_type == "actuator" else "atuador"
    return (
        f"Não há **{kind}** adotado na sua conta para listar tópicos MQTT. "
        f"Peça pelo **nome** do {kind}, ou use *listar dispositivos* para ver o que você tem. "
        f"Se quiser tópicos do **{other}**, diga explicitamente *{other}* na pergunta."
    )


def template_mqtt_topics(
    *,
    device_name: str | None,
    device_type: DeviceTypeLabel | None,
    mqtt_topic_base: str | None,
    model: str | None = None,
    operation_status: str | None = None,
    readings_block: str | None = None,
) -> str:
    """Tópicos normativos tenants/.../devices/... — nunca inventar sensors/foo."""
    label = display_device_name(device_name, device_type=device_type)
    parts = [
        f"Tópicos MQTT do dispositivo **{label}** (contrato da plataforma):",
        "",
        "**Não** use caminhos genéricos como `sensors/nome`; aqui o prefixo é multi-tenant.",
    ]
    if mqtt_topic_base and mqtt_topic_base.strip():
        base = mqtt_topic_base.rstrip("/")
        suffix_lines = [
            "",
            f"- Comandos: `{base}/commands`",
            f"- Estado (ACK): `{base}/state`",
            f"- Presença: `{base}/status`",
        ]
        if device_type == "sensor":
            suffix_lines.insert(1, f"- Telemetria: `{base}/telemetry`")
        else:
            suffix_lines.insert(
                1,
                f"- Telemetria: `{base}/telemetry` _(atuadores em geral não publicam leituras)_",
            )
        parts.extend(suffix_lines)
    else:
        parts.append(
            "\nA base MQTT ainda não está no cadastro — verifique se a adoção foi concluída."
        )
    meta: list[str] = []
    if model and model.strip() and model != "unknown":
        meta.append(f"**Modelo:** {model.strip()}")
    if operation_status:
        meta.append(f"**Status:** {operation_status}")
    if meta:
        parts.extend(["", " · ".join(meta)])
    if readings_block:
        parts.extend(["", f"**Últimas leituras registradas:** {readings_block}"])
    return "\n".join(parts)


def template_network_not_in_chat() -> str:
    """MAC/IP não expostos via tools de chat (mcp-list-devices §4.1)."""
    return (
        "**Endereço MAC** e **IP local** do dispositivo **não** aparecem no chat "
        "(a listagem traz nome, tipo, modelo, status e telemetria — não identidade de rede).\n\n"
        "Para MAC: **etiqueta na placa**, QR de fábrica ou detalhes do device na interface.\n"
        "Para IP: **roteador**, app do fabricante ou serial/USB do embarcado — a TomatoIA não "
        "monitora IP Wi‑Fi no MVP.\n\n"
        "Posso ajudar com **última leitura**, **tempo real** (sensor online) ou **listar dispositivos**."
    )
