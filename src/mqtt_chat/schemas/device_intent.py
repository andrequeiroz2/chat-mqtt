"""Saída do resolver determinístico de intenção/device."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from mqtt_chat.schemas.conversation_context import ClarifyOption, Connectivity

ChatIntent = Literal[
    "read_telemetry",
    "telemetry_history",
    "realtime",
    "actuator_command",
    "list_devices",
    "device_metadata",
]
ResolverOutcomeKind = Literal["pass_through", "execute", "clarify", "instruct"]


class DeviceIntentResolverResult(BaseModel):
    """Resultado do resolver (contrato chat-session-context §7)."""

    outcome: ResolverOutcomeKind
    intent: ChatIntent | None = None
    trigger_id: str | None = None
    template_id: str | None = None
    device_id: str | None = None
    device_name: str | None = None
    device_type: Literal["sensor", "actuator"] | None = None
    connectivity: Connectivity | None = None
    clarify_options: list[ClarifyOption] = Field(default_factory=list)
    instruct_kind: (
        Literal["actuator_no_telemetry", "actuator_vs_sensor", "actuator_power_unknown"]
        | None
    ) = None
    binary_value: Literal[0, 1] | None = None
    verb_pt: str | None = None

    @property
    def short_circuit(self) -> bool:
        """True quando o turno não deve depender do LLM para decidir device/copy."""
        if self.outcome in ("clarify", "instruct"):
            return True
        if self.outcome == "execute" and self.intent in (
            "read_telemetry",
            "telemetry_history",
            "realtime",
            "actuator_command",
            "list_devices",
            "device_metadata",
        ):
            return True
        return False
