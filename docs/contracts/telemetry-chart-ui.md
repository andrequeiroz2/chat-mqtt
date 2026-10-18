# Contrato UI — gráfico de telemetria (`telemetry_chart`)

> **Status:** v1  
> **Tool:** `get_telemetry_history` ([`glossary.md`](../glossary.md))  
> **Frontend:** Recharts 3, tema zinc ([012](../../task/012-frontend-modern-ui-stack.md))

## Fluxo

1. Usuário pede histórico / gráfico (ex.: última semana).
2. Agente chama **`get_telemetry_history`** (Firestore `devices/{id}/telemetry`).
3. Resposta HTTP inclui `suggested_ui` com série de pontos.
4. Frontend monta bolha **`telemetry_chart`** (lazy Recharts).

## `suggested_ui` (JSON)

| Campo | Tipo | Obrigatório |
|-------|------|-------------|
| `kind` | `"telemetry_chart"` | sim |
| `device_id` | string | sim |
| `device_name` | string \| null | sim |
| `metric` | string | sim |
| `unit` | string \| null | sim |
| `period_label` | string (ex. `"7d"`) | sim |
| `points` | array | sim, 1–500 itens |

Cada ponto:

| Campo | Tipo |
|-------|------|
| `received_at` | string ISO-8601 |
| `value` | number |

## RF-UX-CHART-*

| ID | Requisito |
|----|-----------|
| RF-UX-CHART-01 | Gráfico dentro de superfície `card` (dark zinc). |
| RF-UX-CHART-02 | Eixos/tooltip legíveis (`muted-foreground`, `border`). |
| RF-UX-CHART-03 | Lazy-load do bundle Recharts por bolha. |

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-17 | Contrato v1 |
