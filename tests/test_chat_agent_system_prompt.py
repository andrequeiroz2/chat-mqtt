"""Testes do system prompt do agente TomatoIA (task 018)."""

from __future__ import annotations

from mqtt_chat.agent.chat_agent import _build_system_prompt


def test_prompt_has_sections() -> None:
    prompt = _build_system_prompt("André", history_empty=False)
    assert "## Identidade" in prompt
    assert "## Escopo" in prompt
    assert "## Tools e quando usar" in prompt
    assert "## Proibições" in prompt
    assert "## Erros de tool (como responder)" in prompt
    assert "## Política conversacional" in prompt


def test_prompt_tool_error_guidance() -> None:
    prompt = _build_system_prompt("André", history_empty=False)
    assert "device_not_found" in prompt
    assert "device_ambiguous" in prompt
    assert "device_required" in prompt
    assert "telemetry_history_empty" in prompt
    assert "device_not_online_for_realtime" in prompt


def test_prompt_core_rules_preserved() -> None:
    prompt = _build_system_prompt("André", history_empty=False)
    assert "TomatoIA" in prompt
    assert "português" in prompt
    assert "scope=off_topic" in prompt
    assert "list_devices" in prompt
    assert "read_latest_telemetry" in prompt
    assert "start_realtime_telemetry" in prompt
    assert "get_telemetry_history" in prompt
    assert "Nunca invente números de telemetria" in prompt
    assert "tenants/{user_id}/devices/{device_id}" in prompt
    assert "device_id UUID" in prompt
    assert "chat-conversational-policy.md" in prompt


def test_prompt_greeting_only_when_history_empty() -> None:
    prompt_empty = _build_system_prompt("André", history_empty=True)
    assert "cumprimente pelo nome" in prompt_empty
    assert "André" in prompt_empty

    prompt_nonempty = _build_system_prompt("André", history_empty=False)
    assert "cumprimente pelo nome" not in prompt_nonempty
    assert "André" in prompt_nonempty
