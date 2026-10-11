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

Referências: [`docs/requirements.md`](../docs/requirements.md) · [`.cursor/rules/mqtt-chat-project.mdc`](../.cursor/rules/mqtt-chat-project.mdc)
