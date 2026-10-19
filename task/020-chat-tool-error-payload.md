# Task 020 — Erros de tool como payload + prompt anti-proatividade

## Objetivo

Corrigir a falha sistêmica em que **qualquer erro de domínio de tool do agente vira HTTP 500** (pergunta trivial de inventário → 500 em 2026-10-18) e coibir **tool calls não solicitadas** do LLM.

## Contexto

Incidente real: usuário perguntou "tenho algum sensor registrado?" → resolver `pass_through` (inventário não tem intent) → LLM chamou `list_devices` (respondia a pergunta) **e** `get_telemetry_history` (não solicitada) → `telemetry_history_empty` → `raise ValueError` escapa do `agent.run` (Pydantic AI só vira tool-error/retry com `ModelRetry`) → `execute_chat_turn` sem `except` → rota só trata `UsageLimitExceeded`/`ModelHTTPError` → **500**.

Três falhas:

- **F1** — LLM pró-ativo: prompt ([`chat_agent.py`](../src/mqtt_chat/agent/chat_agent.py) `_build_system_prompt`) só diz "evite repetir a mesma tool"; não proíbe acrescentar tools sem pedido.
- **F2** — `raise ValueError(exc.code)` em [`device_tools.py`](../src/mqtt_chat/agent/device_tools.py) propaga para fora do run; o prompt da 018 ("Erros de tool") pressupõe códigos que **nunca chegam ao modelo**.
- **F3** — Inventário ("quais/quantos devices tenho?") não tem caminho determinístico no resolver (policy §12.1).

## Entregáveis

| # | Item | Arquivo(s) |
|---|------|-----------|
| 020-01 | **F2 — erro de tool visível ao modelo**: tools do agente (`list_devices`, `read_latest_telemetry`, `start_realtime_telemetry`, `get_telemetry_history`) sobem `ToolFailed(exc.code)` em vez de `ValueError` — o modelo recebe o resultado como falha (`{"error": code}` / campo nativo do provider) e adapta a resposta conforme a seção "Erros de tool" do prompt; não consome retry budget. Manter `raise` **somente** nas tools MCP (`tools/`), onde o MCP layer mapeia erro. | `src/mqtt_chat/agent/device_tools.py` |
| 020-02 | **F1 — regra no prompt**: "Responda somente o escopo da pergunta. Inventário (quais/quantos devices) se resolve só com `list_devices`; não chame tools de telemetria, histórico ou tempo real sem pedido explícito." | `src/mqtt_chat/agent/chat_agent.py` |
| 020-03 | **F3 (opcional)**: intent determinística `list_devices` no resolver para perguntas de inventário ("quais devices tenho?", "tenho algum sensor/atuador?") com template fixo. | `src/mqtt_chat/services/device_intent_resolver.py`, `src/mqtt_chat/schemas/device_intent.py` |
| 020-04 | Testes: erro de tool retorna payload (não propaga); prompt contém regra anti-proatividade; (se 020-03) intent inventário. | `tests/` |

## Fora de escopo

- Alterar tools MCP (`tools/`) — lá o `raise` é o contrato correto (MCP layer trata).
- Expor `last_day_with_data` na tool do agente (registrado como pendência; pode entrar se trivial).
- Streaming SSE; refactor do resolver além de F3.

## Critérios de verificação

- [ ] Pergunta "tenho algum sensor registrado?" não gera 500 mesmo se `get_telemetry_history` falhar.
- [ ] Erros de domínio chegam ao modelo como resultado de tool (log mostra resposta amigável, não traceback).
- [ ] `uv run pytest` verde.
- [ ] Verificação manual no chat: pergunta de inventário não dispara tool de histórico.

## Checklist

- [x] 020-01 erro de tool via `ToolFailed` nas tools do agente (4 tools)
- [x] 020-02 regra anti-proatividade no prompt
- [ ] 020-03 (opcional) intent inventário no resolver — **adiada** (ver Notas)
- [x] 020-04 testes ([`tests/test_chat_agent_tool_failures.py`](../tests/test_chat_agent_tool_failures.py) + assert no prompt)
- [x] Atualizar status aqui e no [README](README.md)

## Notas

- Origem: incidente 2026-10-18 (terminal 4, POST /api/v1/chat → 500; análise na conversa).
- Skill: `building-pydantic-ai-agents` (tools/erros de tool).
- Decisão: opção **(a)** da análise, refinada pela skill `building-pydantic-ai-agents` (TOOLS-ADVANCED "Report a Failed Tool Result"): usar **`ToolFailed`** (pydantic_ai 2.55.0 ✅) — mecanismo nativo, sem mexer nos schemas de resultado; "qualquer outra exceção propaga e aborta o run" = causa raiz do 500.
- F3 (intent inventário no resolver) **adiada** — F1+F2 resolvem o incidente; F3 é extensão de design (registrar em task futura se desejado).

## Status

- 2026-10-18 — Criada (aprovada; implementação pendente).
- 2026-10-18 — **Concluída** (verificação manual no chat pendente). 020-01/020-02/020-04 implementados; **71 testes** passando. F3 (intent inventário) adiada para task futura.
