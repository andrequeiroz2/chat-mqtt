"""Schemas HTTP e saída estruturada do chat."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

ChatScope = Literal["product", "off_topic"]


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
