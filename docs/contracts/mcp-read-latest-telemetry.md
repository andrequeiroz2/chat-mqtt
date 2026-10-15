# Contrato MCP — `read_latest_telemetry` (v1)

> **Status:** Aprovado para implementação (006 — fatia telemetria)  
> **Normativo com:** [`docs/glossary.md`](../glossary.md), [`mcp-list-devices.md`](mcp-list-devices.md)  
> **Fonte de dados:** Firestore `devices/{device_id}/telemetry` (documentos gravados pelo worker MQTT)

## 1. Propósito

Responder perguntas como:

- “Qual a última leitura do meu sensor?”
- “Temperatura e umidade do **Meu sensor** agora?”
- “Última telemetria do device da sala”

**Não** substitui histórico/gráficos (`get_telemetry_history` — futuro).

---

## 2. Tool MCP

| Atributo | Valor |
|----------|--------|
| Nome (EN) | `read_latest_telemetry` |
| `user_id` | Injetado pelo backend (Bearer / deps); **nunca** parâmetro da tool |

---

## 3. Entrada (`ReadLatestTelemetryInput`)

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `device_id` | UUID string \| omitido | omitido | Device específico (deve pertencer ao usuário) |
| `device_name` | string \| omitido | omitido | Nome amigável; ver `device_name_match` |
| `device_name_match` | `"contains"` \| `"exact"` | `"contains"` | Igual `list_devices` |

**Resolução do device (ordem):**

1. Se `device_id` → validar `user_id` no documento `devices`.
2. Senão, se `device_name` → `list_devices` com filtro; **0** → `device_not_found`; **>1** na página → `device_ambiguous`.
3. Senão → se o usuário tem **exatamente um** device adotado (`list_devices` limit 2, sem `has_more`) → usar esse; caso contrário → `device_required`.

---

## 4. Saída (`ReadLatestTelemetryResult`)

```json
{
  "device_id": "…",
  "device_name": "Meu sensor",
  "device_type": "sensor",
  "device_ts": "2026-10-14T03:51:09Z",
  "received_at": "2026-10-14T03:51:09.123456Z",
  "readings": [
    { "metric": "temperature", "value": 23.4, "unit": "C" },
    { "metric": "humidity", "value": 61.2, "unit": "%" }
  ],
  "has_telemetry": true
}
```

| Campo | Descrição |
|-------|-----------|
| `readings` | Todas as métricas do **mesmo evento** (`received_at` mais recente na subcoleção) |
| `has_telemetry` | `false` se subcoleção vazia (device existe, ainda sem ingestão) |

---

## 5. Erros

| Código | Quando |
|--------|--------|
| `device_not_found` | ID inexistente, outro tenant, ou nome sem match |
| `device_ambiguous` | Vários devices para o nome informado |
| `device_required` | Vários devices e nenhum filtro |
| `firebase_not_configured` | Firestore indisponível |

---

## 6. Camadas

```
tools/read_latest_telemetry.py → services/telemetry_queries.py → Firestore
agent/device_tools.py          → mesmo service
```

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-14 | v1 — contrato inicial |
