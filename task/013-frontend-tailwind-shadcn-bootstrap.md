# Task 013 — Bootstrap Tailwind 4 + shadcn (dark / zinc)

> **Status:** Concluída (MVP shell dark/zinc; composer Enter; thinking dots)  
> **Depende de:** [012](012-frontend-modern-ui-stack.md)  
> **Contratos:** [`chat-streaming-ux.md`](../docs/contracts/chat-streaming-ux.md)

## Objetivo

Integrar **Tailwind CSS 4** + **shadcn/ui** (`new-york`, base **zinc**, **dark first**) em [`services/frontend/`](../services/frontend/) e migrar shell do chat + auth + adoção para tokens (`background`, `card`, `primary`).

## Matriz de versões

| Pacote | Versão alvo |
|--------|-------------|
| tailwindcss | ^4.1.x |
| @tailwindcss/vite | ^4.1.x |
| class-variance-authority, clsx, tailwind-merge | latest |
| @radix-ui/react-slot | ^1.x |
| lucide-react | ^0.x |

## Entregáveis

- [x] Vite + `@/` alias + `@tailwindcss/vite`
- [x] `components.json`, `src/lib/utils.ts`, `Button`, `Textarea`, `Input`, `Card`
- [x] Tema dark zinc + primary azul PoC em `index.css`
- [x] `ChatScreen`, bolhas, auth, banner API, wizard adoção
- [ ] AI Elements `Loader` (opcional — dots custom já validados)
- [x] `npm install` + `npm run build` (após `chown` em `node_modules`)

## Instalação (dev)

**Container (padrão recomendado):** na raiz, `docker compose --profile ui up frontend` — Node 24 Alpine, `node_modules` no volume `frontend_node_modules` (ver [`docker-compose.yml`](../docker-compose.yml)).

**Host (opcional):** `nvm use` (`.nvmrc` = 24) + `npm ci`. Se `EACCES` em `node_modules` misturado com Docker:

```bash
sudo chown -R "$(whoami)" services/frontend/node_modules
# ou remova node_modules no host e use só o container
```

## Verificação

1. `npm run build` — sem erros TS.
2. `npm run dev` — fundo escuro, bolhas `card`, botão primary azul, thinking dots visíveis.
3. Login + turno chat + wizard adoção legíveis no dark.

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-17 | Task criada; bootstrap implementado |
