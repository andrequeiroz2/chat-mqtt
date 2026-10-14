# Copie para secrets_wifi.py (não versionado) e preencha.

# Rede WiFi (fixo v0.1 — provisioning futuro)
WIFI_SSID = "SUA_REDE"
WIFI_PASSWORD = "SUA_SENHA"

# Broker MQTT alcançável **pela placa** (IP LAN do PC/servidor com Mosquitto).
# O backend dev pode enviar mqtt://127.0.0.1:1883 no config — o firmware substitui por este host.
MQTT_BROKER_HOST = "192.168.1.100"
MQTT_BROKER_PORT = 1883

# Opcional — Mosquitto dev allow_anonymous (contrato §7.3)
MQTT_USERNAME = None
MQTT_PASSWORD = None
