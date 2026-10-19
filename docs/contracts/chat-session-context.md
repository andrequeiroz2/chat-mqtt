# Contrato — contexto de sessão de chat (v1)

> **Status:** Implementado (task 011, ondas 1–2)  
> **Normativo com:** [`docs/chat-conversational-policy.md`](../chat-conversational-policy.md), [`docs/glossary.md`](../glossary.md), [`docs/auth.md`](../auth.md)  
> **Não substitui:** histórico de mensagens (`chat_sessions/.../messages`); telemetria (`devices/.../telemetry`)

## 1. Propósito

Persistir **estado conversacional** por sessão de chat: foco de device, snapshot enxuto de devices do usuário e metadados para o **resolver** (`services/device_intent_resolver` — task 011-f).

**Proibido** neste documento: payloads de telemetria, credenciais MQTT, conteúdo bruto de tópicos.

---

## 2. Localização Firestore

| Caminho | Campo |
|---------|--------|
| `users/{user_id}/chat_sessions/{session_id}` | `conversation_context` (objeto JSON, §4) |

O documento da sessão **já** existe ao persistir turnos (`session_id`, `updated_at`). `conversation_context` é escrito com **merge** pelo backend (Admin SDK).

Subcoleção `messages/` permanece exclusiva para histórico LLM (task 007).

---

## 3. Configuração (backend)

| Variável | Default | Descrição |
|----------|---------|-----------|
| `CHAT_DEVICE_SNAPSHOT_CAP` | `20` | Máximo de entradas em `device_snapshot` |
| `CHAT_CONTEXT_SCHEMA_VERSION` | `1` | Valor escrito em `schema_version` |

---

## 4. Schema `conversation_context` (v1)

### 4.1 Objeto raiz

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `schema_version` | int | sim | Atualmente `1` |
| `updated_at` | string (ISO UTC `Z`) | sim | Última escrita do contexto |
| `session_focus_device_id` | string (UUID) \| null | sim | Foco conversacional; ver policy §3 |
| `focus_reason` | enum \| null | sim | `adoption` \| `user_mention` \| `ui` \| null |
| `device_count` | int | sim | Total devices adotados do user (até cap de consulta) |
| `sensor_count` | int | sim | Subconjunto `device_type == sensor` |
| `actuator_count` | int | sim | Subconjunto `device_type == actuator` |
| `device_snapshot` | array | sim | Lista de `DeviceSnapshotEntry` (§4.2), ordenada por `adopted_at` **desc** |
| `pending_actuator_command` | object \| null | não | Comando 0/1 aguardando confirmação — ver [`actuator-binary-command.md`](actuator-binary-command.md) |

### 4.2 `DeviceSnapshotEntry`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `device_id` | string | sim | UUID |
| `device_name` | string \| null | sim | Nome amigável (`device_name` Firestore) |
| `device_type` | `"sensor"` \| `"actuator"` | sim | |
| `adopted_at` | string (ISO UTC) | sim | Ordenação do snapshot |
| `operation_status` | string \| null | não | `online` \| `offline` \| outro; **null** = desconhecido (policy §7) |
| `last_seen_at` | string \| null | não | ISO UTC |
| `last_command` | object \| null | não | Espelho atuador — **shape reservado** até contrato 011-d; omitir se ausente |
| `last_command_at` | string \| null | não | ISO UTC; idem |
| `last_reported_state` | object \| null | não | Resumo JSON pequeno; idem 011-d / worker 011-i |

**Limite sugerido:** `last_reported_state` ≤ 2 KiB serializado; `last_command` ≤ 1 KiB (validar na implementação 011-d).

### 4.3 Exemplo

```json
{
  "schema_version": 1,
  "updated_at": "2026-10-16T02:00:00Z",
  "session_focus_device_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "focus_reason": "adoption",
  "device_count": 3,
  "sensor_count": 2,
  "actuator_count": 1,
  "device_snapshot": [
    {
      "device_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "device_name": "Sala",
      "device_type": "sensor",
      "adopted_at": "2026-10-15T20:00:00Z",
      "operation_status": "offline",
      "last_seen_at": "2026-10-15T19:55:00Z",
      "last_command": null,
      "last_command_at": null,
      "last_reported_state": null
    }
  ]
}
```

---

## 5. Refresh do snapshot

| Gatilho | Ação |
|---------|------|
| Primeiro turno da sessão (contexto ausente) | Build completo via query `devices` (`user_id`, adotados, ordenar por `adopted_at` desc, limit cap) |
| `POST` adoção **committed** (UI 009) | Set foco + refresh; ver §6 |
| Tool `list_devices` / `update_device` / `remove_device` no turno | Refresh opcional (implementação: **após** mutação ou TTL 60 s — escolher uma na 011-e) |
| `publish_command` bem-sucedido (011-h) | Patch entrada do atuador em snapshot + campos `last_command*` |
| Worker atualiza `devices` (`operation_status`, `last_reported_state`) | Refresh no **próximo** turno ou TTL; **não** exige Redis |

Campos espelhados vêm do documento `devices` (e, quando existirem, `last_command*` / `last_reported_state`). Fonte de verdade permanece `devices`, não o snapshot.

---

## 6. Eventos lógicos (integração)

Contratos HTTP dedicados **podem** ser adicionados depois (009 ↔ chat). MVP: comportamento mínimo abaixo.

| Evento | Origem | Efeito no contexto |
|--------|--------|-------------------|
| `adoption_committed` | Frontend após `session_status=committed` | `session_focus_device_id` = device adotado; `focus_reason=adoption`; refresh snapshot; disparar turno zero (policy §9) — mecanismo UI/LLM: pendência task 011-j |
| `focus_changed` | UI (fase posterior) ou resolver após `user_mention` | Atualizar foco + `focus_reason` |
| `chat_turn_completed` | Backend 011-g | Persistir contexto se foco/snapshot alterados no turno |

**Não bloqueante:** turno zero pode usar LLM + policy templates sem endpoint novo; evento `adoption_committed` pode ser **só** chamada interna `conversation_context.set_focus_after_adoption(user_id, session_id, device_id)` desde a UI após commit.

---

## 7. Saída do resolver (referência para 011-f)

O resolver **lê** `conversation_context` + utterance; **não** persiste mensagens.

| Campo saída | Tipo | Descrição |
|-------------|------|-----------|
| `outcome` | `execute` \| `clarify` \| `instruct` \| `off_topic` | |
| `trigger_id` | string \| null | Ex.: `G2`, `G11` |
| `template_id` | string \| null | Ex.: `T1`, `T5` — [`chat-conversational-policy.md`](../chat-conversational-policy.md) §8 |
| `device_id` | string \| null | Candidato único quando `execute` |
| `clarify_options` | array \| null | `{ device_id, device_name, device_type }` |
| `connectivity` | `online` \| `offline` \| `unknown` | Derivado de `operation_status` no snapshot ou device |

Presença para G11/G12 **no MVP sem 011-m:** usar `operation_status` / `last_seen_at` do **snapshot** ou de `DeviceSummary` (`list_devices`) — não exige amend imediato de `read_latest_telemetry`.

---

## 8. Segurança

- Leitura/escrita **somente** Admin SDK no backend; `user_id` do token, **nunca** do corpo.
- `session_id` do cliente deve pertencer ao mesmo user (mesmas regras que chat).
- **Nunca** gravar tokens, senhas MQTT ou payloads completos de telemetria em `conversation_context`.

---

## 9. Relação com artefatos em aberto (task 011)

| Artefato | Bloqueia 011-e/f? |
|----------|-------------------|
| [`chat-conversational-policy.md`](../chat-conversational-policy.md) | Não (fechado v1) |
| Este contrato (011-b) | Não |
| 011-d `last_command` / `last_reported_state` em `devices` | **Não** — campos opcionais no snapshot; omitir até existirem |
| 011-m `read_latest_telemetry` + presença na saída | **Não** — melhora copy pós-tool; resolver usa snapshot |
| 011-n guard tempo real UI | **Não** — paralelo ao resolver G12 |
| `publish_command` / worker `state` | **Não** — G10/G7 parcial sem last_command |

---

## 10. Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-15 | v1 — schema `conversation_context`, refresh, eventos lógicos, resolver ref |
