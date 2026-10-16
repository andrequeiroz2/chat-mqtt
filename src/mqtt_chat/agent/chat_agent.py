"""Agente TomatoIA (Pydantic AI) — escopo produto IoT e saída estruturada."""

from __future__ import annotations

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import infer_model
from pydantic_ai.providers import infer_provider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from mqtt_chat.agent.deps import UserDeps
from mqtt_chat.agent.device_tools import register_device_tools
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
        "Para listar ou filtrar devices já adotados (todos, sensores, atuadores, por nome), "
        "use a tool list_devices — nunca invente devices. "
        "Para última leitura pontual, temperatura ou umidade agora, "
        "use read_latest_telemetry (prefira device_name; nunca cite device_id UUID ao usuário). "
        "Para ver valores em tempo real, stream contínuo ou monitorar ao vivo no chat, "
        "use start_realtime_telemetry (mesmos parâmetros de device). "
        "Nunca invente números de telemetria. "
        "Endereço MAC e IP local do device não estão nas tools — não chame list_devices em loop; "
        "perguntas sobre MAC/IP são escopo produto (explique limites), não off_topic. "
        "Tópicos MQTT seguem tenants/{user_id}/devices/{device_id}/telemetry|commands|state|status — "
        "nunca invente paths como sensors/nome. "
        "Evite repetir a mesma tool se o resultado já respondeu ao pedido. "
        "Para adicionar um device à conta, oriente o usuário ao fluxo de adoção na interface "
        "(QR / pareamento no chat); você não executa adoção. "
        "Siga docs/chat-conversational-policy.md: clarifique device ambíguo; atuador não tem "
        "telemetria de sensor; offline — última leitura histórica com alerta; tempo real só online; "
        "comandos de atuador (ligar/desligar) viram valor digital 0/1 com confirmação. "
        "Quando o backend já respondeu com template fixo, não contradiga. "
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
    def provider_factory(provider_name: str):
        if provider_name == "google":
            if not settings.google_api_key:
                raise ValueError("google_api_key_missing")
            return GoogleProvider(api_key=settings.google_api_key)
        if provider_name == "openai":
            if not settings.openai_api_key:
                raise ValueError("openai_api_key_missing")
            return OpenAIProvider(api_key=settings.openai_api_key)
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

    register_device_tools(agent)
    return agent


async def run_chat(
    agent: Agent[UserDeps, ChatTurnResult],
    deps: UserDeps,
    user_message: str,
    history: list[tuple[str, str]],
    *,
    request_limit: int = 15,
) -> ChatTurnResult:
    """Executa um turno e retorna classificação + resposta bruta do modelo."""
    message_history = _history_to_model_messages(history)
    result = await agent.run(
        user_message,
        deps=deps,
        message_history=message_history,
        usage_limits=UsageLimits(request_limit=request_limit),
    )
    return result.output
