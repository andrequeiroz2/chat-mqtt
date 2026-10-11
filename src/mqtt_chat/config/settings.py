"""Settings carregadas de variáveis de ambiente."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração global do backend PoC."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mqtt_host: str = Field(default="127.0.0.1", validation_alias="MQTT_HOST")
    mqtt_port: int = Field(default=1883, validation_alias="MQTT_PORT")
    mqtt_username: str | None = Field(default=None, validation_alias="MQTT_USERNAME")
    mqtt_password: str | None = Field(default=None, validation_alias="MQTT_PASSWORD")
    mqtt_client_id: str = Field(default="mqtt-chat-worker", validation_alias="MQTT_CLIENT_ID")
    mqtt_keepalive: int = Field(default=60, validation_alias="MQTT_KEEPALIVE")
    mqtt_connect_timeout: int = Field(default=30, validation_alias="MQTT_CONNECT_TIMEOUT")
    mqtt_backoff_initial: int = Field(default=1, validation_alias="MQTT_BACKOFF_INITIAL_SEC")
    mqtt_backoff_max: int = Field(default=30, validation_alias="MQTT_BACKOFF_MAX_SEC")

    firebase_project_id: str | None = Field(default=None, validation_alias="FIREBASE_PROJECT_ID")
    google_application_credentials: str | None = Field(
        default=None,
        validation_alias="GOOGLE_APPLICATION_CREDENTIALS",
    )
    worker_persist_mode: Literal["log", "firestore"] = Field(
        default="log",
        validation_alias="WORKER_PERSIST_MODE",
    )

    api_host: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")

    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_format: Literal["json", "text"] = Field(default="json", validation_alias="LOG_FORMAT")
    log_service_name: str = Field(default="mqtt-chat", validation_alias="LOG_SERVICE_NAME")


@lru_cache
def get_settings() -> Settings:
    """Retorna settings singleton (cache por processo)."""
    return Settings()
