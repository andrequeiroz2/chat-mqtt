"""Tool MCP list_devices."""

from __future__ import annotations

import logging
from typing import Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import CurrentAccessToken
from fastmcp.server.auth import AccessToken

from mqtt_chat.clients.firebase import get_firestore_client
from mqtt_chat.config.settings import get_settings
from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.devices import ListDevicesInput, ListDevicesResult
from mqtt_chat.services import devices as devices_service

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Registra list_devices no servidor MCP."""

    @mcp.tool()
    def list_devices(
        device_type: Literal["sensor", "actuator"] | None = None,
        device_name: str | None = None,
        device_name_match: Literal["contains", "exact"] = "contains",
        device_id: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
        token: AccessToken = CurrentAccessToken(),
    ) -> ListDevicesResult:
        """Lista dispositivos já adotados na conta do usuário autenticado.

        Use quando o usuário pedir para ver, listar, contar ou encontrar devices,
        sensores ou atuadores por nome.

        Parâmetros opcionais:
        - device_type: "sensor" ou "actuator" para filtrar.
        - device_name: nome amigável; use device_name_match "contains" (padrão) ou "exact".
        - device_id: UUID específico (retorna no máximo um, se pertencer ao usuário).
        - limit / cursor: paginação (padrão limit=50).

        Não adota nem registra devices. Para adicionar um device, oriente o usuário
        ao fluxo de adoção na interface (QR / pareamento), não invente devices.

        Retorno: lista resumida (id, nome, tipo, modelo, online/offline, last_seen).
        Lista vazia significa nenhum device corresponde aos filtros.
        """
        settings = get_settings()
        db = get_firestore_client(settings)
        if db is None:
            raise ToolError("firebase_not_configured")

        uid = token.claims.get("uid") or token.subject
        if not uid:
            raise ToolError("missing_authentication")

        log_event(
            logger,
            logging.INFO,
            events.MCP_TOOL_CALL,
            "list_devices invoked",
            tool="list_devices",
            user_id=str(uid),
        )

        try:
            params = ListDevicesInput(
                device_type=device_type,
                device_name=device_name,
                device_name_match=device_name_match,
                device_id=device_id,
                limit=limit,
                cursor=cursor,
            )
        except Exception as exc:
            raise ToolError("invalid_arguments") from exc

        try:
            return devices_service.list_devices(db, str(uid), params)
        except devices_service.ListDevicesError as exc:
            raise ToolError(exc.code) from exc
