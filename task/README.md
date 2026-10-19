# Tasks — mqtt-chat

Planejamento executável do projeto. Texto em **português**; identificadores técnicos conforme [`docs/glossary.md`](../docs/glossary.md).

## Convenção de nomes

| Tipo | Padrão | Quando usar |
|------|--------|-------------|
| Task | `NNN-<slug>.md` | **Padrão.** Um arquivo contém objetivo, versões, entregáveis, verificação e checklist completo. |
| Subtask (opcional) | `NNN-SS-<slug>.md` | Só se a task **001** for grande demais; aí a mãe fica `001-<epic>.md` e filhas `001-01-…`. Preferir **uma task detalhada** em vez de mãe + subtask vazia. |

- `NNN` = três dígitos (`001`, `002`, …).
- `SS` = dois dígitos (`01`, `02`, …) — **somente** se houver subtask.
- `<slug>` = kebab-case em **inglês** (ex.: `docker`, `mqtt-worker`).

Cada task **DEVE** incluir, quando aplicável: **matriz de versões** (Docker, imagens, runtime), entregáveis, fora de escopo e critérios de verificação.

## Status

| ID | Arquivo | Status |
|----|---------|--------|
| 001 | [001-docker.md](001-docker.md) | Concluída |
| 002 | [002-device-simulator.md](002-device-simulator.md) | Concluída |
| 003 | [003-adoption-network-contracts.md](003-adoption-network-contracts.md) | Concluída (spec v1; aprovação humana pendente) |
| 004 | [004-mqtt-worker.md](004-mqtt-worker.md) | Concluída (PoC) |
| 005 | [005-structured-logging.md](005-structured-logging.md) | Em planejamento (spec v1) |
| 006 | [006-user-auth-chat-mcp.md](006-user-auth-chat-mcp.md) | Em execução (6c MCP HTTP; 6d `list_devices` no chat) |
| 007 | [007-tomatoia-chat-guardrails.md](007-tomatoia-chat-guardrails.md) | Em execução (v1 implementada; verificação manual pendente) |
| 008 | [008-device-adoption-handshake-refinement.md](008-device-adoption-handshake-refinement.md) | Em planejamento (contrato v1.2-dev; backend adoção) |
| 009 | [009-adoption-guided-chat-ux.md](009-adoption-guided-chat-ux.md) | Em execução (009a MAC dev + polling no chat; QR câmera pendente) |
| 010 | [010-embedded-esp32c3-micropython.md](010-embedded-esp32c3-micropython.md) | Em execução (WiFi fixo + handshake UC-A v0.1) |
| 011 | [011-chat-session-context-policy.md](011-chat-session-context-policy.md) | MVP entregue (ondas 1–2 ✅; sem onda 3 — retomar opcionais/docs) |
| 012 | [012-frontend-modern-ui-stack.md](012-frontend-modern-ui-stack.md) | Em execução (stack + direção visual dark/zinc ✅; bootstrap na 013) |
| 013 | [013-frontend-tailwind-shadcn-bootstrap.md](013-frontend-tailwind-shadcn-bootstrap.md) | Concluída (Tailwind 4 + shadcn dark/zinc; dev via Docker `profile ui`) |
| 014 | [014-telemetry-chart-recharts.md](014-telemetry-chart-recharts.md) | Concluída (`get_telemetry_history` + bolha Recharts no chat) |
| 016 | [016-frontend-review-hardening.md](016-frontend-review-hardening.md) | Concluída (hardening frontend pós-revisão) |
| 017 | [017-telemetry-payload-unit-required.md](017-telemetry-payload-unit-required.md) | Concluída (`unit` obrigatório na telemetria; descarte parcial) |
| 018 | [018-chat-agent-rules-review.md](018-chat-agent-rules-review.md) | Concluída (prompt em seções; erros de tool; policy §12.1–12.2) |
| 019 | [019-docs-code-sync.md](019-docs-code-sync.md) | Concluída (requirements §3.1/§7, glossário, chat-session-context e chat-streaming-ux sincronizados com o código) |

Referências: [`docs/requirements.md`](../docs/requirements.md) · [`.cursor/rules/mqtt-chat-project.mdc`](../.cursor/rules/mqtt-chat-project.mdc)
