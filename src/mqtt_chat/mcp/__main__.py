"""Entrypoint stdio FastMCP (dev local — preferir HTTP autenticado em /api/v1/mcp)."""

from __future__ import annotations

from mqtt_chat.config.settings import get_settings
from mqtt_chat.logging.bootstrap import setup_logging_from_settings
from mqtt_chat.server import build_mcp_server


def main() -> None:
    settings = get_settings()
    setup_logging_from_settings(settings)
    mcp = build_mcp_server(settings, auth_enabled=False)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
