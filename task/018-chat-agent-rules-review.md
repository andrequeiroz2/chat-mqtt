# Task 018 — Revisão de regras do agente chat (prompt + policy)

> **Status:** Concluída (67 testes verdes; policy §12.1–12.2 atualizada)  
> **Origem:** Análise de contratos do chat (2026-10-18) — regras Pydantic AI, direcionamento pré-LLM ([`chat_agent.py`](../src/mqtt_chat/agent/chat_agent.py), [`device_intent_resolver.py`](../src/mqtt_chat/services/device_intent_resolver.py), [`chat-conversational-policy.md`](../docs/chat-conversational-policy.md))  
> **Skill:** [`building-pydantic-ai-agents`](../.agents/skills/building-pydantic-ai-agents/SKILL.md)  
> **Escopo:** system prompt, policy doc, invariantes internas. **NÃO** alterar comportamento de tools, resolver (regex/intents), schemas de saída, contratos HTTP/MQTT ou glossário.

## Objetivo

Tornar as regras que direcionam o entendimento **antes** do LLM mais **claras, coerentes e imperativas** — reduzindo dependência de “regras só no prompt” para casos que o código já deveria garantir.

## Contexto (da análise)

A arquitetura resolver → LLM está correta: casos críticos (offline, comando, clarificação, gráfico) já são short-circuit determinístico. As fragilidades são de **organização das instruções** e **contratos implícitos**, não de design.

## Entregáveis

- [x] **018-01** **Reestruturar system prompt** em [`chat_agent.py`](../src/mqtt_chat/agent/chat_agent.py) (`_build_system_prompt`) em seções curtas e numeradas: `## Identidade`, `## Escopo`, `## Tools e quando usar`, `## Proibições`, `## Erros de tool (como responder)`, `## Política conversacional`. Personalização `display_name` / `history_empty` e todo o conteúdo normativo preservados.
- [x] **018-02** **Instruir tratativa por código de erro** das tools no prompt: `device_not_found`, `device_ambiguous`, `device_required`, `telemetry_history_empty`, `device_not_online_for_realtime` — cada um com orientação de resposta sem inventar valores.
- [x] **018-03** **Policy doc** [`chat-conversational-policy.md`](../docs/chat-conversational-policy.md): §12.1 — resolver determinístico como **autoridade primária**, LLM cobre long tail; §12.2 — heurísticas de período do resolver documentadas (“semana” → 7d, “últimos N dias”, “último dia com registros”, metric por palavra-chave).
- [x] **018-04** **Invariante `suggested_ui`**: documentada em [`deps.py`](../src/mqtt_chat/agent/deps.py) (campo) e [`chat_turn.py`](../src/mqtt_chat/services/chat_turn.py) (ponto de reset) — mecanismo inalterado.
- [x] **018-05** Testes: [`tests/test_chat_agent_system_prompt.py`](../tests/test_chat_agent_system_prompt.py) — seções, códigos de erro, regras núcleo, greeting condicional. Suíte completa: 67 testes verdes.

## Fora de escopo (registrados da análise para decisão futura)

- **R5** — Pós-validação de UUID na reply final (defesa programática contra vazamento de `device_id` quando o LLM improvisa).
- Mover `suggested_ui` para dentro do `output_type` (mudança de contrato do agente).
- Alterar regex/intents do resolver ou cobertura G1–G12.
- Streaming SSE / drawer de sessões.

## Matriz de versões

| Item | Versão |
|------|--------|
| pydantic-ai | lock atual (`uv.lock`) |
| Modelos | `chat_model` em settings (google/openai) |

## Verificação

1. `uv run pytest -q` — suíte verde.
2. Inspeção do system prompt gerado (teste ou script): contém seções e mapeamento de erros.
3. Manual: perguntas fora do resolver (ex.: “o que é um broker MQTT?”) ainda respondidas em PT dentro do escopo; erro de tool (device inexistente) gera resposta orientada, não improviso.

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-18 | Task criada — análise de regras pré-LLM (clareza, coerência, imperatividade) |
| 2026-10-18 | Implementados 018-01 … 018-05; task concluída |
