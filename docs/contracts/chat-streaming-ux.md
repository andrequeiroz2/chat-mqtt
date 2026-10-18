# Contrato UX — streaming e estados do assistant (chat)

> **Status:** v1 (normativo para frontend TomatoIA)  
> **Tasks:** [006](../task/006-user-auth-chat-mcp.md) (RF-CHAT-03), [012](../task/012-frontend-modern-ui-stack.md) (shadcn / AI Elements), bootstrap [013](../task/012-frontend-modern-ui-stack.md#ordem-sugerida-pós-decisão)  
> **Referência externa (padrão de mercado):** [shadcn/ui — AI Elements](https://ui.shadcn.com/docs/ai-elements), repositório [shadcn/ai-elements](https://github.com/shadcn/ai-elements) (`Loader`, `Message`, `Conversation`, `Shimmer`)

Comportamento esperado da **bolha do assistant** enquanto o backend processa um turno: “pensando” (três pontos) e, em seguida, texto aparecendo como **digitação** (streaming token a token).

---

## 1. Estados da UI (por turno)

| Estado | Quando | O que o usuário vê |
|--------|--------|-------------------|
| **`idle`** | Nenhum turno em andamento | Thread estática; composer habilitado. |
| **`thinking`** | Pedido enviado; **ainda não há** texto do assistant (modelo/tools em execução) | Bolha assistant com **indicador de três pontos** animados (variante “typing” / “dots”), dentro do token `card`/`muted` (tema dark §012). **Sem** texto parcial. |
| **`streaming`** | Primeiro **token** (ou chunk) de texto do assistant recebido | Mesma bolha passa a mostrar texto que **cresce** incrementalmente (efeito “digitando”). Opcional: cursor piscando no fim até `done`. |
| **`done`** | Turno completo (`done` SSE ou resposta REST final) | Bolha final; widgets `suggested_ui` montados; composer habilitado. |
| **`error`** | Falha HTTP/SSE ou `detail` da API | Bolha de erro ou toast; remove indicador `thinking`/`streaming`. |

**Regra:** `thinking` e `streaming` são **mutuamente exclusivos por bolha** — três pontos **somente** enquanto `content === ""` (padrão descrito em [AI Elements / chatbot](https://ui.shadcn.com/docs/ai-elements) e exemplos com `Loader` em [ai-elements](https://github.com/shadcn/ai-elements)).

---

## 2. Requisitos funcionais (RF-UX-STREAM-*)

| ID | Requisito |
|----|-----------|
| RF-UX-STREAM-01 | Após enviar mensagem do usuário, o thread **must** reservar lugar para a resposta do assistant (evitar “pulo” de layout quando o texto chegar). |
| RF-UX-STREAM-02 | Enquanto não houver conteúdo de texto do assistant, **must** exibir animação de **três pontos** (`thinking`). |
| RF-UX-STREAM-03 | Quando o streaming de texto iniciar, **must** ocultar os três pontos e **must** acrescentar tokens/chunks na mesma bolha (`streaming`). |
| RF-UX-STREAM-04 | Durante `thinking` e `streaming`, composer **should** desabilitar envio duplicado (ou enfileirar — **fora de escopo** MVP). |
| RF-UX-STREAM-05 | Scroll: manter usuário no fim do thread durante `streaming`, sem saltos bruscos (Message Scroller / `stick-to-bottom` — padrão AI Elements). |
| RF-UX-STREAM-06 | Copy em **português** opcional ao lado dos pontos (ex.: “Pensando…”) — **muted-foreground**; default **sem** label se poluir UI. |
| RF-UX-STREAM-07 | Tools MCP / turnos sem texto imediato: permanece `thinking` até primeiro texto ou até `done` com payload vazio + widget (`suggested_ui`). |

---

## 3. Transporte backend ↔ frontend

| Caminho | Situação atual | Alvo |
|---------|----------------|------|
| `POST /api/v1/chat` | Resposta **única** após turno completo | Manter para turnos especiais (ex.: pós-adoção); **não** simula digitação. |
| `POST /api/v1/chat/stream` | SSE existe; hoje emite **um** evento `message` com `reply` **inteiro** após `execute_chat_turn` | **Evoluir** para tokens/chunks via Pydantic AI `run_stream` / `run_stream_events` (skill `building-pydantic-ai-agents`, [Run Methods and Streaming](https://pydantic.dev/docs/ai/)). |

### Eventos SSE propostos (v1.1)

| Evento | Payload (JSON) | UI |
|--------|----------------|-----|
| `status` | `{ "phase": "thinking" }` | Opcional; UI pode inferir `thinking` só pelo envio até primeiro `token`. |
| `token` | `{ "text": "..." }` | Append na bolha assistant (`streaming`). |
| `message` | `{ "text": "...", "suggested_ui": ... }` | Metadados finais ou turnos não streamáveis. |
| `done` | `{ "session_id": "..." }` | `done`; persistência já ocorreu no backend. |
| `error` | `{ "detail": "..." }` | `error` |

Autenticação: igual [`auth.md`](../auth.md) (Bearer). `session_id` inalterado.

---

## 4. Implementação frontend (referência)

- **Componentes:** preferir padrões copiados de [AI Elements](https://ui.shadcn.com/docs/ai-elements) — `Conversation` + `Message` + `Loader` (variante `typing` ou `dots`) ou `Shimmer` se atraso longo **sem** tokens.
- **Estado local:** estender [`ChatMessage`](../services/frontend/src/types/chat-ui.ts) ou mensagem assistant com `status?: 'thinking' | 'streaming' | 'complete'` e `text` acumulado.
- **Hook:** consumir SSE (`fetch` + `ReadableStream` ou `EventSource` conforme CORS/método); path [`chatStream`](../services/frontend/src/api/paths.ts) já definido — **substituir** `postChat` no fluxo principal do composer quando RF-UX-STREAM estiver implementado.

**Fase 1 (REST):** [`ChatScreen.tsx`](../services/frontend/src/chat/ChatScreen.tsx) insere bolha assistant `status: thinking` + [`AssistantThinkingDots`](../services/frontend/src/chat/AssistantThinkingDots.tsx) até `postChat` retornar; substitui pela resposta final. **Sem** streaming token a token (fase 2 = SSE).

---

## 5. Fora de escopo

- Mostrar chain-of-thought / reasoning bruto do modelo (componente `Reasoning` AI Elements — fase posterior).
- Indicador de digitação do **usuário** (presença multi-user).
- CopilotKit runtime.

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-17 | Contrato v1 — thinking (três pontos) + streaming (digitação); referência shadcn AI Elements |
| 2026-10-17 | Fase 1 REST (thinking) verificada manualmente no chat |
