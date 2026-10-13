# Task 007 — TomatoIA: escopo do chat, guardrails e persistência seletiva

> **Status:** Em execução (implementação v1)  
> **Fase:** Pós-6b, **antes** da 6c (MCP)  
> **Depende de:** [006-user-auth-chat-mcp.md](006-user-auth-chat-mcp.md) (6a/6b — chat mínimo OK)  
> **Relacionada:** [006](006-user-auth-chat-mcp.md) (6c–6d MCP), [005-structured-logging.md](005-structured-logging.md)

## Objetivo

Ajuste fino do **assistente conversacional** para:

1. **Identidade:** apresentar-se como **TomatoIA** (nome do chat e **nome futuro do produto**).
2. **Escopo:** responder **somente** sobre o **produto** (IoT mqtt-chat / TomatoIA) e **devices do `user_id` autenticado** — **não** entretenimento, finanças (ex.: Bitcoin), celebridades, cinema, etc.
3. **Persistência:** turnos **fora do escopo** **não** gravam `user`/`assistant` em Firestore (`chat_sessions/.../messages`).
4. **Resposta padrão** determinística para assuntos não vinculados ao projeto (UX consistente, baixo custo de token).

Análise de **eficiência e precisão** com **Pydantic AI** (Skill `building-pydantic-ai-agents`, refs `AGENTS-CORE.md`, `ARCHITECTURE.md`, `INPUT-AND-HISTORY.md`).

---

## Posição na roadmap

```
006 (6a/6b) ✅  →  007 (TomatoIA + guardrails)  →  006 (6c/6d MCP)
```

A 6c **pode** iniciar em paralelo técnico (servidor MCP), mas o **chat exposto ao usuário** deve refletir TomatoIA e escopo **antes** de tools IoT no agente (6d), para o modelo não “inventar” dados de device.

---

## Requisitos de produto (normativos desta task)

| ID | Requisito |
|----|-----------|
| RF-TOM-01 | Toda resposta **in-scope** identifica o assistente como **TomatoIA** na abertura de sessão (primeiro turno ou histórico vazio). |
| RF-TOM-02 | **In-scope:** adoção/dispositivos, sensores/atuadores, telemetria, broker MQTT (conceito), perfil (`display_name`), orientação de uso da plataforma. |
| RF-TOM-08 | Falha de adoção: usar **`user_message`** do backend ([contrato §4.5](../docs/contracts/device-adoption.md)); **não** citar `session_id`, MAC, tokens ou senhas. |
| RF-TOM-09 | Adoção **guiada no chat** (pré-check, QR embarcado, progresso, menu pós-sucesso): ver [009-adoption-guided-chat-ux.md](009-adoption-guided-chat-ux.md); LLM **conversa** + UI **executa** API/MQTT. |
| RF-TOM-03 | **Out-of-scope:** filmes, artistas, criptomoedas/preços, notícias gerais, tarefas escolares genéricas, código arbitrário sem ligação IoT, etc. |
| RF-TOM-04 | **Out-of-scope:** resposta **fixa** (texto acordado abaixo); **sem** `append_turn` no Firestore. |
| RF-TOM-05 | **In-scope:** persiste par user/assistant como hoje (`CHAT_MAX_TURNS`). |
| RF-TOM-06 | Histórico enviado ao modelo contém **apenas** turnos previamente persistidos (in-scope) — off-topic não polui contexto. |
| RF-TOM-07 | UI (`services/frontend/`): branding **TomatoIA** (título/cabeçalho); remover referência primária a “mqtt-chat” na UX do chat. |

### Texto padrão out-of-scope (rascunho — aprovar na implementação)

> Sou a **TomatoIA**, assistente do seu painel IoT. Só posso ajudar com **seus dispositivos**, telemetria e uso desta plataforma. Para filmes, finanças ou assuntos gerais, use outro serviço.

*(Manter curto; sem chamar LLM para gerar a recusa.)*

---

## Análise Pydantic AI — conversa direta e precisa

### Estado atual (006 6b)

- `Agent` com `output_type=str`, instructions genéricas (“assistente mqtt-chat”).
- **Sempre** `append_turn` após `run_chat` ([`chat.py`](../src/mqtt_chat/api/routes/chat.py)).
- Histórico: últimas N mensagens Firestore → `message_history` ([`chat_history.py`](../src/mqtt_chat/services/chat_history.py)).

### Opções avaliadas

| Abordagem | Prós | Contras | Recomendação |
|-----------|------|---------|--------------|
| **A. Só prompt** (“não fale de Bitcoin…”) | Simples | Modelo ainda responde e persiste; impreciso | **Não** como única camada |
| **B. `output_type` estruturado** (`scope` + `reply`) | **1 chamada** LLM; validação Pydantic; testável com `TestModel` | Precisa pós-processar: se `off_topic`, descartar `reply` do modelo e usar texto fixo | **Preferida (v1)** |
| **C. Agente classificador + agente resposta** | Classificação explícita | 2× latência/custo | Reserva se B falhar métricas |
| **D. Pydantic Graph** (nó classify → branch) | Fluxo claro | Mais boilerplate na PoC | Fase 2 se regras crescerem |
| **E. Filtro regex/heurística** | Barato | Falso positivo/negativo | Complemento opcional, não substituto |

### Decisão proposta (v1) — **DECISÃO**

1. **`output_type=ChatTurnResult`** (schema em `schemas/chat.py`):

   ```python
   scope: Literal["product", "off_topic"]
   reply: str  # usado somente se scope == "product"
   ```

2. **Pós-processamento no `services/`** (não na route):
   - `off_topic` → `reply` = constante RF-TOM-04; `persist=False`.
   - `product` → `reply` do modelo; `persist=True`.

3. **Instructions** (`agent/`): persona **TomatoIA**, escopo fechado, exemplos negativos (Bitcoin, filme), pedir classificação honesta no schema.

4. **Eficiência:**
   - Manter **um** `agent.run` por turno in-scope; off-topic ainda invoca modelo **na v1** (para classificar + eventual nuance) — **otimização v1.1:** classificador mini-model ou heurística pré-LLM para recusas óbvias sem segunda chamada (documentar em follow-up).
   - Continuar `CHAT_MAX_TURNS`; não incluir off-topic no histórico (RF-TOM-06).

5. **Testes:** `Agent('test', output_type=ChatTurnResult)` + casos in/out ([`TESTING-AND-DEBUGGING.md`](../.agents/skills/building-pydantic-ai-agents/references/TESTING-AND-DEBUGGING.md)).

6. **Logging:** evento `chat.turn.off_topic` (sem conteúdo da pergunta sensível se política exigir — ver [`docs/logging.md`](../docs/logging.md); logar `user_id`, `session_id`, contagem).

---

## Entregáveis (checklist)

### Backend

- [x] Glossário: termo **TomatoIA** ([`docs/glossary.md`](../docs/glossary.md))
- [x] Constantes: [`agent/tomato_ia.py`](../src/mqtt_chat/agent/tomato_ia.py)
- [x] Schema `ChatTurnResult` + `ChatResponse.persisted`
- [x] `chat_agent.py`: instructions TomatoIA + `output_type`
- [x] [`services/chat_turn.py`](../src/mqtt_chat/services/chat_turn.py) — `execute_chat_turn` / `finalize_turn`
- [x] `POST /chat` e `/chat/stream`: persistir **somente** se `persist`
- [x] Resposta API: `persisted: bool` (+ tipos TS)
- [x] Testes unitários `finalize_turn` (`tests/test_chat_turn.py`)

### Frontend

- [x] Branding TomatoIA (header, login)
- [x] Off-topic: mensagem assistant normal (HTTP 200 + `persisted: false`)

### Documentação

- [x] [`docs/requirements.md`](../docs/requirements.md) — TomatoIA + escopo
- [ ] Verificação manual (checklist § Verificação) → **Status: Concluída**

---

## Fora de escopo (007)

- Tools MCP / list_devices (006 6c–6d)
- RAG / embeddings
- Moderação de conteúdo ilegal (reportar apenas escopo produto)
- Renomear repositório/pacote PyPI `mqtt-chat` → TomatoIA (só UX + prompts nesta task)

---

## Matriz de versões

| Componente | Versão | Notas |
|------------|--------|--------|
| Python | ≥3.13 | uv lock |
| pydantic-ai | lock atual | `output_type`, `TestModel` |
| Gemini | `CHAT_MODEL` env | ex.: `google:gemini-3.5-flash` |

---

## Verificação

1. Primeiro turno: “Olá, {display_name}…” assinado **TomatoIA** (não “mqtt-chat”).
2. Pergunta in-scope (“O que é um sensor?”) → resposta útil + documentos em Firestore.
3. “Qual o preço do Bitcoin?” / “Indica um filme” → **texto padrão** + **nenhum** novo doc em `messages/`.
4. Turno in-scope seguinte: histórico **não** contém pergunta off-topic anterior.
5. Logs: evento off-topic sem vazar token/API key ([`docs/logging.md`](../docs/logging.md)).

---

## Referências

- [Pydantic AI — overview](https://pydantic.dev/docs/ai/overview/)
- [Structured output](https://pydantic.dev/docs/ai/core-concepts/output/) (Skill `building-pydantic-ai-agents`)
- [`docs/glossary.md`](../docs/glossary.md) — atualizar com TomatoIA
- Skill repo: `.agents/skills/building-pydantic-ai-agents/`
