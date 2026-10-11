# Task 003 — Levantamento contratos adoção e rede

> **Status:** Concluída (spec v1 entregue — revisão humana pendente para “Aprovado”)  
> **Fase:** Pré-MVP / ponte PoC → adoção  
> **Depende de:** [001-docker.md](001-docker.md), [002-device-simulator.md](002-device-simulator.md)  
> **Bloqueia:** [004-mqtt-worker.md](004-mqtt-worker.md), alinhamento final do simulador, API `POST /devices/adopt`

## Objetivo

Fechar **requisitos e contratos** (payload MQTT, identidade do `device`, tópicos, QR, Firestore) para adoção simples pelo usuário web — **antes** de implementar worker de telemetria ou provisionamento Mosquitto.

Experiência alvo: cliente compra sensor (ex.: temperatura + umidade) → cadastra-se na web → escaneia QR → backend associa o device ao `user_id` → firmware recebe config de rede/MQTT (detalhe de transporte WiFi em task futura).

Referência de domínio: `~/DEV/Tauri/device_app` (MAC único, `device_id` UUID na adoção, `parameter_ranges` / `command_spec`). Adoção lá é serial; mqtt-chat usa **QR + web** com as mesmas separações lógicas.

Entregável normativo: [`docs/contracts/device-adoption.md`](../docs/contracts/device-adoption.md) **v1.1**.

---

## Matriz de versões

| Componente | Versão / pin | Notas |
|------------|--------------|--------|
| **MQTT (contrato)** | 3.1.1 na PoC | Compatível com simulador e Mosquitto 2.0.21 |
| **Broker** | `eclipse-mosquitto:2.0.21` | Task 001 |
| **Simulador PoC** | `scripts/devices/simulate_device.py` | Tópicos `tenants/...` — ver § migração no contrato |
| **Firestore** | — | Modelo lógico na spec; implementação em tasks posteriores |

---

## Entregáveis (checklist)

- [x] [`docs/contracts/device-adoption.md`](../docs/contracts/device-adoption.md) com versão **v1** no cabeçalho
- [x] Diagrama de sequência: QR → sessão → validação contrato → handshake → **commit** Firestore + Mosquitto após ack do device
- [x] Tabela de tópicos (base + sufixos) + QoS + retain + LWT
- [x] Schemas JSON (telemetria multi-métrica, commands, state, status, metadados de device)
- [x] Modelo Firestore: `devices` (pós-commit), `adoption_sessions` (transitório), `factory_inventory` (opcional)
- [x] RFs numerados (RF-ID-*, RF-QR-*, RF-TOP-*, RF-PAY-*, RF-ADOPT-*) prontos para [`docs/requirements.md`](../docs/requirements.md)
- [x] Índice em [README.md](README.md) (003 concluída spec; 004 pendente)
- [ ] **Aprovação humana** explícita no contrato (checkbox “Aprovado v1”) — pendente

---

## Decisões registradas (resumo)

| Tema | Decisão v1 |
|------|------------|
| Chave lógica | **1:1** — `device_id` (UUID, doc/API/MQTT) + `mac_address` (hardware, **unique**); não é chave composta — ver contrato §2.5 |
| Tópico canônico no banco | Campo `mqtt_topic_base` (unique), prefixo MQTT real pós-adoção |
| Namespace MQTT | Manter PoC: `tenants/{user_id}/devices/{device_id}` |
| Sufixos | `telemetry`, `commands`, `state`, `status` (não `/data` do device_app) |
| QR produto (MVP) | Deep link + `claim_token` opaco (requirements §4.3) |
| QR dev / fábrica mínima | Alternativa documentada: só `mac_address` com device `pending` |
| QR rejeitado | MAC + topic redundante; topic com MAC como ID canônico no Firestore |
| Persistência | **`devices` só após** contrato OK, sem dono conflitante e `adoption_ack` (v1.1) |

Detalhes, tabelas e exemplos JSON: ver contrato v1.1.

---

## Fora de escopo

- Implementação FastAPI, firmware ESP32, TLS/ACL Mosquitto automatizado, worker aiomqtt
- Escolha final de WiFi provisioning (SoftAP / BLE / SmartConfig) — apenas requisitos de interface no contrato
- Leitura de QR pelo LLM (permanece UI dedicada)

---

## Impacto no simulador (PoC)

| Item | Até task 004+ | Após alinhamento implementação |
|------|----------------|--------------------------------|
| `--user-id`, `--device-id` | Válido para testes manuais | Deve refletir `user_id` / `device_id` reais pós-adoção |
| Payload telemetria | Uma métrica por mensagem | Contrato v1 permite **array `readings`** ou múltiplas mensagens — ver contrato |
| MAC / QR | Não simulado | Flags ou doc para emular `pending` + adopt |

---

## Verificação

1. Ler [`docs/contracts/device-adoption.md`](../docs/contracts/device-adoption.md) e percorrer fluxo “sensor temp+umidade” ponta a ponta.
2. Confirmar que `device_id`, `mac_address` e `mqtt_topic_base` não são intercambiáveis na spec.
3. Comparar sufixos MQTT com [`002-device-simulator.md`](002-device-simulator.md) — divergências só as listadas no contrato (device_app vs mqtt-chat).
4. Marcar contrato como **Aprovado v1** após revisão (data no histórico do contrato).

**Verificado (entrega spec):** 2026-10-10 — documentos criados; aprovação de produto pendente.

---

## Próxima task

| ID | Arquivo | Conteúdo |
|----|---------|----------|
| 004 | [004-mqtt-worker.md](004-mqtt-worker.md) | Worker: assinar telemetria conforme contrato, persistir Firestore |

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-10 | Task criada; entregue `docs/contracts/device-adoption.md` v1; README tasks 003/004 |
| 2026-10-10 | Contrato v1.1 — commit tardio em `devices`; fluxo sessão + ack bilateral |
