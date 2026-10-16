"""Tools Pydantic AI (mesmo contrato que MCP list_devices → services/)."""

from __future__ import annotations

import logging
from typing import Literal

from pydantic_ai import Agent, RunContext

from mqtt_chat.agent.deps import UserDeps
from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.chat import ChatTurnResult, SuggestedUiAction
from mqtt_chat.schemas.devices import ListDevicesInput, ListDevicesResult
from mqtt_chat.schemas.telemetry_tools import (
    ReadLatestTelemetryInput,
    ReadLatestTelemetryResult,
    StartRealtimeTelemetryResult,
)
from mqtt_chat.services import devices as devices_service
from mqtt_chat.services import telemetry_queries as telemetry_queries_service

logger = logging.getLogger(__name__)


def register_device_tools(agent: Agent[UserDeps, ChatTurnResult]) -> None:
    """Registra tools IoT no agente TomatoIA."""

    @agent.tool
    def list_devices(
        ctx: RunContext[UserDeps],
        device_type: Literal["sensor", "actuator"] | None = None,
        device_name: str | None = None,
        device_name_match: Literal["contains", "exact"] = "contains",
        device_id: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> ListDevicesResult:
        """Lista dispositivos já adotados na conta do usuário autenticado.

        Use quando o usuário pedir para ver, listar, contar ou encontrar devices,
        sensores ou atuadores por nome.

        Parâmetros opcionais:
        - device_type: "sensor" ou "actuator" para filtrar.
        - device_name: nome amigável; device_name_match "contains" (padrão) ou "exact".
        - device_id: UUID específico (no máximo um, se pertencer ao usuário).
        - limit / cursor: paginação (padrão limit=50).

        Não adota nem registra devices. Para adicionar um device, oriente o usuário
        ao fluxo de adoção na interface (QR / pareamento).

        Retorno: lista resumida; lista vazia = nenhum device corresponde aos filtros.
        """
        log_event(
            logger,
            logging.INFO,
            events.MCP_TOOL_CALL,
            "list_devices invoked (chat agent)",
            tool="list_devices",
            user_id=ctx.deps.user_id,
        )
        params = ListDevicesInput(
            device_type=device_type,
            device_name=device_name,
            device_name_match=device_name_match,
            device_id=device_id,
            limit=limit,
            cursor=cursor,
        )
        try:
            return devices_service.list_devices(ctx.deps.db, ctx.deps.user_id, params)
        except devices_service.ListDevicesError as exc:
            raise ValueError(exc.code) from exc

    @agent.tool
    def read_latest_telemetry(
        ctx: RunContext[UserDeps],
        device_id: str | None = None,
        device_name: str | None = None,
        device_name_match: Literal["contains", "exact"] = "contains",
    ) -> ReadLatestTelemetryResult:
        """Lê a telemetria mais recente de um dispositivo adotado.

        Use quando o usuário perguntar última leitura, temperatura, umidade,
        valores atuais do sensor ou telemetria ao vivo.

        Parâmetros opcionais: device_id, device_name (+ device_name_match).
        Com um único device na conta, pode omitir ambos.

        Não invente números; use readings do retorno ou explique has_telemetry=false.
        """
        log_event(
            logger,
            logging.INFO,
            events.MCP_TOOL_CALL,
            "read_latest_telemetry invoked (chat agent)",
            tool="read_latest_telemetry",
            user_id=ctx.deps.user_id,
        )
        params = ReadLatestTelemetryInput(
            device_id=device_id,
            device_name=device_name,
            device_name_match=device_name_match,
        )
        try:
            return telemetry_queries_service.read_latest_telemetry(
                ctx.deps.db,
                ctx.deps.user_id,
                params,
            )
        except telemetry_queries_service.ReadLatestTelemetryError as exc:
            raise ValueError(exc.code) from exc

    @agent.tool
    def start_realtime_telemetry(
        ctx: RunContext[UserDeps],
        device_id: str | None = None,
        device_name: str | None = None,
        device_name_match: Literal["contains", "exact"] = "contains",
    ) -> StartRealtimeTelemetryResult:
        """Inicia painel ao vivo de telemetria no chat (WebSocket no browser).

        Use quando o usuário pedir valores em tempo real, stream contínuo, monitorar
        ao vivo, acompanhar leituras enquanto conversa — não para uma única leitura
        pontual (nesse caso use read_latest_telemetry).

        Parâmetros opcionais: device_id, device_name (+ device_name_match).
        Com um único device na conta, pode omitir ambos.

        Após chamar, confirme na reply que o painel ao vivo foi aberto no chat.
        """
        log_event(
            logger,
            logging.INFO,
            events.MCP_TOOL_CALL,
            "start_realtime_telemetry invoked (chat agent)",
            tool="start_realtime_telemetry",
            user_id=ctx.deps.user_id,
        )
        params = ReadLatestTelemetryInput(
            device_id=device_id,
            device_name=device_name,
            device_name_match=device_name_match,
        )
        try:
            resolved_id, resolved_name = telemetry_queries_service.resolve_device_for_telemetry(
                ctx.deps.db,
                ctx.deps.user_id,
                params,
            )
        except telemetry_queries_service.ReadLatestTelemetryError as exc:
            raise ValueError(exc.code) from exc

        snap = ctx.deps.db.collection("devices").document(resolved_id).get()
        data = snap.to_dict() if snap.exists else {}
        status = data.get("operation_status")
        if status != "online":
            raise ValueError("device_not_online_for_realtime")

        ctx.deps.suggested_ui = SuggestedUiAction(
            kind="realtime_telemetry",
            device_id=resolved_id,
            device_name=resolved_name,
        )
        return StartRealtimeTelemetryResult(
            device_id=resolved_id,
            device_name=resolved_name,
        )
