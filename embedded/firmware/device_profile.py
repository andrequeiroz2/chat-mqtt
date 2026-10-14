# Perfil de fábrica do device (contrato §6.5 — sensor v0.1)

MODEL = "SEEED_XIAO_ESP32C3"
DEVICE_TYPE = "sensor"
SENSOR_TYPE = "DHT11"
ACTUATOR_TYPE = None
FIRMWARE_VERSION = "0.1.0-mqtt-chat"

# Intervalo entre publicações de telemetria simulada (sem DHT11 físico)
TELEMETRY_INTERVAL_MS = 5000

PARAMETER_RANGES = {
    "temperature": {"unit": "C", "min_reading": 0, "max_reading": 50},
    "humidity": {"unit": "%", "min_reading": 0, "max_reading": 100},
}

COMMAND_SPEC = None
