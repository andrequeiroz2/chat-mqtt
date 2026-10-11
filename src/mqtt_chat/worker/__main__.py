"""Executa somente o worker MQTT (sem HTTP)."""

import asyncio
import signal

from mqtt_chat.config.settings import get_settings
from mqtt_chat.logging.bootstrap import setup_logging_from_settings
from mqtt_chat.worker.monitor import run_with_reconnect


async def _async_main() -> None:
    settings = get_settings()
    setup_logging_from_settings(settings)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    await run_with_reconnect(settings, stop)


def main() -> None:
    """CLI: uv run python -m mqtt_chat.worker"""
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
