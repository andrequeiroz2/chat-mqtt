# Task 019 — Sincronização docs ↔ código (requirements, glossário, contratos)

## Objetivo

Corrigir divergências encontradas na auditoria docs-vs-código (2026-10-18): documentação **somente** (sem alteração de código), para que `docs/` volte a refletir a implementação real.

## Contexto

Auditoria completa dos `.md` de `docs/` cruzados com `src/mqtt_chat/`. Documentos conformes: `auth.md`, `contracts/mcp-list-devices.md`, `contracts/device-adoption.md` (pós-017), `contracts/mcp-read-latest-telemetry.md`, `chat-conversational-policy.md` (pós-018), `contracts/chat-streaming-ux.md` (marca fases honestamente). Divergências listadas abaixo.

## Entregáveis

| # | Item | Arquivo | Divergência |
|---|------|---------|-------------|
| 019-01 | Corrigir §3.1 e §7: assinatura real de `get_telemetry_history` no **agente** é `TelemetryHistoryInput` = `device_id?`, `device_name?`, `metric?`, `days` (1–30), `last_day_with_data` — **não** `period`, **não** `start`/`end`. Registrar também que o resolver pré-LLM pode atender sem LLM (policy §12.1). | [`docs/requirements.md`](../docs/requirements.md) |
| 019-02 | Corrigir §7 "Tools MCP mínimas": o servidor real ([`src/mqtt_chat/server.py`](../src/mqtt_chat/server.py)) registra **4** tools — `list_devices`, `read_latest_telemetry`, `publish_command`, `get_realtime_stream_info`. `update_device`/`remove_device`/`get_telemetry_history` **não** estão no MCP (as duas primeiras são planejadas; a última existe só no agente Pydantic AI). Marcar planejadas como tais. | [`docs/requirements.md`](../docs/requirements.md) |
| 019-03 | Status do cabeçalho: "Aprovado para implementação" → **Implementado** (task 011 ondas 1–2; schema em `schemas/conversation_context.py`). | [`docs/contracts/chat-session-context.md`](../docs/contracts/chat-session-context.md) |
| 019-04 | Tabela de tools MCP: marcar quais estão **implementadas** (`list_devices`, `read_latest_telemetry`, `publish_command`, `get_realtime_stream_info`) vs **planejadas** (`update_device`, `remove_device`); `get_telemetry_history` (MCP) permanece fora do servidor — existe apenas no agente. | [`docs/glossary.md`](../docs/glossary.md) |
| 019-05 | Nota explícita na fase 1: endpoint `POST /api/v1/chat/stream` existe no backend mas **não** é consumido pelo frontend ([`ChatScreen.tsx`](../services/frontend/src/chat/ChatScreen.tsx) usa só `postChat`); `paths.ts` define `chatStream` sem consumidor. | [`docs/contracts/chat-streaming-ux.md`](../docs/contracts/chat-streaming-ux.md) |

## Fora de escopo

- Alterar código, tools ou comportamento do agente.
- Implementar streaming SSE token-a-token (fase 2 de `chat-streaming-ux.md`).
- Criar `update_device`/`remove_device`/`get_telemetry_history` no MCP.

## Critérios de verificação

- [ ] `requirements.md` §3.1 e §7 descrevem assinatura e lista de tools iguais ao código.
- [ ] `glossary.md` distingue tools implementadas de planejadas.
- [ ] `chat-session-context.md` com status "Implementado".
- [ ] `chat-streaming-ux.md` com nota sobre `/chat/stream` sem consumidor frontend.
- [ ] Nenhum arquivo Python/TS alterado (`git status` mostra apenas `docs/` e `task/`).

## Checklist

- [x] 019-01 assinatura `get_telemetry_history` em requirements
- [x] 019-02 lista tools MCP em requirements
- [x] 019-03 status chat-session-context
- [x] 019-04 glossário implementado/planejado
- [x] 019-05 nota /chat/stream sem consumidor
- [x] Atualizar status aqui e no [README](README.md)

## Notas

- Origem: auditoria solicitada em 2026-10-18 ("análise dos .md em docs vs código implementado").
- Skill aplicável: nenhuma específica (edição de documentação apenas); manter PT em docs conforme RNF-I18N-01.

## Status

- 2026-10-18 — Criada (auditoria concluída; correções pendentes).
- 2026-10-18 — **Concluída.** 019-01…019-05 aplicados; apenas `docs/` e `task/` alterados (nenhum arquivo de código).
