"""Tool MCP publish_command."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import CurrentAccessToken
from fastmcp.server.auth import AccessToken

from mqtt_chat.clients.firebase import get_firestore_client
from mqtt_chat.config.settings import get_settings
from mqtt_chat.logging import events, log_event
from mqtt_chat import runtime as app_runtime
from mqtt_chat.schemas.publish_command import PublishCommandInput, PublishCommandResult
from mqtt_chat.services.actuator_command_service import ActuatorCommandError, publish_actuator_command

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def register(mcp: FastMCP) -> None:
    """Registra publish_command no servidor MCP."""

    @mcp.tool()
    async def publish_command(
        device_id: str,
        value: int,
        channel: int = 1,
        token: AccessToken = CurrentAccessToken(),
    ) -> PublishCommandResult:
        """Publica comando binário (0/1) em atuador adotado.

        Use somente para `device_type == actuator`, após confirmação explícita do usuário
        (G10). Atualiza `last_command` / `last_command_at` no documento `devices`.

        Parâmetros:
        - device_id: UUID do atuador.
        - value: 0 (desligado) ou 1 (ligado).
        - channel: canal (default 1).

        Erros: device_not_found, not_actuator, mqtt_unavailable, invalid_arguments.
        """
        settings = get_settings()
        db = get_firestore_client(settings)
        if db is None:
            raise ToolError("firebase_not_configured")

        uid = token.claims.get("uid") or token.subject
        if not uid:
            raise ToolError("missing_authentication")

        if value not in (0, 1):
            raise ToolError("invalid_arguments")

        log_event(
            logger,
            logging.INFO,
            events.MCP_TOOL_CALL,
            "publish_command invoked",
            tool="publish_command",
            user_id=str(uid),
            device_id=device_id,
        )

        try:
            params = PublishCommandInput(device_id=device_id, value=value, channel=channel)  # type: ignore[arg-type]
        except Exception as exc:
            raise ToolError("invalid_arguments") from exc

        queue = app_runtime.publish_queue
        try:
            payload = await publish_actuator_command(
                db,
                str(uid),
                params.device_id,
                params.value,
                queue,
                channel=params.channel,
            )
        except ActuatorCommandError as exc:
            raise ToolError(exc.code) from exc

        return PublishCommandResult(
            device_id=params.device_id,
            payload=payload,
            last_command_at=_now_iso(),
        )
