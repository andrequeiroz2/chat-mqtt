"""Tools Pydantic AI (mesmo contrato que MCP list_devices → services/)."""

from __future__ import annotations

import logging
from typing import Literal

from pydantic_ai import Agent, RunContext

from mqtt_chat.agent.deps import UserDeps
from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.chat import ChatTurnResult
from mqtt_chat.schemas.devices import ListDevicesInput, ListDevicesResult
from mqtt_chat.services import devices as devices_service

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
