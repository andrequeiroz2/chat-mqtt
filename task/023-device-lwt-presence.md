# Task 023 — LWT MQTT: presença offline real (device + simulador)

## Objetivo

Fechar a lacuna de presença detectada em 2026-10-18: device desligado físicamente
continuava `online` no chat. O contrato ([`docs/contracts/device-adoption.md`](../docs/contracts/device-adoption.md))
exige LWT em `.../status` (payload `offline`, retain, QoS 1), mas nem o firmware
nem o simulador desktop configuram Last Will.

## Contexto

Cadeia de presença: device publica `online` retained ao conectar → worker
(`persist_status` em `services/telemetry.py`) persiste `operation_status` no
documento `devices` → snapshot do chat reflete o valor. Sem LWT, queda abrupta
(queda de energia/WiFi) deixa o retained `online` para sempre. Agravante: LWT
não dispara em desconexão **graciosa** — o `disconnect()` também precisa
publicar `offline` antes de desconectar. Backend/worker já consomem
corretamente; a correção é toda na ponta do device/publisher.

## Matriz de versões

| Componente | Versão |
|---|---|
| MicroPython `umqtt.simple` | `set_last_will(topic, msg, retain, qos)` antes de `connect()`; `keepalive` no construtor |
| paho-mqtt (simulador) | `will_set(topic, payload, qos, retain)` antes de `connect()` |
| Broker | `eclipse-mosquitto:2.0.21` (docker-compose) |

## Entregáveis

| # | Item | Arquivo(s) |
|---|------|-----------|
| 023-01 | **Firmware LWT**: `set_last_will(status_topic, {"ts","operation_status":"offline"}, retain=True, qos=1)` antes de `connect()` + `keepalive=60` no construtor (broker detecta queda em ~1,5× keepalive ≈ 90s) | `embedded/firmware/operation_mqtt.py` |
| 023-02 | **Firmware desligamento gracioso**: publicar `offline` retained antes de `disconnect()` | `embedded/firmware/operation_mqtt.py` |
| 023-03 | **Simulador desktop**: `will_set` equivalente + publicar `offline` ao parar (`wait_for_publish` antes de `loop_stop`/`disconnect`) | `scripts/devices/simulate_device.py` |
| 023-04 | Teste do simulador com client MQTT mockado: will configurado com retain/payload offline; parada publica offline | `tests/` |

## Fora de escopo

- Hardening backend por staleness (`last_seen_at` antigo ⇒ tratar como offline) —
  camada futura caso LWT não seja suficiente (ex.: device sem bateria/rede falsa).
- Reconexão automática do firmware (backoff) — já tratada como domínio no `device_app`.

## Critérios de verificação

- [ ] Device liga → chat responde "online".
- [ ] Device desligado no braço (energia) → `operation_status` vira `offline` no
      Firestore em ~90s (will do broker) e o chat responde "offline".
- [ ] Parada graciosa (simulador Ctrl+C / firmware reset controlado) → `offline` imediato.
- [x] `uv run pytest` verde.

## Checklist

- [x] 023-01 LWT no firmware
- [x] 023-02 offline gracioso no firmware
- [x] 023-03 LWT + offline no simulador
- [x] 023-04 testes
- [x] Atualizar status aqui e no [README](README.md)

## Notas

- Origem: pergunta "qual o status do meu sensor?" com device desligado → resposta
  "online" (retained antigo de 2026-10-19 01:29 UTC).
- Firmware é MicroPython embarcado: verificação dos itens 023-01/02 é manual no
  hardware; simulador cobre o mesmo contrato em CPython (testável).

## Status

- 2026-10-18 — Criada e implementada; verificação manual no hardware pendente.
