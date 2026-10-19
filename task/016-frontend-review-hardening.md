# Task 016 — Revisão frontend: hardening, tokens e componentização

> **Status:** Concluída (itens 016-01 a 016-10 implementados; build e lint OK)  
> **Origem:** Revisão de código (2026-10-18) — chat [`ChatScreen`](../services/frontend/src/chat/ChatScreen.tsx), wizard adoção, realtime, banner API, `TelemetryChart`  
> **Depende de:** [013](013-frontend-tailwind-shadcn-bootstrap.md), [014](014-telemetry-chart-recharts.md)  
> **Skills:** [`vercel-composition-patterns`](../.agents/skills/vercel-composition-patterns/SKILL.md) (variantes, compound, React 19), [`clean-code`](../.agents/skills/clean-code/SKILL.md)  
> **Escopo:** **somente** frontend em [`services/frontend/`](../services/frontend/). **NÃO** alterar contratos HTTP/WebSocket, campos JSON, glossário, [`docs/contracts/`](../docs/contracts/) ou regras do projeto. **NÃO** alterar lógica de negócio no backend.

## Objetivo

Corrigir fragilidades de UX/estado, alinhar cores ao tema zinc (013), melhorar resiliência de rede e polling, e preparar componentização do thread para evoluções futuras (015 drawer, streaming) — sem quebrar comportamento observável já validado (012–014).

## Fora de escopo

- Mudar payloads da API, `suggested_ui`, nomes de tools MCP, textos contratuais em PT exigidos por contrato.
- Implementar 015 (drawer) ou streaming SSE token a token (task futura).
- Mudar bibliotecas (Recharts, Tailwind, shadcn já adotadas na 012).

## Entregáveis (checklist)

### Estado e wizard (alto)

- [x] **016-01** Reset explícito do estado interno de [`AdoptWizardPanel`](../services/frontend/src/chat/adopt/AdoptWizardPanel.tsx) ao sair da fase `adopting` / fechar wizard (ou `key` por tentativa de adoção) — evita MAC/sessão “fantasma” em segundo ciclo de adoção.

### Tema zinc / design (alto)

- [x] **016-02** Substituir cores fixas amber em [`ApiStatusBanner`](../services/frontend/src/app/ApiStatusBanner.tsx) por tokens do tema (`border-border`, `bg-destructive/10`, `text-destructive` ou variante equivalente), mantendo copy atual em português.
- [x] **016-03** Alinhar indicador “conectado” em [`LiveTelemetryChatBubble`](../services/frontend/src/realtime/LiveTelemetryChatBubble.tsx) ao tema (verde explícito como semântico de sucesso documentado no CSS **ou** tokens neutros) — evitar improviso visual.

### Resiliência (alto)

- [x] **016-04** [`useAdoptionPoll`](../services/frontend/src/chat/adopt/useAdoptionPoll.ts): em falha de rede/API, continuar polling mas expor estado visível no wizard (ex.: “Sem conexão — tentando novamente…”), sem expor detalhes técnicos ao usuário.
- [x] **016-05** [`realtimeConnectionManager`](../services/frontend/src/realtime/manager.ts): reconnect com backoff em `onclose` inesperado; reabrir com token fresco via `getAccessToken` (respeitar `refCount`, `deviceKey`, 4409 `device_not_online_for_realtime`).

### UX / chat thread (médio)

- [x] **016-06** Auto-scroll em [`ChatScreen`](../services/frontend/src/chat/ChatScreen.tsx): só rolar quando usuário estiver perto do fim (threshold) ou quando a última mensagem for nova — reduz briga com scroll manual e prepara RF-UX-STREAM-05.

### Componentização / skills (médio)

- [x] **016-07** [`ChatMessageItem`](../services/frontend/src/chat/ChatMessageItem.tsx): extrair variantes nomeadas por papel (`TextMessage`, `LiveTelemetryMessage`, `TelemetryChartMessage`, `PostAdoptionMessage`) mantendo dispatcher fino — alinha a `patterns-explicit-variants` sem mudar tipos/contratos.

### Clean code (baixo)

- [x] **016-08** [`intent.ts`](../services/frontend/src/chat/adopt/intent.ts): remover duplicação dos dois ramos de `isAdoptionIntent` (mesmo retorno booleano), sem mudar regex nem comportamento.

### Polish (baixo / opcional)

- [x] **016-09** [`TelemetryChart`](../services/frontend/src/charts/TelemetryChart.tsx): documentar que valores `oklch()` espelham tokens zinc em [`index.css`](../services/frontend/src/index.css) (comentário curto) ou centralizar constantes — evita drift silencioso.
- [x] **016-10** [`AssistantMessageText`](../services/frontend/src/chat/AssistantMessageText.tsx): chaves React mais estáveis que `key={index}` quando o texto muda.

## Matriz de versões

| Item | Versão |
|------|--------|
| Node | 24 (`.nvmrc`; Docker `profile ui`) |
| React | ^19.2 |
| Tailwind CSS | ^4.1.x |
| Recharts | ^3.10.x |

## Verificação

1. `docker compose --profile ui up frontend` ou `npm run dev` no container: build sem erros TS.
2. Dois ciclos de wizard de adoção (abrir → fechar → abrir): formulário limpo, sem sessão anterior.
3. Backend parado: banner com tokens zinc; wizard em `adopting` mostra mensagem de reconexão amigável se aplicável (016-04).
4. Bolha ao vivo: reconexão após queda simulada do WS (dev tools / backend restart) sem duplicar conexões.
5. Chat com mensagens longas: auto-scroll não “rouba” posição quando usuário lê histórico (016-06).

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-18 | Task criada após revisão de código (foco: design, estrutura, resiliência, componentização) |
| 2026-10-18 | Implementados 016-01 … 016-10; build e lint OK; task concluída |
