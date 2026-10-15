# Contrato — WebSocket tempo real (v1)

> **Status:** Implementado (PoC)  
> **Normativo:** [`docs/auth.md`](../auth.md), [`docs/glossary.md`](../glossary.md) (`telemetry`, `device`)

## 1. Propósito

Permitir que o **frontend** (usuário autenticado) receba **telemetria** e **status** assim que o worker MQTT ingere — sem polling HTTP.

**Não** é tool MCP para o LLM: o chat continua usando `read_latest_telemetry` / futuro histórico. O WebSocket é **transporte browser ↔ API**.

---

## 2. Endpoint

| | |
|---|---|
| URL | `GET /api/v1/realtime/ws` (upgrade WebSocket) |
| Auth | Query `token=<Firebase ID token>` (JWT curto; renovar no cliente ao expirar) |
| Filtro opcional | `device_id=<uuid>` — só eventos desse device (deve pertencer ao `user_id`) |

Mensagens: **JSON** texto, uma por frame.

---

## 3. Eventos servidor → cliente

Envelope comum:

```json
{ "type": "<event_type>", "payload": { ... } }
```

| `type` | Quando | `payload` (campos principais) |
|--------|--------|-------------------------------|
| `connected` | Após auth OK | `user_id`, `device_id_filter` (null = todos) |
| `telemetry` | MQTT `.../telemetry` ingerido | `device_id`, `device_ts`, `received_at`, `readings[]` |
| `device_status` | MQTT `.../status` | `device_id`, `operation_status`, `last_seen_at` |
| `error` | Erro interno | `code`, `message` |

---

## 4. Segurança

- Token validado com Admin SDK (mesmo que HTTP Bearer).
- Eventos **sempre** filtrados pelo `user_id` do token; nunca cross-tenant.
- `device_id` na query: 404 lógico → fechar WS com código **4404** se device não for do usuário.

---

## 5. Frontend

Hook `useRealtimeStream` em `services/frontend/src/realtime/` — URL base de `VITE_API_BASE_URL` (http→ws).

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-14 | v1 — telemetria + status |
