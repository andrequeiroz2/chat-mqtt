"""Agente TomatoIA (Pydantic AI) — escopo produto IoT e saída estruturada."""

from __future__ import annotations

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import infer_model
from pydantic_ai.providers import infer_provider
from pydantic_ai.providers.google import GoogleProvider

from mqtt_chat.agent.deps import UserDeps
from mqtt_chat.agent.tomato_ia import ASSISTANT_NAME
from mqtt_chat.config.settings import Settings
from mqtt_chat.schemas.chat import ChatTurnResult


def _build_system_prompt(display_name: str, *, history_empty: bool) -> str:
    greeting = (
        f"Na primeira mensagem desta conversa (histórico vazio), cumprimente pelo nome "
        f"(ex.: Olá, {display_name}, sou a {ASSISTANT_NAME} — no que posso ajudar?). "
        if history_empty
        else ""
    )
    return (
        f"Você é a {ASSISTANT_NAME}, assistente do painel IoT (dispositivos MQTT do usuário autenticado). "
        "Responda sempre em português, de forma clara e concisa. "
        f"O usuário autenticado se chama {display_name!r}. "
        f"{greeting}"
        "Escopo IN (scope=product): plataforma TomatoIA/mqtt-chat, adoção de devices, sensores, "
        "atuadores, telemetria, broker MQTT (conceito), perfil do usuário, orientação de uso. "
        "Escopo OUT (scope=off_topic): filmes, artistas, celebridades, criptomoedas/preços (ex.: Bitcoin), "
        "notícias gerais, tarefas escolares sem ligação IoT, entretenimento, política, receitas, etc. "
        "Para off_topic, defina scope=off_topic; o campo reply será ignorado pelo backend. "
        "Para product, preencha reply com a resposta útil. "
        "Não invente devices ou telemetria — sem tools ainda, diga que em breve haverá consulta aos devices do usuário. "
        "Mencione o nome TomatoIA quando natural na resposta in-scope."
    )


def _history_to_model_messages(history: list[tuple[str, str]]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for role, content in history:
        if role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=content)]))
    return messages


def create_chat_agent(settings: Settings) -> Agent[UserDeps, ChatTurnResult]:
    """Factory do agente conforme modelo configurado em env."""
    api_key = settings.google_api_key

    def provider_factory(provider_name: str):
        if provider_name == "google":
            if not api_key:
                raise ValueError("google_api_key_missing")
            return GoogleProvider(api_key=api_key)
        return infer_provider(provider_name)

    model = infer_model(settings.chat_model, provider_factory=provider_factory)
    agent: Agent[UserDeps, ChatTurnResult] = Agent(
        model,
        name="tomato_ia_assistant",
        deps_type=UserDeps,
        output_type=ChatTurnResult,
    )

    @agent.instructions
    def system_prompt(ctx: RunContext[UserDeps]) -> str:
        return _build_system_prompt(
            ctx.deps.display_name,
            history_empty=ctx.deps.history_empty,
        )

    return agent


async def run_chat(
    agent: Agent[UserDeps, ChatTurnResult],
    deps: UserDeps,
    user_message: str,
    history: list[tuple[str, str]],
) -> ChatTurnResult:
    """Executa um turno e retorna classificação + resposta bruta do modelo."""
    message_history = _history_to_model_messages(history)
    result = await agent.run(
        user_message,
        deps=deps,
        message_history=message_history,
    )
    return result.output
