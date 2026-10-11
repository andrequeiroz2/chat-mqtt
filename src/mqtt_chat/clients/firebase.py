"""Cliente Firebase Admin / Firestore (singleton)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import firebase_admin
from firebase_admin import credentials, firestore

from mqtt_chat.config.settings import Settings
from mqtt_chat.logging import events, log_event

if TYPE_CHECKING:
    from google.cloud.firestore_v1 import Client as FirestoreClient

logger = logging.getLogger(__name__)

_db: FirestoreClient | None = None
_initialized = False


def get_firestore(settings: Settings) -> FirestoreClient | None:
    """
    Retorna cliente Firestore se credenciais/projeto configurados.

    Em dev sem Firebase, retorna None (persistência via log em services/).
    """
    global _db, _initialized

    if settings.worker_persist_mode != "firestore":
        return None

    if _db is not None:
        return _db

    if not settings.firebase_project_id:
        log_event(
            logger,
            logging.WARNING,
            events.FIREBASE_UNAVAILABLE,
            "Firestore mode but FIREBASE_PROJECT_ID unset",
        )
        return None

    if not _initialized:
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

    _db = firestore.client()
    return _db
