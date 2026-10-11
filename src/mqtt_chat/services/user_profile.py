"""Perfil do usuário em Firestore (coleção users)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from mqtt_chat.logging import events, log_event
from mqtt_chat.schemas.user import UserProfileResponse, UserProfileUpdateRequest

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient

logger = logging.getLogger(__name__)

USERS_COLLECTION = "users"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _auth_providers_from_claims(decoded_token: dict[str, Any]) -> list[str]:
    firebase_claims = decoded_token.get("firebase") or {}
    identities = firebase_claims.get("identities") or {}
    if isinstance(identities, dict) and identities:
        return sorted(str(k) for k in identities)
    provider = firebase_claims.get("sign_in_provider")
    if provider:
        return [str(provider)]
    return []


def _default_display_name(decoded_token: dict[str, Any]) -> str:
    name = decoded_token.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    email = decoded_token.get("email")
    if isinstance(email, str) and "@" in email:
        return email.split("@", maxsplit=1)[0]
    return "User"


def _doc_to_response(data: dict[str, Any]) -> UserProfileResponse:
    return UserProfileResponse.model_validate(data)


def ensure_user_profile(
    db: FirestoreClient,
    decoded_token: dict[str, Any],
) -> UserProfileResponse:
    """
    Garante documento users/{user_id}; espelha campos OAuth somente leitura.

    display_name editável só via PATCH; photo_url/email atualizados a partir do token.
    """
    user_id = str(decoded_token["uid"])
    doc_ref = db.collection(USERS_COLLECTION).document(user_id)
    snapshot = doc_ref.get()
    now = _now_iso()

    email = decoded_token.get("email")
    email_str = str(email) if isinstance(email, str) else None
    photo = decoded_token.get("picture")
    photo_str = str(photo) if isinstance(photo, str) else None
    providers = _auth_providers_from_claims(decoded_token)

    if not snapshot.exists:
        payload = {
            "user_id": user_id,
            "email": email_str,
            "display_name": _default_display_name(decoded_token),
            "photo_url": photo_str,
            "auth_providers": providers,
            "created_at": now,
            "updated_at": now,
        }
        doc_ref.set(payload)
        log_event(
            logger,
            logging.INFO,
            events.USER_PROFILE_CREATED,
            "User profile created",
            user_id=user_id,
        )
        return _doc_to_response(payload)

    data = snapshot.to_dict() or {}
    updates: dict[str, Any] = {}
    if email_str is not None and data.get("email") != email_str:
        updates["email"] = email_str
    if photo_str is not None and data.get("photo_url") != photo_str:
        updates["photo_url"] = photo_str
    if providers and data.get("auth_providers") != providers:
        updates["auth_providers"] = providers
    if updates:
        updates["updated_at"] = now
        doc_ref.update(updates)
        data.update(updates)

    data.setdefault("user_id", user_id)
    data.setdefault("display_name", _default_display_name(decoded_token))
    data.setdefault("created_at", now)
    data.setdefault("updated_at", now)
    data.setdefault("auth_providers", providers)
    return _doc_to_response(data)


def update_user_display_name(
    db: FirestoreClient,
    user_id: str,
    body: UserProfileUpdateRequest,
) -> UserProfileResponse:
    """Atualiza somente display_name (RF-USER-02)."""
    doc_ref = db.collection(USERS_COLLECTION).document(user_id)
    snapshot = doc_ref.get()
    if not snapshot.exists:
        raise LookupError("user_profile_not_found")

    now = _now_iso()
    display_name = body.display_name.strip()
    doc_ref.update({"display_name": display_name, "updated_at": now})

    data = snapshot.to_dict() or {}
    data["display_name"] = display_name
    data["updated_at"] = now
    data.setdefault("user_id", user_id)
    log_event(
        logger,
        logging.INFO,
        events.USER_PROFILE_UPDATED,
        "User display_name updated",
        user_id=user_id,
    )
    return _doc_to_response(data)
