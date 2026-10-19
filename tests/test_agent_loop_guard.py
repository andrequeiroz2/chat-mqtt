"""Loop guard do agente (task 021-02): repetição de tool call idêntica → ToolFailed.

Cobre o incidente de 2026-10-19: modelo em loop chamando a mesma tool até
``UsageLimitExceeded`` (503). Com o guard, a 2ª call idêntica falha antes de
executar e o modelo finaliza com os dados que já tem.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from mqtt_chat.agent.deps import UserDeps
from mqtt_chat.agent.device_tools import register_device_tools
from mqtt_chat.agent.loop_guard import TOOL_LOOP_CODE, build_loop_guard
from mqtt_chat.schemas.chat import ChatTurnResult
from mqtt_chat.schemas.telemetry_tools import ReadLatestTelemetryResult
from mqtt_chat.services import telemetry_queries as telemetry_queries_service

_LOOP_TOOL = "read_latest_telemetry"


def _fake_read_latest(*args: Any, **kwargs: Any) -> ReadLatestTelemetryResult:
    return ReadLatestTelemetryResult(
        device_id="d1",
        device_name="Meu sensor",
        device_type="sensor",
        has_telemetry=False,
    )


def _looping_model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    """Modelo teimoso: repete a mesma tool call até receber falha; então finaliza."""
    has_failure = any(
        isinstance(part, ToolReturnPart) and part.outcome == "failed"
        for message in messages
        for part in getattr(message, "parts", [])
    )
    if has_failure:
        output_tool = info.output_tools[0].name
        return ModelResponse(
            parts=[
                ToolCallPart(
                    output_tool,
                    args={"scope": "product", "reply": "Você tem 1 sensor: Meu sensor."},
                )
            ]
        )
    return ModelResponse(
        parts=[ToolCallPart(_LOOP_TOOL, args={"device_name": "Meu sensor"})]
    )


def _make_looping_agent() -> Agent[UserDeps, ChatTurnResult]:
    agent: Agent[UserDeps, ChatTurnResult] = Agent(
        FunctionModel(_looping_model),
        name="test_loop_guard",
        deps_type=UserDeps,
        output_type=ChatTurnResult,
        capabilities=[build_loop_guard()],
    )
    register_device_tools(agent)
    return agent


def _deps() -> UserDeps:
    return UserDeps(
        user_id="user-test",
        display_name="André",
        session_id="session-test",
        db=MagicMock(),
    )


def test_loop_guard_stops_identical_tool_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"n": 0}

    def _counting_fake(*args: Any, **kwargs: Any) -> ReadLatestTelemetryResult:
        calls["n"] += 1
        return _fake_read_latest()

    monkeypatch.setattr(
        telemetry_queries_service, "read_latest_telemetry", _counting_fake
    )

    agent = _make_looping_agent()
    result = agent.run_sync("tenho algum sensor?", deps=_deps())

    # Run finaliza (não propaga) e o serviço executou UMA vez (guard barrou a 2ª).
    assert isinstance(result.output, ChatTurnResult)
    assert calls["n"] == 1

    failed = [
        part
        for message in result.all_messages()
        for part in getattr(message, "parts", [])
        if isinstance(part, ToolReturnPart)
        and part.tool_name == _LOOP_TOOL
        and part.outcome == "failed"
    ]
    assert failed, "esperava ToolReturnPart failed do loop guard"
    assert TOOL_LOOP_CODE in str(failed[0].content)


def test_loop_guard_ignores_output_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    """Output tool (final_result) nunca é bloqueada pelo guard."""
    monkeypatch.setattr(
        telemetry_queries_service, "read_latest_telemetry", _fake_read_latest
    )
    agent = _make_looping_agent()
    result = agent.run_sync("teste", deps=_deps())
    assert result.output.scope == "product"
