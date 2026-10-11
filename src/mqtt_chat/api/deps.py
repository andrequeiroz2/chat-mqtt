"""Dependências FastAPI (settings, auth, Firestore)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

from google.cloud.firestore_v1 import Client as FirestoreClient

from mqtt_chat.clients.firebase import get_firestore_client, verify_id_token
from mqtt_chat.config.settings import Settings, get_settings
from mqtt_chat.logging import events, log_event

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Claims mínimos após validação do ID token Firebase."""

    user_id: str
    decoded_token: dict[str, Any]


def require_firestore(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FirestoreClient:
    """Cliente Firestore ou 503 se Firebase não configurado (rotas de perfil)."""
    db = get_firestore_client(settings)
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="firebase_not_configured",
        )
    return db


def get_current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthenticatedUser:
    """Valida Bearer ID token; rejeita requests anônimos."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        log_event(
            logger,
            logging.WARNING,
            events.AUTH_TOKEN_REJECTED,
            "Missing bearer token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing_authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if get_firestore_client(settings) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="firebase_not_configured",
        )

    try:
        decoded = verify_id_token(credentials.credentials, settings)
    except firebase_auth.InvalidIdTokenError:
        log_event(
            logger,
            logging.WARNING,
            events.AUTH_TOKEN_REJECTED,
            "Invalid ID token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except firebase_auth.ExpiredIdTokenError:
        log_event(
            logger,
            logging.WARNING,
            events.AUTH_TOKEN_REJECTED,
            "Expired ID token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="expired_token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except firebase_auth.RevokedIdTokenError:
        log_event(
            logger,
            logging.WARNING,
            events.AUTH_TOKEN_REJECTED,
            "Revoked ID token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="revoked_token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except Exception:
        log_event(
            logger,
            logging.ERROR,
            events.AUTH_TOKEN_REJECTED,
            "Token verification failed",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    uid = decoded.get("uid")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(user_id=str(uid), decoded_token=dict(decoded))
