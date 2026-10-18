# mqtt-chat — serviço frontend (UI)

Microserviço **React + Vite + Tailwind CSS 4 + shadcn/ui** (tema **dark / zinc**) do monorepo: chat web, Firebase Auth (Google) e chamadas HTTP ao backend **`mqtt-chat-api`** (`/api/v1/me`, `/api/v1/chat`).

Não compartilha runtime Python nem `src/mqtt_chat/` — apenas contratos HTTP e config Firebase Web.

## Pré-requisitos

- Node.js **24+** (Firebase 13 exige `>=24.12`; use `nvm use` em `services/frontend` — arquivo [`.nvmrc`](.nvmrc))
- Backend em execução: `uv run mqtt-chat-api` (porta padrão **8000**)
- Firebase: Google habilitado; domínios autorizados incluindo `localhost`

## Configuração

```bash
cd services/frontend
cp .env.example .env
# Preencha VITE_FIREBASE_* com o app Web do projeto Firebase
npm install
```

Se `npm install` falhar com `EACCES` em `node_modules` (pastas criadas como `root`):

```bash
sudo chown -R "$(whoami)" node_modules
npm install
```

Componentes UI: `src/components/ui/` (shadcn). Alias `@/` → `src/`. Ver [task 013](../../task/013-frontend-tailwind-shadcn-bootstrap.md).

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

## Docker (recomendado para dev UI)

Perfil `ui` na raiz do monorepo — imagem **`node:24-alpine`**, `npm ci` + Vite em `0.0.0.0:5173`:

```bash
# Terminal 1 — raiz (API no host, como hoje)
uv run mqtt-chat-api

# Terminal 2 — raiz
docker compose --profile ui up frontend
```

- **Não** é obrigatório rodar `npm install` no host: `node_modules` fica no volume Docker `frontend_node_modules` (bind mount só do código).
- Após mudar `package.json` / `package-lock.json`, recrie o serviço para rodar `npm ci` de novo:

  ```bash
  docker compose --profile ui up frontend --force-recreate
  ```

- **`.env`:** mantenha `VITE_API_BASE_URL=http://127.0.0.1:8000` — o **navegador no host** chama a API no host; CORS já inclui `http://localhost:5173`.
- Firebase Auth: adicione `localhost` (e domínios OAuth) no console Firebase como já fazia para dev local.

## Estrutura

| Pasta | Papel |
|-------|--------|
| `src/types/` | Tipos TS: contratos API (espelho `src/mqtt_chat/schemas/`), auth, UI |
| `src/auth/` | Provider Firebase Auth + contexto |
| `src/api/` | Cliente HTTP, type guards na resposta JSON |
| `src/chat/` | UI de chat (composição de componentes) |
| `src/config/` | Leitura tipada de `import.meta.env` (`vite-env.d.ts`) |

Skill de referência (repo): `.agents/skills/vercel-composition-patterns`.
