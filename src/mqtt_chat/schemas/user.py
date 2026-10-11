"""Schemas Pydantic para perfil do usuário (Firestore / API)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    """Perfil exposto em GET /api/v1/me."""

    user_id: str
    email: str | None = None
    display_name: str
    photo_url: str | None = None
    auth_providers: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class UserProfileUpdateRequest(BaseModel):
    """Corpo de PATCH /api/v1/me — somente display_name editável."""

    display_name: str = Field(min_length=1, max_length=128)
