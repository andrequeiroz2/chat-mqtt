# Serviços (microserviços do monorepo)

Cada pasta em `services/` é um **deployável independente** (runtime, dependências e `.env` próprios). O backend Python permanece na raiz (`src/mqtt_chat/`, `uv`).

| Serviço | Stack | Porta dev | Contrato |
|---------|-------|-----------|----------|
| [`frontend/`](frontend/) | React + Vite + Firebase Auth Web | 5173 | HTTP → API `mqtt-chat-api` (`/api/v1/*`) |

Infra compartilhada: `docker-compose.yml` (broker Mosquitto; perfil `ui` para o frontend).
