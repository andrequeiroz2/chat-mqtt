def main() -> None:
    """Atalho: inicia API com worker MQTT (uv run mqtt-chat)."""
    from mqtt_chat.api.app import run

    run()
