# Task 014 — Gráfico de telemetria (Recharts) no chat

> **Status:** Concluída (verificação manual 2026-10-18)  
> **Depende de:** [013](013-frontend-tailwind-shadcn-bootstrap.md), [012](012-frontend-modern-ui-stack.md)  
> **Contrato:** [`docs/contracts/telemetry-chart-ui.md`](../docs/contracts/telemetry-chart-ui.md)

## Objetivo

Tool **`get_telemetry_history`** → `suggested_ui.kind === telemetry_chart` → bolha Recharts no thread.

## Entregáveis

- [x] Serviço Firestore + schemas + tool agente (+ MCP opcional)
- [x] Frontend: tipos, parse, `TelemetryChart`, lazy-load
- [x] Testes serviço
- [x] Verificação manual no chat

## Verificação

1. Pedir “gráfico da última semana” com simulador emitindo telemetria.
2. Bolha cinza (`card`) com linha e tooltip; sem crash com 0 pontos (tool erro amigável).

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-18 | Verificação manual OK; task concluída |
