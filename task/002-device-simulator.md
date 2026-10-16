# Task 002 — Simulador de device MQTT

> **Status:** Concluída  
> **Fase:** PoC  
> **Depende de:** [001-docker.md](001-docker.md) (broker Mosquitto)  
> **Referências:** [`docs/glossary.md`](../docs/glossary.md) · [`docs/requirements.md`](../docs/requirements.md) §5

## Objetivo

Fornecer um **device** simulado em Python que publica telemetria e responde a comandos MQTT, usando os mesmos tópicos e payloads da PoC, para testes sem hardware embarcado.

---

## Matriz de versões

| Componente | Versão / pin | Notas |
|------------|--------------|--------|
| **Python** | `>=3.13` (projeto) | Executar com `uv run` |
| **paho-mqtt** | `>=2.1.0` (lock: 2.1.0) | Cliente MQTT; API `CallbackAPIVersion.VERSION2`, protocolo MQTT 3.1.1 |
| **Broker** | `eclipse-mosquitto:2.0.21` | Task 001 — host padrão `127.0.0.1:1883` |
| **Script** | `scripts/devices/simulate_device.py` | Standalone; não é pacote instalável separado |

---

## Entregáveis (checklist)

- [x] Pasta `scripts/devices/`
- [x] Script `simulate_device.py` (sensor + actuator via `--device-type`)
- [x] Dependência `paho-mqtt` no `pyproject.toml` / `uv.lock`
- [x] Documentação de uso no `README.md`
- [x] Alinhamento de tópicos e JSON com glossário / requirements

---

## Comportamento implementado

### Tópicos

| Finalidade | Padrão |
|------------|--------|
| Telemetria | `tenants/{user_id}/devices/{device_id}/telemetry` |
| Comandos (subscribe) | `tenants/{user_id}/devices/{device_id}/commands` |
| Estado / ACK (publish) | `tenants/{user_id}/devices/{device_id}/state` |
| Presença | `tenants/{user_id}/devices/{device_id}/status` (retain, `operation_status: online`) |

### `device_type`: sensor (padrão)

- Publica JSON: `{ "ts", "metric", "value", "unit" }` (default: `humidity`, `%`).
- Umidade simulada com random walk (30–90).
- Intervalo configurável (`--interval`, default 10 s).

### `device_type`: actuator

- Publica estado em `state` (retain): `{ "ts", "channel", "value" }`.
- Em `commands`, aceita `{"action":"set","channel":1,"value":0|1|bool,"command_id":?}` (integer 0/1 normativo MVP).
- Responde ACK em `state` com `status`: `received` / `applied`.

### CLI

| Argumento | Default | Descrição |
|-----------|---------|-----------|
| `--device-type` | `sensor` | `sensor` \| `actuator` |
| `--user-id` | `dev-user` | Segmento do tópico |
| `--device-id` | `sim-1` | Segmento do tópico |
| `--host` | `127.0.0.1` | Broker |
| `--port` | `1883` | Broker |
| `--interval` | `10` | Segundos entre ciclos |
| `--metric` | `humidity` | Métrica (sensor) |
| `--unit` | `%` | Unidade (sensor) |

---

## Verificação

1. `docker compose up -d` (task 001).
2. Sensor:

```bash
uv run python scripts/devices/simulate_device.py --interval 5
```

Em outro terminal:

```bash
docker compose exec mosquitto mosquitto_sub \
  -t 'tenants/dev-user/devices/sim-1/telemetry' -C 1 -W 10
```

3. Actuator:

```bash
uv run python scripts/devices/simulate_device.py \
  --device-type actuator --device-id sim-relay-1 --interval 5
```

```bash
docker compose exec mosquitto mosquitto_pub \
  -t 'tenants/dev-user/devices/sim-relay-1/commands' \
  -m '{"action":"set","channel":1,"value":true,"command_id":"test-1"}'
```

**Verificado:** 2026-10-09 — telemetria sensor OK (`timeout 3` + smoke test).

---

## Fora de escopo

- Integração Firestore / worker backend
- Múltiplos devices no mesmo processo
- TLS, credenciais MQTT por device
- Simulação no `docker-compose` como serviço (opcional futuro)

---

## Próxima task sugerida

| ID | Arquivo | Conteúdo |
|----|---------|----------|
| 003 | [003-adoption-network-contracts.md](003-adoption-network-contracts.md) | Contratos adoção, QR, tópicos, payloads |
| 004 | [004-mqtt-worker.md](004-mqtt-worker.md) | Worker backend: assinar telemetria, persistir Firebase |

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-09 | Task criada; implementação já entregue em `scripts/devices/simulate_device.py` |
