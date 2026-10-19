# Task 022 — G14 (metadados do device) + gate de suggested_ui

## Objetivo

Fechar as duas lacunas do incidente "que dia ele foi registrado?" (2026-10-19, 01:03): LLM chamou `get_telemetry_history` **não solicitada** (abriu gráfico + incluiu leituras na resposta) antes de `list_devices`. Resposta certa com 2 enfeites não pedidos.

## Contexto

Sequência real (logs): modelo chamou `get_telemetry_history(days=30)` → abriu bolha de gráfico via `suggested_ui` e trouxe min/max/latest → `list_devices` (de onde veio `adopted_at`) → resposta com data correta **+ leituras + gráfico não pedidos**. Loop guard não se aplica (tools diferentes); regra de parada ("máx. 2 tools") virou licença. Causa estrutural: (a) metadado do device cai no LLM apesar de `adopted_at` estar no snapshot; (b) `suggested_ui` propaga sem validação contra a mensagem do usuário.

## Entregáveis

| # | Item | Arquivo(s) |
|---|------|-----------|
| 022-01 | **G14 — intent `device_metadata`**: "que dia/quando/em que data foi registrado/adotado/cadastrado" → resposta do snapshot (`adopted_at`), zero LLM. Resolução: nome citado → foco de sessão → device único; múltiplos sem alvo → clarify; inventário vazio → template. | `schemas/device_intent.py`, `services/device_intent_resolver.py`, `services/resolver_turn.py`, `services/conversation_templates.py` |
| 022-02 | **Gate de `suggested_ui`** no caminho LLM: `TelemetryChartSuggestedUi` só propaga se `detect_chat_intent(msg) == "telemetry_history"`; `RealtimeTelemetrySuggestedUi` só se `== "realtime"`. Função pura testável. | `services/chat_turn.py` |
| 022-03 | Prompt: metadados (data de adoção, modelo, status) → UMA chamada a `list_devices`, sem leituras/gráficos extras. | `agent/chat_agent.py` |
| 022-04 | Testes: G14 (nome/foco/único/clarify/vazio), gate (passa/bloqueia chart e realtime), prompt. Suíte verde. | `tests/` |

## Fora de escopo

- Expandir G14 para outros metadados além de data de adoção (modelo, status — templates futuros).
- Mudar formato de data na bolha de gráfico; unit "°C" cosmético.

## Critérios de verificação

- [x] "que dia ele foi registrado?" → resolver G14, zero chamada OpenAI (verificado manualmente no chat em 2026-10-18: "quando ele foi registrado?" → "O sensor Meu sensor foi adotado (registrado) em 14/10/2026.").
- [x] Pergunta sem pedido de gráfico que dispare `get_telemetry_history` no LLM → bolha de gráfico **não** aparece (gate testado como função pura; manual pendente).
- [ ] Pedido explícito de gráfico/tempo real → bolha continua abrindo (caminho resolver e LLM) — verificação manual pendente.
- [x] `uv run pytest` verde (97 passando).

## Checklist

- [x] 022-01 G14
- [x] 022-02 gate suggested_ui
- [x] 022-03 prompt metadados
- [x] 022-04 testes
- [x] Atualizar status aqui e no [README](README.md)

## Notas

- Origem: análise do turno 01:03:06–01:03:10 (logs) em 2026-10-19.
- Skill: `building-pydantic-ai-agents` (não requerida para o gate — lógica de serviço).

## Status

- 2026-10-18 — Criada (aprovada; implementação pendente).
- 2026-10-18 — **Concluída** (verificação manual no chat pendente): G14 no resolver (`detect_adoption_date_question` + `_resolve_adoption_date`), template `template_adoption_date` (data PT DD/MM/YYYY), gate `gate_suggested_ui_by_intent` no caminho LLM, regra de metadados no prompt. Suíte: 97 testes passando.
- 2026-10-18 — **Verificação manual OK**: "eu tenho algum sensor registrado?" → G13 inventário ("Você tem 1 sensor adotado: Meu sensor — online"); "quando ele foi registrado?" → G14 com foco de sessão ("O sensor Meu sensor foi adotado (registrado) em 14/10/2026.").
