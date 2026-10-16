"""Servidor FastMCP — registro de tools IoT."""

from __future__ import annotations

from fastmcp import FastMCP

from mqtt_chat.config.settings import Settings
from mqtt_chat.mcp.firebase_verifier import FirebaseTokenVerifier
from mqtt_chat.tools import list_devices as list_devices_tool
from mqtt_chat.tools import get_realtime_stream_info as get_realtime_stream_info_tool
from mqtt_chat.tools import publish_command as publish_command_tool
from mqtt_chat.tools import read_latest_telemetry as read_latest_telemetry_tool


def build_mcp_server(settings: Settings, *, auth_enabled: bool = True) -> FastMCP:
    """Instancia FastMCP com auth Firebase (HTTP) quando habilitado."""
    auth = FirebaseTokenVerifier(settings) if auth_enabled else None
    mcp = FastMCP(
        "mqtt-chat IoT",
        instructions=(
            "Tools IoT da plataforma TomatoIA. Escopo multi-tenant: "
            "cada chamada usa o usuário autenticado no Bearer token."
        ),
        auth=auth,
    )
    list_devices_tool.register(mcp)
    read_latest_telemetry_tool.register(mcp)
    publish_command_tool.register(mcp)
    get_realtime_stream_info_tool.register(mcp)
    return mcp
