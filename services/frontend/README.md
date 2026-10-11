# mqtt-chat — serviço frontend (UI)

Microserviço **React + Vite** do monorepo: chat web, Firebase Auth (Google) e chamadas HTTP ao backend **`mqtt-chat-api`** (`/api/v1/me`, `/api/v1/chat`).

Não compartilha runtime Python nem `src/mqtt_chat/` — apenas contratos HTTP e config Firebase Web.

## Pré-requisitos

- Node.js **24+** recomendado (Firebase SDK; Docker usa `node:24-alpine`)
- Backend em execução: `uv run mqtt-chat-api` (porta padrão **8000**)
- Firebase: Google habilitado; domínios autorizados incluindo `localhost`

## Configuração

```bash
cd services/frontend
cp .env.example .env
# Preencha VITE_FIREBASE_* com o app Web do projeto Firebase
npm install
```

## Desenvolvimento

**Dois processos** (frontend no Docker ou `npm run dev`):

```bash
# Terminal 1 — raiz do monorepo
uv run mqtt-chat-api

# Terminal 2 — este serviço
npm run dev
```

UI: [http://localhost:5173](http://localhost:5173) (CORS do backend já permite origem 5173).

Sem a API, o Google login **não** abre o chat: após OAuth o app chama `GET /api/v1/me`.

## Build

```bash
npm run build
npm run preview
```

## Docker (opcional)

Perfil `ui` no compose da raiz:

```bash
docker compose --profile ui up frontend
```

## Estrutura

| Pasta | Papel |
|-------|--------|
| `src/types/` | Tipos TS: contratos API (espelho `src/mqtt_chat/schemas/`), auth, UI |
| `src/auth/` | Provider Firebase Auth + contexto |
| `src/api/` | Cliente HTTP, type guards na resposta JSON |
| `src/chat/` | UI de chat (composição de componentes) |
| `src/config/` | Leitura tipada de `import.meta.env` (`vite-env.d.ts`) |

Skill de referência (repo): `.agents/skills/vercel-composition-patterns`.
