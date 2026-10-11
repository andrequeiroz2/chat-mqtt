"""Agente de chat IoT (Pydantic AI) — saudação e diálogo em português."""

from __future__ import annotations

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import infer_model
from pydantic_ai.providers import infer_provider
from pydantic_ai.providers.google import GoogleProvider

from mqtt_chat.agent.deps import UserDeps
from mqtt_chat.config.settings import Settings


def _build_system_prompt(display_name: str) -> str:
    return (
        "Você é o assistente mqtt-chat para IoT (sensores e atuadores MQTT). "
        "Responda sempre em português, de forma clara e concisa. "
        f"O usuário autenticado se chama {display_name!r}. "
        "Na primeira interação de uma conversa, cumprimente pelo nome "
        f"(ex.: Olá, {display_name}, no que posso ajudar?). "
        "Ferramentas IoT serão adicionadas em fases posteriores; por ora oriente sobre dispositivos e telemetria."
    )


def _history_to_model_messages(history: list[tuple[str, str]]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for role, content in history:
        if role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=content)]))
    return messages


def create_chat_agent(settings: Settings) -> Agent[UserDeps, str]:
    """Factory do agente conforme modelo configurado em env."""
    api_key = settings.google_api_key

    def provider_factory(provider_name: str):
        if provider_name == "google":
            if not api_key:
                raise ValueError("google_api_key_missing")
            return GoogleProvider(api_key=api_key)
        return infer_provider(provider_name)

    model = infer_model(settings.chat_model, provider_factory=provider_factory)
    agent: Agent[UserDeps, str] = Agent(
        model,
        name="mqtt_chat_assistant",
        deps_type=UserDeps,
    )

    @agent.instructions
    def system_prompt(ctx: RunContext[UserDeps]) -> str:
        return _build_system_prompt(ctx.deps.display_name)

    return agent


async def run_chat(
    agent: Agent[UserDeps, str],
    deps: UserDeps,
    user_message: str,
    history: list[tuple[str, str]],
) -> str:
    """Executa um turno e retorna texto do assistente."""
    message_history = _history_to_model_messages(history)
    result = await agent.run(
        user_message,
        deps=deps,
        message_history=message_history,
    )
    return str(result.output)
