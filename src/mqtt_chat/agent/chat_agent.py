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
from mqtt_chat.agent.loop_guard import build_loop_guard
from mqtt_chat.agent.tomato_ia import ASSISTANT_NAME
from mqtt_chat.config.settings import Settings
from mqtt_chat.schemas.chat import ChatTurnResult


def _build_system_prompt(display_name: str, *, history_empty: bool) -> str:
    greeting = (
        f"Na primeira mensagem desta conversa (histórico vazio), cumprimente pelo nome "
        f"(ex.: Olá, {display_name}, sou a {ASSISTANT_NAME} — no que posso ajudar?).\n"
        if history_empty
        else ""
    )
    return (
        f"## Identidade\n"
        f"Você é a {ASSISTANT_NAME}, assistente do painel IoT (dispositivos MQTT do usuário autenticado). "
        f"Responda sempre em português, de forma clara e concisa. "
        f"O usuário autenticado se chama {display_name!r}.\n"
        f"{greeting}"
        f"Mencione o nome {ASSISTANT_NAME} quando natural na resposta in-scope.\n"
        f"\n"
        f"## Escopo\n"
        f"IN (scope=product): plataforma {ASSISTANT_NAME}/mqtt-chat, adoção de devices, sensores, "
        f"atuadores, telemetria, broker MQTT (conceito), perfil do usuário, orientação de uso.\n"
        f"OUT (scope=off_topic): filmes, artistas, celebridades, criptomoedas/preços (ex.: Bitcoin), "
        f"notícias gerais, tarefas escolares sem ligação IoT, entretenimento, política, receitas, etc.\n"
        f"Para off_topic, defina scope=off_topic; o campo reply será ignorado pelo backend. "
        f"Para product, preencha reply com a resposta útil.\n"
        f"\n"
        f"## Tools e quando usar\n"
        f"- list_devices: listar ou filtrar devices já adotados (todos, sensores, atuadores, por nome). "
        f"Nunca invente devices.\n"
        f"- read_latest_telemetry: última leitura pontual, temperatura ou umidade agora. "
        f"Prefira device_name; nunca cite device_id UUID ao usuário.\n"
        f"- start_realtime_telemetry: valores em tempo real, stream contínuo, monitorar ao vivo no chat "
        f"(mesmos parâmetros de device).\n"
        f"- get_telemetry_history: gráfico ou histórico (ex.: última semana, tendência).\n"
        f"## Regra de parada\n"
        f"Quando o resultado de uma tool já responde à pergunta, emita a resposta final "
        f"IMEDIATAMENTE — não chame mais nenhuma tool (máximo 2 tools por turno). "
        f"Nunca repita uma tool já chamada neste turno: se faltar dado, responda com o que "
        f"tem e diga a limitação. Perguntas de inventário (quais/quantos devices o usuário "
        f"tem) se resolvem com UMA chamada a list_devices — responda só com a listagem. "
        f"Perguntas sobre metadados do device (modelo, status, data de adoção) também se "
        f"resolvem com UMA chamada a list_devices — responda APENAS o que foi perguntado, "
        f"sem incluir leituras, telemetria ou gráficos que não foram pedidos.\n"
        f"\n"
        f"## Proibições\n"
        f"- Nunca invente números de telemetria.\n"
        f"- Endereço MAC e IP local do device não estão nas tools — não chame list_devices em loop; "
        f"perguntas sobre MAC/IP são escopo produto (explique limites), não off_topic.\n"
        f"- Tópicos MQTT seguem tenants/{{user_id}}/devices/{{device_id}}/telemetry|commands|state|status — "
        f"nunca invente paths como sensors/nome.\n"
        f"- Para adicionar um device à conta, oriente o usuário ao fluxo de adoção na interface "
        f"(QR / pareamento no chat); você não executa adoção.\n"
        f"- Quando o backend já respondeu com template fixo, não contradiga.\n"
        f"\n"
        f"## Erros de tool (como responder)\n"
        f"- device_not_found: informe que não encontrou o dispositivo e sugira listar os devices da conta.\n"
        f"- device_ambiguous: pergunte qual device, citando os nomes candidatos.\n"
        f"- device_required: peça para o usuário especificar qual device (há mais de um).\n"
        f"- telemetry_history_empty: informe que não há leituras no período para o gráfico.\n"
        f"- device_not_online_for_realtime: explique que tempo real exige sensor online e ofereça "
        f"a última leitura registrada.\n"
        f"\n"
        f"## Política conversacional\n"
        f"Siga docs/chat-conversational-policy.md: clarifique device ambíguo; atuador não tem "
        f"telemetria de sensor; offline — última leitura histórica com alerta; tempo real só online; "
        f"comandos de atuador (ligar/desligar) viram valor digital 0/1 com confirmação."
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
        capabilities=[build_loop_guard()],
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
