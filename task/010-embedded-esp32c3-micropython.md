# Task 010 — Firmware MicroPython ESP32-C3 (Seeed XIAO) — adoção MQTT WiFi

> **Status:** Em execução (estrutura + handshake UC-A v0.1)  
> **Fase:** Testes reais pós-backend [008](008-device-adoption-handshake-refinement.md) e chat [009](009-adoption-guided-chat-ux.md)  
> **Contrato:** [`docs/contracts/device-adoption.md`](../docs/contracts/device-adoption.md) UC-A, §4.2.1, §6.5–§6.7  
> **Referência domínio (não copiar serial):** `~/DEV/Tauri/device_app/embedded`

## Objetivo

Firmware **real** em **MicroPython** para **Seeed XIAO ESP32-C3** (ESP32-C3 Super Mini USB-C, RISC-V), conectando via **WiFi** (SSID/senha **fixos no código** na v0.1) ao Mosquitto e executando o **handshake de adoção** igual ao simulador [`scripts/devices/simulate_adoption_device.py`](../scripts/devices/simulate_adoption_device.py).

**Fora do escopo v0.1:** Bluetooth, provisioning WiFi (SoftAP/BLE/serial). **Telemetria simulada** (random em `parameter_ranges`, 5 s) incluída sem DHT11 físico.

## Placa e firmware base

| Item | Valor |
|------|--------|
| Placa | Seeed **XIAO ESP32C3** (Super Mini) |
| Port MicroPython | [SEEED_XIAO_ESP32C3](https://micropython.org/download/SEEED_XIAO_ESP32C3/) |
| MicroPython (pin) | **v1.29.0** (2026-08-24) — `.bin` estável da página oficial |
| Flash / erase | [esptool](https://docs.espressif.com/projects/esptool/en/latest/esp32c3/esptool/basic-options.html) `--chip esp32c3` |
| Quickref | [MicroPython ESP32](https://docs.micropython.org/en/latest/esp32/quickref.html) |

## Decisões

| # | Decisão |
|---|---------|
| D1 | **Adoção só MQTT** — sem protocolo serial USB (diferente do device_app Tauri) |
| D2 | WiFi: credenciais em `embedded/firmware/secrets_wifi.py` (**gitignored**); exemplo em `secrets_wifi.example.py` |
| D3 | Identidade: `mac_address` lida do STA; tópico `unclaimed/devices/{mac_normalized}/…` |
| D4 | Perfil v0.1: **sensor** + `parameter_ranges`; leituras **simuladas** (`sensor_sim.py`) até DHT real |
| D5 | Pós-ack: `device_config.json` + **soft reset** → operação: `…/status` online + `…/telemetry` a cada **5 s** |
| D6 | BLE **não** usado nesta task |

## Entregáveis

### Fase 010a (atual)

- [x] Pasta [`embedded/`](../embedded/) na raiz do repo
- [x] [`embedded/README.md`](../embedded/README.md) + [`embedded/docs/flash-xiao-esp32c3.md`](../embedded/docs/flash-xiao-esp32c3.md)
- [x] Firmware mínimo: WiFi → MQTT → subscribe `challenge`/`config` → publish `info`/`ack`
- [ ] Flash em placa física + E2E: UI/chat adoção com MAC da placa → `committed` → `list_devices`

### Fase 010b (próxima)

- [x] Modo operação: telemetria simulada + `status` online (retain)
- [ ] DHT11 real (GPIO) substituindo `sensor_sim.py`
- [ ] LWT offline em `/status`; unsubscribe `unclaimed/…` explícito (§4.4)
- [ ] (Opcional) factory reset GPIO → `adopted_status = 0`

## Matriz de versões (dev)

| Componente | Versão | Notas |
|------------|--------|--------|
| MicroPython | 1.29.0 | Board ID SEEED_XIAO_ESP32C3 |
| esptool | ≥ 4.x | `pip install esptool` ou `uv tool` |
| Mosquitto | 2.0.21 | `docker compose` task 001 |
| mqtt-chat API | lock atual | `WORKER_PERSIST_MODE=firestore`, worker no lifespan |
| Broker dev | allow_anonymous | §7.3 contrato |

## Verificação E2E (010a)

1. Mosquitto + `uv run mqtt-chat-api` (Firestore + credenciais).
2. Flash MicroPython + copiar `embedded/firmware/*` para a placa (`mpremote` ou ampy).
3. Ajustar `secrets_wifi.py` (rede alcança `MQTT_HOST` do `.env`, em dev geralmente IP LAN do host, **não** `127.0.0.1` na placa).
4. Anotar MAC (log serial ou `mac_address.py`).
5. Chat: intenção adoção → MAC → committed.
6. Chat: *“liste meus dispositivos”* → aparece o device.

## Rede (armadilha comum)

O firmware roda **na placa**. `broker_url` vindo do backend em dev usa `mqtt://127.0.0.1:1883` — **inválido na placa**. Mitigações v0.1:

- Definir `MQTT_BROKER_HOST` em `secrets_wifi.py` com IP LAN do PC (ex.: `192.168.1.x`), **ou**
- Ajustar `MQTT_HOST` no `.env` do backend para IP LAN antes do adopt (mesmo valor alcançável pela placa).

Documentar no README embedded; evolução: backend enviar host alcançável por segmento (fase posterior).

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-13 | Task criada — embedded ESP32-C3 MicroPython, WiFi fixo, UC-A |
