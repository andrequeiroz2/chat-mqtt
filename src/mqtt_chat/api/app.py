"""FastAPI: health check e lifespan do worker MQTT."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mqtt_chat.config.settings import get_settings
from mqtt_chat.logging import events, log_event
from mqtt_chat.logging.bootstrap import setup_logging_from_settings
from mqtt_chat.api.routes import adopt as adopt_routes
from mqtt_chat.api.routes import chat as chat_routes
from mqtt_chat.api.routes import me as me_routes
from mqtt_chat.server import build_mcp_server
from mqtt_chat.worker.monitor import WorkerHealth, run_with_reconnect

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicia worker MQTT na subida; cancela no shutdown."""
    settings = get_settings()
    setup_logging_from_settings(settings)
    stop_event = asyncio.Event()
    health = WorkerHealth()
    publish_queue: asyncio.Queue[tuple[str, bytes]] = asyncio.Queue(maxsize=32)

    app.state.worker_health = health
    app.state.publish_queue = publish_queue

    worker_task = asyncio.create_task(
        run_with_reconnect(settings, stop_event, health, publish_queue),
        name="mqtt-worker",
    )
    log_event(
        logger,
        logging.INFO,
        events.API_STARTED,
        "API started",
        persist_mode=settings.worker_persist_mode,
        mqtt_host=settings.mqtt_host,
        mqtt_port=settings.mqtt_port,
    )

    yield

    stop_event.set()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    log_event(logger, logging.INFO, events.API_SHUTDOWN, "API shutdown complete")


app = FastAPI(title="mqtt-chat", lifespan=lifespan)
# Dev: Vite no Docker expõe também IP da bridge (ex. 172.25.0.3:5173); sem isso
# o browser bloqueia /health e /me após login Firebase (Origin ≠ localhost).
_DEV_VITE_ORIGIN_REGEX = (
    r"http://("
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
    r"):5173"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_origin_regex=_DEV_VITE_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(me_routes.router)
app.include_router(chat_routes.router)
app.include_router(adopt_routes.router)

_mcp_settings = get_settings()
_mcp = build_mcp_server(_mcp_settings, auth_enabled=True)
_mcp_http = _mcp.http_app(path="/", transport="streamable-http")
app.mount("/api/v1/mcp", _mcp_http)


@app.get("/health")
async def health() -> dict:
    """Health check inclui estado da conexão MQTT do worker."""
    health_state: WorkerHealth = app.state.worker_health
    return {
        "status": "ok",
        "mqtt_connected": health_state.mqtt_connected,
        "mqtt_reconnect_count": health_state.reconnect_count,
        "mqtt_last_error": health_state.last_error,
    }


def run() -> None:
    """Entrypoint uvicorn (script mqtt-chat-api)."""
    import uvicorn

    settings = get_settings()
    setup_logging_from_settings(settings)
    uvicorn.run(
        "mqtt_chat.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
    )
