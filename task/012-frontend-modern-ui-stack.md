# Task 012 — Stack de UI moderna do frontend (discussão de bibliotecas)

> **Status:** Em execução (E1 — Tailwind, Recharts, **shadcn** + tokens dark; CopilotKit rejeitado)  
> **Fase:** Pós-v1 funcional do chat ([006](006-user-auth-chat-mcp.md), [009](009-adoption-guided-chat-ux.md), [011](011-chat-session-context-policy.md)); referência visual [shadcn/ui](https://ui.shadcn.com/)  
> **Depende de:** monorepo [`services/frontend/`](../services/frontend/) (React 19 + Vite); contratos HTTP/WebSocket existentes  
> **Referências de produto:** [`docs/requirements.md`](../docs/requirements.md) § gráficos (Recharts); [`docs/contracts/chat-session-context.md`](../docs/contracts/chat-session-context.md)

## Objetivo

Definir **quais bibliotecas e padrões** adotamos para evoluir o chat TomatoIA de uma UI mínima (CSS custom + componentes locais) para um **visual moderno**, mantendo:

- Backend **Pydantic AI + FastAPI** (sem LangChain; sem LLM direto em Firestore/MQTT).
- Frontend **somente HTTP** (`/api/v1/*`) + realtime já contratado ([`realtime-websocket.md`](../docs/contracts/realtime-websocket.md)).
- Nomenclatura e UX copy em **português**; identificadores em **inglês** ([`glossary.md`](../docs/glossary.md)).
- Padrões React 19 e composição ([`vercel-composition-patterns`](../.agents/skills/vercel-composition-patterns/SKILL.md)) — evitar props booleanas no `ChatScreen`.

**Esta task não implementa UI.** Produz decisões registradas (ADRs curtos neste arquivo ou em `docs/`) e um backlog de follow-ups (ex.: task 013 design tokens, 014 migração shadcn).

---

## Estado atual (baseline)

| Item | Situação |
|------|----------|
| Runtime | React **19.2**, Vite **8**, TypeScript **6**, oxlint |
| Estilo | [`index.css`](../services/frontend/src/index.css) global hoje; **Tailwind CSS 4.x** adotado na task (bootstrap na [013](#ordem-sugerida-pós-decisão)) |
| Chat | [`ChatScreen.tsx`](../services/frontend/src/chat/ChatScreen.tsx) — mensagens locais + widgets adoção / telemetria ao vivo |
| Sessão | `session_id` em `sessionStorage` ([`session.ts`](../services/frontend/src/chat/session.ts)); persistência de turnos e `conversation_context` no **Firestore via backend** |
| Auth | Firebase Auth Web (Bearer para API) |

---

## Decisão E1 (2026-10-16)

| Biblioteca | Decisão | Notas |
|------------|---------|-------|
| **Tailwind CSS** | **Adotar** | Versão alvo **4.x** + integração Vite (`@tailwindcss/vite`); migrar estilos gradualmente a partir de [`index.css`](../services/frontend/src/index.css). |
| **Recharts** | **Adotar** | ^3.10.x; gráficos no chat via payload estruturado (`suggested_ui` / contrato — task **014**). Lazy-load por bolha. |
| **shadcn/ui** | **Adotar** | Base do design system; bootstrap CLI na task **013**. Ver § [Direção visual](#direção-visual-2026-10-17). |
| **CopilotKit** | **Rejeitar** (MVP) | **Cenário D:** shell e drawer **custom** (Tailwind + componentes locais ou shadcn depois); sessões **Firestore** via backend; sem Copilot Runtime / Intelligence. |

**Justificativa CopilotKit (cenário D):** mantém **Pydantic AI** no FastAPI, evita duplicar `chat_sessions` na nuvem CopilotKit e preserva widgets atuais (`adopt`, `live_telemetry`). Referência visual do [Threads Drawer](https://docs.copilotkit.ai/claude-sdk-typescript/prebuilt-components/copilot-threads-drawer) apenas como inspiração UX para task **015**.

---

## Direção visual (2026-10-17)

**Referência de produto:** site oficial [shadcn/ui](https://ui.shadcn.com/) — fundo **escuro** e superfícies de UI em **cinza claro** (cartões, inputs, painéis “elevados” sobre o background).

| Decisão | Escolha | Significado na UI |
|---------|---------|-------------------|
| **Referência** | shadcn.com (marketing / blocks) | Tom neutro, contraste suave, aparência “app moderno” — não copiar layout do site literalmente; adaptar ao chat TomatoIA. |
| **Tema padrão** | **Dark first** | `<html class="dark">` (ou equivalente) no MVP; light mode **opcional** depois (toggle Appearance). |
| **Paleta base (CLI shadcn)** | **`zinc`** | Cinzas neutros alinhados ao site; evita hue colorido no chrome (primary continua para CTAs). |
| **Variante de componente** | **`new-york`** | Densidade e bordas próximas aos blocks atuais do ecossistema shadcn (sidebar, chat blocks). |
| **Superfícies** | Background escuro + **card/muted** mais claro | `--background` ≈ fundo da página; `--card`, `--muted`, `--secondary` ≈ bolhas, wizard adoção, composer, drawer futuro. |
| **Primary (CTA)** | **Zinc neutro** (shadcn default dark) | Sem azul PoC; CTAs e chrome em **secondary** / **primary** zinc (cinza claro sobre fundo escuro). |

### Mapeamento tokens → chat (implementação 013)

| Token shadcn | Uso TomatoIA (proposta) |
|--------------|-------------------------|
| `background` | Shell do app, área atrás do thread |
| `card` | Painéis (adoção, telemetria ao vivo, gráfico Recharts embutido) |
| `muted` | Bolhas assistant / mensagens de sistema; fundo sutil da lista |
| `border` | Separadores, moldura do composer |
| `secondary` / `card` | Bolha usuário, Enviar, adoção, chips — tons de cinza |
| `foreground` / `muted-foreground` | Texto principal e secundário (PT) |

**Recharts (014):** eixos, grid e tooltip usam `muted-foreground`, `border` e `card` — gráfico “dentro” do mesmo card cinza claro, não fundo branco solto.

**Fora de escopo desta decisão:** logo TomatoIA, ilustrações, tipografia custom (usar stack shadcn até Figma).

---

## Candidatos principais (proposta do time)

### 1. [shadcn/ui](https://ui.shadcn.com/)

**Papel desejado:** base do design system — botões, inputs, dialogs, sheets, sidebar, tipografia, tema claro/escuro.

| Prós | Contras / perguntas |
|------|---------------------|
| Componentes copiados para o repo (controle total, alinhado a PoC) | Exige **Tailwind CSS** (+ provável `tailwindcss-animate`, `class-variance-authority`, Radix) — aumento do toolchain Vite |
| Acessibilidade via Radix; combina com React 19 | Decidir **variante** (default vs New York) e estratégia de tokens (CSS variables vs `@theme`) |
| Ecossistema maduro (blocks de chat/dashboard reutilizáveis como referência) | Tempo de migração dos widgets atuais (adoção, composer, bolhas) |

**Decisões a fechar:** Tailwind v4 vs v3; pasta `components/ui/`; integração com Firebase sem conflito de estilos; lint/format (Prettier plugin Tailwind?).

---

### 2. [Recharts](https://recharts.github.io/)

**Papel desejado:** gráficos de telemetria **dentro do chat** (já previsto em [`requirements.md`](../docs/requirements.md): tool → payload estruturado → componente React).

| Prós | Contras / perguntas |
|------|---------------------|
| Composable, React-first; citado oficialmente no requisito de produto | Bundle size; lazy-load por mensagem `kind: chart` |
| Encaixa em “generative UI” **nosso** (Pydantic valida série/título/eixos) | Contrato JSON backend ↔ frontend ainda a especificar (task filha ou extensão MCP) |
| Versão estável **3.x** (ver matriz abaixo) | Tema consistente com shadcn (cores de grid, tooltip, dark mode) |

**Decisões a fechar:** formato do payload (`suggested_ui.kind === 'telemetry_chart'`?); interação (zoom, intervalo); acessibilidade (tabela alternativa?).

---

### 3. [CopilotKit — Threads Drawer / v2 chat](https://docs.copilotkit.ai/claude-sdk-typescript/prebuilt-components/copilot-threads-drawer)

**Papel desejado (hipótese):** sidebar de **threads** (listar, trocar, arquivar, nova conversa) + possivelmente shell de chat pré-montado (`CopilotChat`, `CopilotSidebar`).

| Prós | Contras / perguntas **críticas para mqtt-chat** |
|------|--------------------------------------------------|
| UI pronta e moderna; drawer mobile/desktop | Runtime CopilotKit (`CopilotKitProvider`, `runtimeUrl`) — **não** é o stack atual (agente **Pydantic AI** no FastAPI) |
| Threads persistentes via **CopilotKit Intelligence** (cloud) | Sessões já modeladas em Firestore (`chat_sessions`) — **duplicidade ou substituição?** |
| `useThreads` headless se quisermos só o data layer | Licença / `CPK_INTELLIGENCE_API_KEY` vs self-hosted token — custo e dependência vendor |
| Documentação Claude Agent SDK TS — verificar overlap com nosso backend Python | Adoção guiada, `suggested_ui`, WebSocket telemetria — **compatibilidade** com widgets custom |

**Cenários a comparar (obrigatório antes de adopt):**

| Cenário | Descrição |
|---------|-----------|
| **A — Inspiração only** | UX/layout do drawer reimplementado com shadcn + API nossa (`GET /chat/sessions`, etc.) |
| **B — Headless CopilotKit** | `useThreads` + runtime bridge mínimo (alto esforço de integração com Pydantic AI) |
| **C — CopilotKit full stack** | Migrar orquestração para Copilot Runtime — **conflito** com regra de projeto (Pydantic AI imperativo) salvo exceção explícita em `requirements.md` |
| **D — Híbrido** | shadcn + Recharts no chat atual; lista de sessões **Firestore** nativa; CopilotKit **fora de escopo** |

**Recomendação inicial para discussão:** tratar CopilotKit como **opcional** até mapearmos API de sessões multi-thread no backend; favorecer **Cenário A ou D** salvo decisão de produto de pagar Intelligence e unificar runtime.

---

## Outras bibliotecas (mesa de apoio — não decididas)

| Área | Opções | Notas |
|------|--------|-------|
| Estilo utilitário | Tailwind CSS (quase obrigatório com shadcn) | — |
| Ícones | `lucide-react` (padrão shadcn) | — |
| Fetch/cache | TanStack Query vs hooks atuais | Sessões, devices, adopt polling |
| Animações | `motion` / CSS only | Estados **thinking** (três pontos) + **streaming** — [`docs/contracts/chat-streaming-ux.md`](../docs/contracts/chat-streaming-ux.md); componentes [AI Elements](https://ui.shadcn.com/docs/ai-elements) (`Loader`, `Conversation`) |
| QR adoção (009b) | `html5-qrcode` ou BarcodeDetector | Independente desta task, mas layout dentro de shadcn Dialog/Sheet |
| Formulários | react-hook-form + zod | Adopt wizard, settings futuros |

---

## Matriz de versões (alvo — confirmar no lockfile ao implementar)

| Pacote / runtime | Versão referência (2026-10) | Onde fixar |
|------------------|----------------------------|------------|
| Node.js | LTS alinhado ao CI (documentar) | task filha / `.nvmrc` se existir |
| React / React DOM | ^19.2.x (já no projeto) | `services/frontend/package.json` |
| Vite | ^8.x | idem |
| Tailwind CSS | **4.x** (adotado) | `services/frontend` — task 013 |
| shadcn/ui CLI | **new-york** + **zinc** + css variables | `components.json` (task 013) |
| Recharts | **^3.10.x** (adotado) | task 014 |
| CopilotKit (`@copilotkit/react-core/v2`) | — | **Rejeitado** MVP (cenário D) |
| Firebase JS SDK | ^13.x (já no projeto) | idem |

---

## Critérios de decisão (checklist)

Marcar **Sim/Não/Parcial** por biblioteca antes de fechar a task:

1. **Alinhamento arquitetural** — respeita Pydantic AI + FastAPI + Firestore como source of truth?
2. **Multi-sessão** — suporta várias `chat_sessions` por user sem vendor lock-in indesejado?
3. **Generative UI** — permite bolhas custom (`adopt_widget`, `live_telemetry`, `telemetry_chart`) sem lutar contra o shell?
4. **Auth** — funciona com Firebase Bearer existente (sem `user_id` no body)?
5. **Tema / a11y** — dark mode, teclado, contraste AA?
6. **Operação** — build Vite, tamanho de bundle, sem secrets no frontend?
7. **Custo / ops** — dependência SaaS aceitável para PoC/MVP?
8. **Velocidade** — tempo até “chat bonito” vs manutenção longa?

---

## Entregáveis desta task (discussão)

| # | Entregável |
|---|------------|
| E1 | Tabela de decisão final — **✅** (Tailwind, Recharts, shadcn; CopilotKit rejeitado) |
| E2 | Cenário escolhido para **lista de conversas** — **Firestore + drawer custom** (derivado de CopilotKit cenário D); detalhes MVP na task 015 |
| E3 | Esboço de estrutura de pastas frontend pós-decisão — ver § E3 abaixo |
| E4 | Lista de contratos/API faltantes (ex.: listar/arquivar `chat_sessions` se drawer custom) |
| E5 | Atualizar [`requirements.md`](../docs/requirements.md) — **✅** stack frontend (Tailwind + Recharts) |

### E3 — Estrutura de pastas (alvo pós-013)

```
services/frontend/src/
├── app/                    # shell, rotas, providers auth
├── components/
│   └── ui/                 # shadcn (quando adotado) ou primitivos Tailwind
├── chat/                   # thread, composer, widgets (adopt, telemetry, chart)
├── charts/                 # TelemetryChart (Recharts), temas alinhados ao app
├── api/                    # client HTTP (existente)
├── index.css               # @import "tailwindcss"; tokens CSS; overrides mínimos
└── lib/                    # cn(), utils (ex.: tailwind-merge)
```

---

## Fora de escopo (012)

- Implementar instalação shadcn / CopilotKit / Recharts.
- Design visual final (cores, marca TomatoIA, Figma).
- Mudar agente de Pydantic AI para Copilot Runtime **sem** ADR em `requirements.md`.
- Substituir Firebase Auth ou contratos MQTT/Firestore.

---

## Ordem sugerida pós-decisão

1. **012** — fechar E1–E5 (esta discussão).
2. **013** (futura) — bootstrap **Tailwind 4** + **shadcn** + **AI Elements** (`Loader`, chat shell); UX streaming § [`chat-streaming-ux.md`](../docs/contracts/chat-streaming-ux.md); migrar `ChatScreen`.
3. **014** (futura) — instalar **Recharts** + contrato + componente + tool backend.
4. **015** (futura) — drawer de sessões (custom ou CopilotKit) + APIs Firestore.

Paralelo permitido: 009b QR câmera pode usar componentes shadcn assim que 013 existir.

---

## Verificação (da task de discussão)

1. Documento lido e comentado pelo time; nenhum item “Adotar” sem owner.
2. Cenário CopilotKit (A–D) escolhido explicitamente com justificativa — **✅ cenário D**.
3. `task/README.md` atualizado com status **Concluída** quando E1–E5 estiverem no repositório.
4. Riscos registrados (vendor lock-in, bundle, duplicidade de sessão) com mitigação ou aceite.

---

## Perguntas abertas para a reunião / async

1. Precisamos de **múltiplas conversas** no MVP ou uma sessão ativa por aba (como hoje) basta até fase 2?
2. O drawer deve **arquivar/apagar** threads ou só listar/trocar?
3. Streaming de resposta do assistant: SSE/WebSocket já existente — o shell CopilotKit traria ganho real?
4. Gráficos: só histórico semanal ou também sparklines na bolha de telemetria ao vivo?
5. Mobile-first: drawer off-canvas é requisito hard?

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-16 | Task criada — discussão stack UI moderna (shadcn, Recharts, CopilotKit) |
| 2026-10-16 | Decisão: **Adotar** Tailwind CSS 4.x + Recharts; CopilotKit rejeitado MVP (cenário D); shadcn adiado |
| 2026-10-17 | Direção visual: referência [shadcn.com](https://ui.shadcn.com/) — dark first, superfícies cinza (`zinc`), variante **new-york**; shadcn **adotado** |
| 2026-10-17 | Contrato UX thinking/streaming — [`docs/contracts/chat-streaming-ux.md`](../docs/contracts/chat-streaming-ux.md) |
| 2026-10-17 | Tokens: removido primary azul PoC; UI 100% paleta **zinc** (bolhas + CTAs) |
