"""Tool MCP read_latest_telemetry."""

from __future__ import annotations

import logging
from typing import Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import CurrentAccessToken

from mqtt_chat.clients.firebase import get_firestore_client
from mqtt_chat.config.settings import get_settings
from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.telemetry_tools import ReadLatestTelemetryInput, ReadLatestTelemetryResult
from mqtt_chat.services import telemetry_queries as telemetry_queries_service

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Registra read_latest_telemetry no servidor MCP."""

    @mcp.tool()
    def read_latest_telemetry(
        device_id: str | None = None,
        device_name: str | None = None,
        device_name_match: Literal["contains", "exact"] = "contains",
        token: AccessToken = CurrentAccessToken(),
    ) -> ReadLatestTelemetryResult:
        """Lê a telemetria mais recente de um dispositivo adotado.

        Use quando o usuário perguntar última leitura, temperatura, umidade,
        valores atuais do sensor ou telemetria ao vivo (dados já ingeridos pelo backend).

        Parâmetros opcionais:
        - device_id: UUID do device.
        - device_name: nome amigável (contains ou exact).
        - Se omitir ambos e o usuário tiver um único device, usa esse automaticamente.

        Não invente valores numéricos — se has_telemetry for false, diga que ainda
        não há leituras persistidas ou o device não enviou dados.

        Retorno: readings (métrica, valor, unidade), device_ts e received_at.
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
            "read_latest_telemetry invoked",
            tool="read_latest_telemetry",
            user_id=str(uid),
        )

        params = ReadLatestTelemetryInput(
            device_id=device_id,
            device_name=device_name,
            device_name_match=device_name_match,
        )
        try:
            return telemetry_queries_service.read_latest_telemetry(db, str(uid), params)
        except telemetry_queries_service.ReadLatestTelemetryError as exc:
            raise ToolError(exc.code) from exc
