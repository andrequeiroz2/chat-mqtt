# Papel do firmware (embedded)

## Escopo mqtt-chat

- **DEVE** implementar adoção **UC-A**: `unclaimed/devices/{mac_normalized}/challenge|info|config|ack`.
- **DEVE** usar campos JSON em **inglês** alinhados a [`docs/contracts/device-adoption.md`](../docs/contracts/device-adoption.md) e [`docs/glossary.md`](../docs/glossary.md) (`device_type`, `mac_address`, …).
- **DEVE** conectar ao broker via **WiFi** antes do handshake (provisionamento WiFi = responsabilidade deste firmware; backend **não** envia SSID/senha na v0).
- **NÃO DEVE** usar serial USB para adoção neste produto (legado device_app).
- **NÃO DEVE** persistir telemetria no backend fora do contrato MQTT → worker → Firestore.

## Modos

| Modo | Condição | Comportamento |
|------|----------|----------------|
| Adoção | `adopted_status == 0` | MQTT em `unclaimed/…`; responde challenge/config |
| Operação | `adopted_status == 1` | Somente `tenants/{user_id}/devices/{device_id}/…` (fase 010b) |

## Referência

Estrutura modular inspirada em `device_app/embedded` (WiFi, MQTT, perfil sensor), adaptada ao contrato mqtt-chat v1.2-dev.
