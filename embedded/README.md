# embedded — firmware MicroPython (mqtt-chat)

Firmware para dispositivos **sensor/atuador** adotados pela plataforma TomatoIA. Comunicação com a plataforma: **somente MQTT** ([contrato UC-A](../docs/contracts/device-adoption.md)).

## Placa alvo (v0.1)

**Seeed XIAO ESP32C3** (Super Mini, USB-C, RISC-V). Bluetooth não é usado nesta versão.

| Recurso | Link |
|---------|------|
| Firmware MicroPython | [micropython.org/download/SEEED_XIAO_ESP32C3](https://micropython.org/download/SEEED_XIAO_ESP32C3/) |
| Gravação | [esptool ESP32-C3](https://docs.espressif.com/projects/esptool/en/latest/esp32c3/esptool/basic-options.html) |
| API MicroPython | [ESP32 quickref](https://docs.micropython.org/en/latest/esp32/quickref.html) |

Referência de **domínio** (metadados, sensores): `~/DEV/Tauri/device_app/embedded` — **não** copiar fluxo serial; aqui a adoção é **WiFi + MQTT**.

## Layout

```
embedded/
  docs/flash-xiao-esp32c3.md   # apagar/gravar firmware
  firmware/                    # arquivos copiados para a raiz do filesystem da placa
    boot.py
    main.py
    secrets_wifi.example.py    # copiar → secrets_wifi.py (gitignored)
    wifi_sta.py
    mac_address.py
    device_profile.py
    runtime_config.py
    adoption_mqtt.py
    operation_mqtt.py
    sensor_sim.py
    time_util.py
```

## Configuração rápida

1. Flash MicroPython (ver `docs/flash-xiao-esp32c3.md`).
2. `cp firmware/secrets_wifi.example.py firmware/secrets_wifi.py` e preencher **WIFI_SSID**, **WIFI_PASSWORD**, **MQTT_BROKER_HOST** (IP LAN do host com Mosquitto — **não** use `127.0.0.1` na placa).
3. Instalar **mpremote** (esptool não copia `.py` — só o `.bin`):

```bash
uv tool install mpremote
# ou: pipx install mpremote
# Garanta ~/.local/bin no PATH
```

4. Enviar arquivos de `firmware/` para a placa (fique **nesta pasta**, não em `micropython/`):

```bash
cd embedded/firmware
mpremote connect /dev/ttyACM0 fs cp boot.py :
mpremote connect /dev/ttyACM0 fs cp main.py :
mpremote connect /dev/ttyACM0 fs cp adoption_mqtt.py :
mpremote connect /dev/ttyACM0 fs cp operation_mqtt.py :
mpremote connect /dev/ttyACM0 fs cp device_profile.py :
mpremote connect /dev/ttyACM0 fs cp mac_address.py :
mpremote connect /dev/ttyACM0 fs cp wifi_sta.py :
mpremote connect /dev/ttyACM0 fs cp runtime_config.py :
mpremote connect /dev/ttyACM0 fs cp sensor_sim.py :
mpremote connect /dev/ttyACM0 fs cp time_util.py :
mpremote connect /dev/ttyACM0 fs cp secrets_wifi.py :
mpremote connect /dev/ttyACM0 reset
```

(`*.py` na raiz de `firmware/` também funciona; **não** inclui subpastas.)

4. Console: `mpremote connect /dev/ttyACM0 repl` — anote o **MAC** impresso no boot.
5. Na UI mqtt-chat, adoção com esse MAC (mesma rede WiFi que alcança o broker).

## QR code de adoção (QR-A dev)

O chat aceita **MAC em texto** ou JSON `{"v":1,"mac":"AA:BB:..."}` ([`parseMacInput.ts`](../services/frontend/src/chat/adopt/parseMacInput.ts)).

1. MAC da placa: log serial `main: MAC …` ou:

```bash
mpremote connect /dev/ttyACM0 exec "import network; w=network.WLAN(network.STA_IF); w.active(True); print(':'.join('%02X'%b for b in w.config('mac')))"
```

2. Gerar PNG:

```bash
uv run --with 'qrcode[pil]' python embedded/scripts/generate_adoption_qr.py \
  --mac 80:F1:B2:50:AC:88 \
  -o embedded/out/adoption-qr.png
```

Escaneie/cole no wizard de adoção do chat (009a).

## Task de planejamento

[`task/010-embedded-esp32c3-micropython.md`](../task/010-embedded-esp32c3-micropython.md)
