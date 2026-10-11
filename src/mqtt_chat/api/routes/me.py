"""Perfil do usuário autenticado."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud.firestore_v1 import Client as FirestoreClient

from mqtt_chat.api.deps import AuthenticatedUser, get_current_user, require_firestore
from mqtt_chat.schemas.user import UserProfileResponse, UserProfileUpdateRequest
from mqtt_chat.services.user_profile import ensure_user_profile, update_user_display_name

router = APIRouter(prefix="/api/v1", tags=["user"])


@router.get("/me", response_model=UserProfileResponse)
async def get_me(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[FirestoreClient, Depends(require_firestore)],
) -> UserProfileResponse:
    """Retorna perfil; cria documento Firestore no primeiro acesso."""
    return ensure_user_profile(db, user.decoded_token)


@router.patch("/me", response_model=UserProfileResponse)
async def patch_me(
    body: UserProfileUpdateRequest,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[FirestoreClient, Depends(require_firestore)],
) -> UserProfileResponse:
    """Atualiza somente display_name."""
    ensure_user_profile(db, user.decoded_token)
    try:
        return update_user_display_name(db, user.user_id, body)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user_profile_not_found",
        ) from exc
