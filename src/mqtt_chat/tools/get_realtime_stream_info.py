"""Tool MCP — metadados do WebSocket tempo real (para orientar UI/integração)."""

from __future__ import annotations

import logging

from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import CurrentAccessToken
from pydantic import BaseModel, Field

from mqtt_chat.config.settings import get_settings
from mqtt_chat.logging import events, log_event

logger = logging.getLogger(__name__)


class RealtimeStreamInfo(BaseModel):
    """Como o frontend (não o LLM) abre o stream ao vivo."""

    websocket_path: str = Field(
        default="/api/v1/realtime/ws",
        description="Path relativo à base da API; upgrade WebSocket.",
    )
    auth: str = Field(
        default="Firebase ID token na query ?token= (renovar no browser).",
    )
    optional_device_filter: str = Field(
        default="Query opcional device_id=<uuid> restringe eventos a um device.",
    )
    event_types: list[str] = Field(
        default_factory=lambda: ["connected", "telemetry", "device_status"],
    )
    note_for_agent: str = Field(
        default=(
            "O LLM não assina este WebSocket. Use read_latest_telemetry para valores "
            "sob demanda no chat; o WebSocket é para a UI acompanhar ao vivo."
        ),
    )


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def get_realtime_stream_info(
        token: AccessToken = CurrentAccessToken(),
    ) -> RealtimeStreamInfo:
        """Retorna como conectar ao WebSocket de telemetria/status em tempo real.

        Use quando o usuário pedir acompanhar leituras ao vivo, dashboard em tempo
        real ou integração frontend — não para ler valores no chat (use
        read_latest_telemetry).

        O browser deve abrir WebSocket na API com token Firebase na query string.
        """
        uid = token.claims.get("uid") or token.subject
        log_event(
            logger,
            logging.INFO,
            events.MCP_TOOL_CALL,
            "get_realtime_stream_info invoked",
            tool="get_realtime_stream_info",
            user_id=str(uid) if uid else None,
        )
        settings = get_settings()
        _ = settings  # reservado para URL absoluta futura
        return RealtimeStreamInfo()
