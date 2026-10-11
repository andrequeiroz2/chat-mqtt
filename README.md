# mqtt-chat

Plataforma web: dispositivos IoT via MQTT (Mosquitto), Firebase, chat com Pydantic AI e tools FastMCP.

Documentação: [`docs/requirements.md`](docs/requirements.md) · Glossário: [`docs/glossary.md`](docs/glossary.md) · Skills: [`docs/skills.md`](docs/skills.md)

## Ambiente (uv)

Requisito: [uv](https://docs.astral.sh/uv/) instalado. Python **3.13+** (ver `.python-version`).

```bash
uv sync
uv run mqtt-chat
```

Desenvolvimento:

```bash
uv run python -m mqtt_chat
uv add <pacote>
```

## Docker (broker MQTT)

Task: [`task/001-docker.md`](task/001-docker.md)

| Componente | Versão |
|------------|--------|
| Imagem | `eclipse-mosquitto:2.0.21` |
| Docker Engine | 24.0+ (dev: 29.x) |
| Docker Compose | plugin v2 (`docker compose`) |

**Atenção:** `allow_anonymous true` na PoC é **somente para dev local**. Não use esta configuração exposta na internet.

```bash
cp .env.example .env   # opcional
docker compose up -d
docker compose ps
```

Teste publish/subscribe (tópico de exemplo):

```bash
docker compose exec mosquitto sh -c \
  'mosquitto_sub -t "tenants/dev-user/devices/sim-1/telemetry" -C 1 -W 5 & sleep 1; \
   mosquitto_pub -t "tenants/dev-user/devices/sim-1/telemetry" -m "{\"metric\":\"humidity\",\"value\":42}"; wait'
```

Parar:

```bash
docker compose down
# docker compose down -v   # remove volumes nomeados
```

## Simulador de device (PoC)

Script: [`scripts/devices/simulate_device.py`](scripts/devices/simulate_device.py)

Requer broker Mosquitto em execução (`docker compose up -d`).

```bash
# Sensor (umidade simulada a cada 10 s)
uv run python scripts/devices/simulate_device.py

# Atuador (relé simulado)
uv run python scripts/devices/simulate_device.py --device-type actuator --device-id sim-relay-1

# Publicar comando para actuator (outro terminal)
docker compose exec mosquitto mosquitto_pub \
  -t 'tenants/dev-user/devices/sim-relay-1/commands' \
  -m '{"action":"set","channel":1,"value":true,"command_id":"test-1"}'
```

Opções úteis: `--user-id`, `--device-id`, `--host`, `--port`, `--interval`, `--metric`, `--unit`.

## Worker MQTT (task 004)

Ingestão com reconexão automática (ref. collector `device_app`). Persistência PoC: **`WORKER_PERSIST_MODE=log`** (padrão); com Firebase, use `firestore` + `FIREBASE_PROJECT_ID`.

Variáveis: [`.env.example`](.env.example) (`MQTT_HOST`, `MQTT_PORT`, `WORKER_PERSIST_MODE`, …).

Com broker e simulador rodando:

```bash
# Só worker (logs de telemetria)
uv run python -m mqtt_chat.worker
# ou
uv run mqtt-chat-worker

# API + worker no lifespan + GET /health
uv run mqtt-chat-api
# ou
uv run mqtt-chat
```

Health:

```bash
curl -s http://127.0.0.1:8000/health | jq
```

Firestore: `WORKER_PERSIST_MODE=firestore`, `FIREBASE_PROJECT_ID` e JSON em `secrets/service-account.json` (ver `.env.example` → `GOOGLE_APPLICATION_CREDENTIALS`). Telemetria em `devices/{device_id}/telemetry`.

## Logging estruturado (task 005)

JSON em stdout, taxonomia de eventos (`mqtt.*`, `telemetry.*`), redação de secrets. Guia completo: [`docs/logging.md`](docs/logging.md).
