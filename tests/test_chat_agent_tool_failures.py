"""Erros de domínio das tools do agente viram falha visível ao modelo (task 020).

Antes da 020: ``raise ValueError`` propagava para fora de ``agent.run`` → HTTP 500.
Depois: ``ToolFailed`` registra a falha como resultado de tool e o run completa,
permitindo ao modelo responder conforme a seção "Erros de tool" do system prompt.
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
from mqtt_chat.schemas.chat import ChatTurnResult
from mqtt_chat.services import devices as devices_service
from mqtt_chat.services import telemetry_queries as telemetry_queries_service

_TOOL_UNDER_TEST = "get_telemetry_history"


def _raising_model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    """1ª chamada: invoca a tool sob teste; 2ª (após falha): emite output final."""
    has_tool_return = any(
        isinstance(part, ToolReturnPart)
        for message in messages
        for part in getattr(message, "parts", [])
    )
    if has_tool_return:
        output_tool = info.output_tools[0].name
        return ModelResponse(
            parts=[
                ToolCallPart(
                    output_tool,
                    args={"scope": "product", "reply": "Não há leituras no período."},
                )
            ]
        )
    return ModelResponse(parts=[ToolCallPart(_TOOL_UNDER_TEST, args={"days": 7})])


def _make_agent() -> Agent[UserDeps, ChatTurnResult]:
    """Agente mínimo com as tools reais e modelo determinístico de teste."""
    agent: Agent[UserDeps, ChatTurnResult] = Agent(
        FunctionModel(_raising_model),
        name="test_tool_failures",
        deps_type=UserDeps,
        output_type=ChatTurnResult,
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


def _raise_telemetry_error(*args: Any, **kwargs: Any) -> Any:
    raise telemetry_queries_service.ReadLatestTelemetryError("telemetry_history_empty")


@pytest.fixture
def telemetry_failing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Força erro de domínio no serviço usado pela tool sob teste."""
    monkeypatch.setattr(
        telemetry_queries_service, "get_telemetry_history", _raise_telemetry_error
    )


def test_tool_domain_error_does_not_abort_run(telemetry_failing: None) -> None:
    """Erro de domínio na tool: o run deve completar com output (não propagar)."""
    agent = _make_agent()
    result = agent.run_sync("gráfico da última semana", deps=_deps())
    assert isinstance(result.output, ChatTurnResult)
    assert result.output.scope == "product"


def test_tool_failure_recorded_as_failed_tool_return(telemetry_failing: None) -> None:
    """A falha fica registrada no histórico como ToolReturnPart com outcome='failed'."""
    agent = _make_agent()
    result = agent.run_sync("gráfico da última semana", deps=_deps())

    failed_returns = [
        part
        for message in result.all_messages()
        for part in getattr(message, "parts", [])
        if isinstance(part, ToolReturnPart)
        and part.tool_name == _TOOL_UNDER_TEST
        and part.outcome == "failed"
    ]
    assert failed_returns, "esperava ToolReturnPart com outcome='failed'"


def test_list_devices_error_also_does_not_abort(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mesmo comportamento para erros de list_devices (ex.: invalid_device_name)."""

    def _raise(*args: Any, **kwargs: Any) -> Any:
        raise devices_service.ListDevicesError("invalid_device_name")

    monkeypatch.setattr(devices_service, "list_devices", _raise)

    def _call_list_devices(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        has_tool_return = any(
            isinstance(part, ToolReturnPart)
            for message in messages
            for part in getattr(message, "parts", [])
        )
        if has_tool_return:
            output_tool = info.output_tools[0].name
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        output_tool,
                        args={"scope": "product", "reply": "Não encontrei o dispositivo."},
                    )
                ]
            )
        return ModelResponse(parts=[ToolCallPart("list_devices", args={})])

    agent: Agent[UserDeps, ChatTurnResult] = Agent(
        FunctionModel(_call_list_devices),
        name="test_list_devices_failure",
        deps_type=UserDeps,
        output_type=ChatTurnResult,
    )
    register_device_tools(agent)

    result = agent.run_sync("liste meus sensores", deps=_deps())
    assert isinstance(result.output, ChatTurnResult)
