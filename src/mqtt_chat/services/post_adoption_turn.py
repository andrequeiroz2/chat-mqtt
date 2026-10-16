"""Turno zero pós-adoção (G8/G9 — task 011-j)."""

from __future__ import annotations

from typing import Literal

from google.cloud.firestore_v1 import Client as FirestoreClient
from pydantic import BaseModel, Field

from mqtt_chat.config.settings import Settings, get_settings
from mqtt_chat.services.conversation_context import set_focus_after_adoption
from mqtt_chat.services.conversation_templates import template_post_adopt

DeviceType = Literal["sensor", "actuator"]
ActionId = Literal["read_latest", "realtime", "list_devices", "actuator_help"]


class PostAdoptionAction(BaseModel):
    """Chip de ação sugerida (frontend envia ``prompt`` como mensagem de chat)."""

    action_id: ActionId
    label: str = Field(min_length=1, max_length=80)
    prompt: str = Field(min_length=1, max_length=500)
    disabled: bool = False


class PostAdoptionTurnResult(BaseModel):
    """Resposta do turno zero após commit de adoção."""

    message: str
    device_id: str
    device_name: str | None = None
    device_type: DeviceType
    actions: list[PostAdoptionAction] = Field(default_factory=list)


class PostAdoptionError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _device_type_pt(device_type: DeviceType) -> str:
    return "sensor" if device_type == "sensor" else "atuador"


def _build_actions(
    device_type: DeviceType,
    *,
    operation_status: str | None,
) -> list[PostAdoptionAction]:
    common = [
        PostAdoptionAction(
            action_id="list_devices",
            label="Listar dispositivos",
            prompt="Liste meus dispositivos",
        ),
    ]
    if device_type == "sensor":
        realtime_disabled = operation_status != "online"
        return [
            PostAdoptionAction(
                action_id="read_latest",
                label="Última leitura",
                prompt="Mostre a última leitura",
            ),
            PostAdoptionAction(
                action_id="realtime",
                label="Acompanhar ao vivo",
                prompt="Quero acompanhar em tempo real",
                disabled=realtime_disabled,
            ),
            *common,
        ]
    return [
        PostAdoptionAction(
            action_id="actuator_help",
            label="Ligar ou desligar",
            prompt="Quero ligar ou desligar este atuador",
        ),
        *common,
    ]


def register_post_adoption_turn(
    db: FirestoreClient,
    user_id: str,
    session_id: str,
    device_id: str,
    *,
    settings: Settings | None = None,
) -> PostAdoptionTurnResult:
    """
    Define foco de sessão e monta turno zero (RF-CHAT-CTX-04 / G8–G9).

    Raises:
        PostAdoptionError: device_not_found, not_adopted.
    """
    cfg = settings or get_settings()
    snap = db.collection("devices").document(device_id).get()
    if not snap.exists:
        raise PostAdoptionError("device_not_found")
    data = snap.to_dict() or {}
    if data.get("user_id") != user_id:
        raise PostAdoptionError("device_not_found")
    device_type = data.get("device_type")
    if device_type not in ("sensor", "actuator"):
        raise PostAdoptionError("not_adopted")

    device_name = data.get("device_name")
    set_focus_after_adoption(
        db,
        user_id,
        session_id,
        device_id,
        cap=cfg.chat_device_snapshot_cap,
    )

    message = template_post_adopt(
        device_name=device_name,
        device_type_pt=_device_type_pt(device_type),  # type: ignore[arg-type]
    )
    return PostAdoptionTurnResult(
        message=message,
        device_id=device_id,
        device_name=device_name,
        device_type=device_type,  # type: ignore[arg-type]
        actions=_build_actions(
            device_type,  # type: ignore[arg-type]
            operation_status=data.get("operation_status")
            if isinstance(data.get("operation_status"), str)
            else None,
        ),
    )
