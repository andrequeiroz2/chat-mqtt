"""Configuração CHAT_MODEL / chaves de provedor."""

from mqtt_chat.config.settings import Settings


def test_chat_model_configured_google_requires_google_key() -> None:
    s = Settings(
        chat_model="google:gemini-3.5-flash",
        google_api_key=None,
        openai_api_key="sk-test",
    )
    assert s.chat_model_configured() is False


def test_chat_model_configured_openai_requires_openai_key() -> None:
    s = Settings(
        chat_model="openai:gpt-4o-mini",
        google_api_key="g-test",
        openai_api_key=None,
    )
    assert s.chat_model_configured() is False


def test_chat_model_configured_openai_ok() -> None:
    s = Settings(
        chat_model="openai:gpt-4o-mini",
        openai_api_key="sk-test",
    )
    assert s.chat_model_configured() is True
