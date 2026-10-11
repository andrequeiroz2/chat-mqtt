"""Cliente Firebase Admin (Auth + Firestore)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials, firestore

from mqtt_chat.config.settings import Settings
from mqtt_chat.logging import events, log_event

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient

logger = logging.getLogger(__name__)

_db: FirestoreClient | None = None
_initialized = False


def ensure_firebase_app(settings: Settings) -> bool:
    """Inicializa Firebase Admin se FIREBASE_PROJECT_ID estiver definido."""
    global _initialized

    if not settings.firebase_project_id:
        return False

    if _initialized:
        return True

    cred: credentials.Base = credentials.ApplicationDefault()
    if settings.google_application_credentials:
        cred = credentials.Certificate(settings.google_application_credentials)
    firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
    _initialized = True
    log_event(
        logger,
        logging.INFO,
        events.FIREBASE_INITIALIZED,
        "Firebase Admin initialized",
        firebase_project_id=settings.firebase_project_id,
    )
    return True


def get_firestore_client(settings: Settings) -> FirestoreClient | None:
    """
    Cliente Firestore quando o projeto Firebase está configurado.

    Usado por perfil de usuário (auth) e, se habilitado, ingestão do worker.
    """
    global _db

    if not ensure_firebase_app(settings):
        return None

    if _db is None:
        _db = firestore.client()
    return _db


def get_firestore(settings: Settings) -> FirestoreClient | None:
    """
    Retorna Firestore somente em WORKER_PERSIST_MODE=firestore.

    Em dev sem Firebase, retorna None (persistência via log em services/).
    """
    if settings.worker_persist_mode != "firestore":
        return None

    if not settings.firebase_project_id:
        log_event(
            logger,
            logging.WARNING,
            events.FIREBASE_UNAVAILABLE,
            "Firestore mode but FIREBASE_PROJECT_ID unset",
        )
        return None

    return get_firestore_client(settings)


def verify_id_token(id_token: str, settings: Settings) -> dict[str, Any]:
    """Valida ID token JWT do Firebase Auth; exige Admin SDK inicializado."""
    if not ensure_firebase_app(settings):
        raise RuntimeError("firebase_not_configured")
    decoded = firebase_auth.verify_id_token(id_token, check_revoked=False)
    return dict(decoded)
