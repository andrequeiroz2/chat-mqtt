# Task 021 — Chat deterministic-first (inventário no resolver + loop guard + parada)

## Objetivo

Inverter a dependência do LLM: **intenções de produto são determinísticas**; LLM só para conversa aberta. Eliminar a classe de incidentes vista em 2026-10-18/19 (proatividade → 500; loop de tools → 503) sem trocar de modelo (`gpt-4o-mini` permanece — decisão do usuário).

## Contexto

Reprodução confirmada com [`scripts/repro_inventory_loop.py`](../scripts/repro_inventory_loop.py): com o histórico real da sessão, `gpt-4o-mini` ignora a regra anti-proatividade (020-02) e entra em loop `list_devices` ↔ `read_latest_telemetry` até `UsageLimitExceeded` para a pergunta "tenho algum sensor registrado?". Causa: histórico rico em telemetria + modelo fraco em regra negativa + inventário sem caminho determinístico (F3 da task 020). Evidência: 100% dos incidentes vieram do caminho LLM; o resolver nunca falhou assim.

## Entregáveis

| # | Item | Arquivo(s) |
|---|------|-----------|
| 021-01 | **Intent `list_devices` no resolver**: padrões "quantos/quais/tenho devices/sensores/atuadores (registrados/adotados)" → templates fixos (inventário vazio / 1 / N devices; filtro sensor/atuador; ambíguo sem tipo → lista tudo). Zero LLM. | `src/mqtt_chat/schemas/device_intent.py`, `src/mqtt_chat/services/device_intent_resolver.py`, `src/mqtt_chat/services/resolver_turn.py`, templates |
| 021-02 | **Loop guard**: mesma tool ≥2× com args equivalentes no turno → `ToolFailed("tool_loop_detected: responda agora com os dados que já obteve")` (não consome retry budget; modelo finaliza). | `src/mqtt_chat/agent/` (capability/hook) |
| 021-03 | **Prompt: regra de parada positiva** substituindo a proibitiva da 020-02: "Após uma tool responder à pergunta, emita a resposta final IMEDIATAMENTE; no máximo 2 tools por turno." | `src/mqtt_chat/agent/chat_agent.py` |
| 021-04 | Testes: intent inventário (vazio/1/N/filtro), loop guard dispara e run finaliza, prompt contém regra de parada. Suíte verde. | `tests/` |

## Fora de escopo

- Trocar o modelo (`gpt-4o-mini` fica — decisão explícita do usuário).
- Expandir resolver para outras intenções além de inventário (help, perfil — futuras).
- Streaming SSE; mudanças de frontend.

## Critérios de verificação

- [ ] `uv run python scripts/repro_inventory_loop.py`: "tenho algum sensor registrado?" resolvido **sem LLM** (resolver) ou, forçando LLM, loop guard para em ≤3 tool calls.
- [ ] `uv run pytest` verde.
- [ ] Verificação manual no chat: "quantos dispositivos eu tenho?", "quais são os meus sensores?", "tenho algum sensor registrado?" respondem instantaneamente (sem chamada OpenAI nos logs).

## Checklist

- [x] 021-01 intent inventário no resolver (G13) + templates
- [x] 021-02 loop guard ([`agent/loop_guard.py`](../src/mqtt_chat/agent/loop_guard.py); contagem em `UserDeps.tool_call_counts` por turno)
- [x] 021-03 regra de parada no prompt (substitui a proibitiva da 020-02)
- [x] 021-04 testes (5 G13 + 5 templates inventário + 2 loop guard + prompt) — **83 passando**
- [x] Atualizar status aqui e no [README](README.md)

## Notas

- Origem: incidentes 2026-10-18 (500) e 2026-10-19 (503 loop); análise e reprodução na conversa.
- Decisão: deterministic-first — LLM só para conversa aberta (policy §12.1 já prevê resolver como autoridade primária).
- Skill: `building-pydantic-ai-agents` (loop guard via capability/hook de tool).

## Status

- 2026-10-18 — Criada (direção aprovada: deterministic-first completo).
- 2026-10-18 — **Concluída** (verificação manual no chat pendente). Aceites: [`repro_inventory_loop.py`](../scripts/repro_inventory_loop.py) → **0 chamadas ao LLM** ("Você tem **1 sensor** adotado: Meu sensor — online"); caminho LLM forçado com modelo+histórico reais → 2 tool calls e finaliza (antes: 15 → 503). Fix bônus: `_device_type_hint_from_message` aceita plurais ("sensores", "atuadores").
