"""Verificação Bearer Firebase ID token para MCP HTTP."""

from __future__ import annotations

import logging
import time

from firebase_admin import auth as firebase_auth

from fastmcp.server.auth import AccessToken, TokenVerifier

from mqtt_chat.clients.firebase import verify_id_token
from mqtt_chat.config.settings import Settings
from mqtt_chat.logging import events, log_event

logger = logging.getLogger(__name__)


class FirebaseTokenVerifier(TokenVerifier):
    """Valida JWT do Firebase Auth no endpoint MCP (mesma regra que FastAPI /chat)."""

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings

    async def verify_token(self, token: str) -> AccessToken | None:
        if not self._settings.firebase_project_id:
            log_event(
                logger,
                logging.WARNING,
                events.MCP_AUTH_REJECTED,
                "Firebase not configured for MCP auth",
            )
            return None

        try:
            decoded = verify_id_token(token, self._settings)
        except firebase_auth.InvalidIdTokenError:
            log_event(logger, logging.WARNING, events.MCP_AUTH_REJECTED, "Invalid ID token")
            return None
        except firebase_auth.ExpiredIdTokenError:
            log_event(logger, logging.WARNING, events.MCP_AUTH_REJECTED, "Expired ID token")
            return None
        except firebase_auth.RevokedIdTokenError:
            log_event(logger, logging.WARNING, events.MCP_AUTH_REJECTED, "Revoked ID token")
            return None
        except Exception:
            log_event(
                logger,
                logging.ERROR,
                events.MCP_AUTH_REJECTED,
                "Token verification failed",
                exc_info=True,
            )
            return None

        uid = decoded.get("uid")
        if not uid:
            return None

        exp = decoded.get("exp")
        expires_at = int(exp) if isinstance(exp, (int, float)) else int(time.time()) + 3600

        return AccessToken(
            token=token,
            client_id=str(uid),
            scopes=[],
            expires_at=expires_at,
            subject=str(uid),
            claims=dict(decoded),
        )
