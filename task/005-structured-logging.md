# Task 005 — Política e logging estruturado

> **Status:** Em planejamento (spec v1 entregue — aguardando aprovação)  
> **Fase:** PoC / preparação MCP  
> **Depende de:** [004-mqtt-worker.md](004-mqtt-worker.md)  
> **Bloqueia:** tools FastMCP / MCP (decisão de produto: logging antes do MCP)

## Objetivo

Definir e implementar **logging estruturado** no backend para:

1. **Entrada de dados** — mensagens MQTT recebidas (metadados, não secrets).
2. **Transformação** — parse de tópico, validação Pydantic, normalização telemetria.
3. **Erros** — severidade, **módulo/logger**, **função**, **linha**, stack trace.

Saída alinhada a **ferramentas de telemetria/observabilidade** (JSON indexável; compatível com [Cloud Logging structured](https://cloud.google.com/logging/docs/structured-logging) e modelo [OpenTelemetry Logs](https://opentelemetry.io/docs/specs/otel/logs/data-model/)).

Entregável normativo: [`docs/logging.md`](../docs/logging.md) **v1**.

---

## Análise (estado atual vs alvo)

### Situação hoje (pós-004)

| Aspecto | Hoje | Problema |
|---------|------|----------|
| Formato | `basicConfig` texto em `worker.__main__` | Difícil filtrar por `device_id`, `event` |
| Módulos | `logging.getLogger(__name__)` espalhado | OK para `logger`; falta contrato de campos |
| Ingestão | INFO só em modo `log`; Firestore quase mudo | Não vê pipeline entrada→persist |
| Erros | `logger.exception` em handler | Texto livre; não padroniza JSON |
| Secrets | Sem filtro | Risco futuro (adopt, MQTT password) |

### Referências oficiais aplicadas

| Documento | Decisão derivada |
|-----------|------------------|
| **Python 3 logging** | Usar `LogRecord` (`name`, `funcName`, `lineno`, `module`); um `Logger` por módulo; config centralizada |
| **Google Cloud structured logging** | **JSON** em stdout; campos nomeados para query (`jsonPayload` no GCP) |
| **OpenTelemetry log data model** | Campos `severity`, `body`/`message`, `attributes`, **`event` name** estável; ERROR para falhas |
| **FastAPI** | Configurar logging no startup/lifespan; uvicorn herda root logger |
| **Firebase** | Projeto GCP → logs estruturados facilitam correlacionar worker e Firestore |

**Não** adotar na v1: OpenTelemetry SDK completo, LangChain, SQLite de logs.

### Alternativas consideradas

| Opção | Prós | Contras | Veredito |
|-------|------|---------|----------|
| Texto + grep | Simples | Ruim para telemetria/Cloud | Rejeitado como default |
| `structlog` | Ergonómico | Dependência extra; regra diz uv add explícito | Opcional v1.1 |
| **stdlib + JsonFormatter** | Zero deps novas, oficial Python | Mais boilerplate | **v1 recomendado** |
| Print JSON | — | Fora do padrão FastAPI | Rejeitado |

---

## Matriz de versões

| Componente | Versão | Notas |
|------------|--------|--------|
| Python | ≥3.13 | `logging` stdlib |
| FastAPI / uvicorn | lock atual | Access log separado; política cobre app loggers |
| Deploy futuro GCP | — | stdout JSON → Cloud Logging automático em Cloud Run |

---

## Entregáveis (checklist)

- [x] [`docs/logging.md`](../docs/logging.md) v1 (taxonomia `event`, campos, redação, arquitetura)
- [ ] Aprovação humana §12 de `docs/logging.md`
- [x] `src/mqtt_chat/logging/` — ver [`docs/logging.md`](../docs/logging.md) §2 e §9
- [x] Env: `LOG_LEVEL`, `LOG_FORMAT`, `LOG_SERVICE_NAME` em `.env.example`
- [x] Integrar setup em `worker.__main__` e `api.app` lifespan
- [x] Refatorar ingestão: eventos entrada → parse → persist (worker/services/clients)
- [ ] Teste: erro forçado + redação password + `jq` em uma linha
- [ ] Link em [`docs/requirements.md`](../docs/requirements.md) e regra Cursor (1 parágrafo)
- [ ] Atualizar [`task/README.md`](README.md)

---

## Decisão de produto (2026-10-10)

- **Logs não** são medição de desempenho (`duration_ms`, percentis, alertas de latência).
- **Métricas de performance** → implementação futura (OTel Metrics ou equivalente), pacote/camada separada.

## Fora de escopo (task 005)

- OpenTelemetry Collector / export OTLP / **métricas de desempenho**
- Logs do simulador embarcado (`scripts/devices/`)
- Audit log de ações MCP (task MCP posterior, mas **usar mesma taxonomia**)
- Frontend browser logging

---

## Critérios de verificação

1. Worker em `LOG_FORMAT=json` emite JSON válido por linha.
2. Simulador + worker: pelo menos um ciclo com eventos de entrada e persistência identificáveis no JSON.
3. `logger.exception` em falha simulada inclui `code.line` e stack.
4. String `password=secret` em atributo logado → `[REDACTED]`.
5. Nenhum teste/commit inclui `secrets/service-account.json`.

---

## Ordem no roadmap

```
004 worker → 005 logging → 006 MCP (sugerido)
```

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-10 | Task criada; `docs/logging.md` v1 (documento único) |
