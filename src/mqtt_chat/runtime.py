"""Referências de runtime compartilhadas (processo API + MCP montado no mesmo app)."""

from __future__ import annotations

import asyncio

publish_queue: asyncio.Queue[tuple[str, bytes]] | None = None
