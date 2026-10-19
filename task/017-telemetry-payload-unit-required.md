# Task 017 — Contrato telemetria: `unit` obrigatório por leitura

> **Status:** Concluída (63 testes passando; contrato §6.1 atualizado)  
> **Origem:** Revisão de contratos worker MQTT ↔ device (2026-10-18); decisão: **Gap A sim** — cada amostra `metric` + `value` + **`unit` obrigatório**; **Gap B não** — **sem** vocabulário fechado de unidades  
> **Escopo:** Ingestão MQTT no worker ([`src/mqtt_chat/schemas/telemetry.py`](../src/mqtt_chat/schemas/telemetry.py), [`src/mqtt_chat/services/telemetry.py`](../src/mqtt_chat/services/telemetry.py)), contrato [`device-adoption.md`](../docs/contracts/device-adoption.md) §6.1, testes. **NÃO** alterar frontend, drawer, SSE, glossário ou tópicos MQTT.

## Objetivo

Garantir que toda leitura persistida em Firestore (`devices/{id}/telemetry`) tenha **`unit` string não vazio**, para que `read_latest_telemetry` e `get_telemetry_history` (gráfico) sempre exibam grandeza + unidade (`C`, `%`, `Bar`, …).

## Decisões (fechadas)

| Item | Decisão |
|------|---------|
| `unit` no JSON do device | **Obrigatório** em cada leitura (`readings[]` e formato legado single-metric) |
| Vocabulário de unidades | **Aberto** — qualquer string não vazia aceita (sem lista fixa) |
| Leitura inválida no lote | **Descartar somente a leitura inválida**; demais leituras válidas do mesmo payload **seguem** para persistência |
| `parameter_ranges` (adoção) | Não é fonte obrigatória de `unit` nesta task; device **deve** enviar `unit` |

## Entregáveis

- [x] **017-01** `ReadingItem` (e equivalente single-metric): `unit: str` com validação **não vazia** (após `strip`), Pydantic v2.
- [x] **017-02** [`persist_telemetry`](../src/mqtt_chat/services/telemetry.py): separar leituras válidas vs inválidas; persistir **só** válidas; log estruturado para descarte (evento `telemetry.reading.discarded`, seguindo [`docs/logging.md`](../docs/logging.md)).
- [x] **017-03** Se **todas** as leituras do payload forem inválidas: comportamento de “empty telemetry” (log, sem gravação) — documentado em `_valid_readings_from_raw` / `expanded_readings`.
- [x] **017-04** Contrato [`device-adoption.md`](../docs/contracts/device-adoption.md) §6.1: tabela de campos com **`unit` obrigatório**, nota de descarte individual e RF-PAY-03.
- [x] **017-05** Testes: [`tests/test_telemetry_unit_contract.py`](../tests/test_telemetry_unit_contract.py) — schema, descarte parcial, descarte total, legado single-metric.
- [x] **017-06** Simulador host (task 002) já envia `unit` (`--unit`, default `%`). Embedded: [`embedded/firmware/sensor_sim.py`](../embedded/firmware/sensor_sim.py) passou a **sempre** incluir `unit` (fallback `C`/`%` por métrica se `parameter_ranges` omitir) — alinhado ao descarte do worker.

## Fora de escopo

- Migração de dados históricos Firestore com `unit: null` (avaliar separadamente; gráfico pode mostrar `null` até reprocessar ou expirar TTL futuro).
- Validação `parameter_ranges` min/max (Gap C da revisão — task futura opcional).
- Idempotência QoS1 / duplicatas (Gap E — discussão separada).
- Novos documentos de contrato MQTT além do ajuste em `device-adoption.md` (Gap D — opcional futuro).

## Verificação

1. Publicar telemetria com `readings` misto (uma leitura sem `unit`, outra com): só a válida aparece no Firestore e no `read_latest_telemetry`.
2. Publicar single-metric sem `unit`: nenhum documento novo na subcoleção `telemetry`.
3. `uv run pytest` — suíte worker/telemetria verde.
4. Pedir “gráfico” no chat com simulador emitindo com `unit`: tooltip/eixo mostram unidade.

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-18 | Task criada — decisão `unit` obrigatório, unidades abertas, descarte parcial de leituras inválidas |
| 2026-10-18 | Implementação: schema, worker, evento `telemetry.reading.discarded`, contrato §6.1 + RF-PAY-03, testes; task concluída |
