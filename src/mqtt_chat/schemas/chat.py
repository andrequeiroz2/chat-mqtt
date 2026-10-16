"""Schemas HTTP e saída estruturada do chat."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

ChatScope = Literal["product", "off_topic"]
SuggestedUiKind = Literal["realtime_telemetry"]


class SuggestedUiAction(BaseModel):
    """Hint para o frontend montar widget (RF-009); não executa MQTT."""

    kind: SuggestedUiKind
    device_id: str = Field(min_length=1)
    device_name: str | None = None


class ChatRequest(BaseModel):
    """Corpo de POST /api/v1/chat."""

    message: str = Field(min_length=1, max_length=8000)
    session_id: str = Field(default="default", min_length=1, max_length=128)


class ChatTurnResult(BaseModel):
    """Saída estruturada do agente Pydantic AI (classificação + resposta in-scope)."""

    scope: ChatScope
    reply: str = Field(default="", max_length=8000)

    @model_validator(mode="after")
    def product_requires_reply(self) -> ChatTurnResult:
        if self.scope == "product" and not self.reply.strip():
            raise ValueError("reply_required_for_product_scope")
        return self


class ChatResponse(BaseModel):
    """Resposta JSON de POST /api/v1/chat."""

    reply: str
    session_id: str
    persisted: bool
    suggested_ui: SuggestedUiAction | None = None


class PostAdoptionRequest(BaseModel):
    """Corpo de POST /api/v1/chat/post-adoption (turno zero 011-j)."""

    session_id: str = Field(min_length=1, max_length=128)
    device_id: str = Field(min_length=1, max_length=128)


class PostAdoptionActionItem(BaseModel):
    """Ação sugerida pós-adoção (chip na UI)."""

    action_id: Literal["read_latest", "realtime", "list_devices", "actuator_help"]
    label: str = Field(min_length=1, max_length=80)
    prompt: str = Field(min_length=1, max_length=500)
    disabled: bool = False


class PostAdoptionResponse(BaseModel):
    """Turno zero: foco de sessão + mensagem + chips."""

    message: str
    session_id: str
    device_id: str
    device_name: str | None = None
    device_type: Literal["sensor", "actuator"]
    actions: list[PostAdoptionActionItem] = Field(default_factory=list)
