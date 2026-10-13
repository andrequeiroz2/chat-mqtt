# Contrato MCP — `list_devices` (v1)

> **Status:** Aprovado para implementação **6c**  
> **Normativo com:** [`docs/glossary.md`](../glossary.md) (nome da tool), [`docs/requirements.md`](../requirements.md) §7, [`docs/auth.md`](../auth.md) (escopo `user_id`)  
> **Fonte de dados:** coleção Firestore `devices` (§2.1 de [`device-adoption.md`](device-adoption.md)) — **somente** registros pós-commit (`adoption_status`: `adopted`)

## 1. Propósito

Permitir que o **TomatoIA** (via Pydantic AI → FastMCP) responda perguntas do tipo:

- “Quais devices eu tenho?”
- “Liste meus sensores / atuadores”
- “Ache o device **Sala**”

**Não** cria, adota, remove nem altera devices. Inclusão na conta continua **somente** adoção (UI + `adopt/*`).

---

## 2. Tool MCP

| Atributo | Valor |
|----------|--------|
| Nome (EN) | `list_devices` |
| Docstring | **Português** — ver §7 |
| Identidade | `user_id` **nunca** é parâmetro da tool; injetado pelo backend (Bearer → contexto MCP / deps) |

---

## 3. Entrada (`ListDevicesInput`)

Todos os campos são **opcionais**. Sem filtros = todos os devices **adotados** do usuário autenticado.

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `device_type` | `"sensor"` \| `"actuator"` \| omitido | omitido | Restringe por tipo lógico (`device_type` Firestore) |
| `device_name` | string, 1–120 | omitido | Filtro por nome amigável (`device_name`) |
| `device_name_match` | `"contains"` \| `"exact"` | `"contains"` | `contains`: case-insensitive, substring; `exact`: igualdade case-insensitive |
| `device_id` | string UUID | omitido | Se informado, retorna **no máximo um** device; **deve** pertencer ao `user_id` do token |
| `limit` | int, 1–100 | `50` | Máximo de itens no array de saída |
| `cursor` | string \| null | `null` | Paginação opaca (ver §5); omitido ou `null` = primeira página |

### 3.1 Validação (Pydantic / validators)

| Regra | Erro (`detail` / tool error) |
|-------|------------------------------|
| `limit` fora de 1–100 | `invalid_limit` |
| `device_type` inválido | `invalid_device_type` |
| `device_name` vazio após trim | ignorar filtro ou `invalid_device_name` (implementação: **rejeitar** string só espaços) |
| `device_id` informado **e** outros filtros (`device_type`, `device_name`) | **permitido** — todos aplicados em conjunto (AND) |
| `cursor` malformado / expirado | `invalid_cursor` |

**Não** expor filtro por `mac_address` na v1 da tool (evita incentivar o LLM a tratar MAC como chave de UX; adoção/dev usam outros fluxos). Evolução v2 se necessário.

---

## 4. Saída (`ListDevicesResult`)

```json
{
  "devices": [ /* DeviceSummary, ver §4.1 */ ],
  "total_returned": 2,
  "has_more": false,
  "next_cursor": null
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `devices` | array | Ordenação estável: `device_name` asc (case-insensitive), desempate `device_id` asc |
| `total_returned` | int | `len(devices)` nesta página |
| `has_more` | bool | `true` se existir página seguinte |
| `next_cursor` | string \| null | Cursor para próxima chamada; `null` se `has_more` é false |

Lista vazia **não** é erro — resposta HTTP/MCP 200 com `devices: []`.

### 4.1 `DeviceSummary` (item)

Campos expostos ao LLM (sem secrets MQTT):

| Campo | Tipo | Obrigatório na resposta | Origem Firestore |
|-------|------|-------------------------|------------------|
| `device_id` | string | sim | doc id / campo `device_id` |
| `device_name` | string \| null | sim | `device_name` |
| `device_type` | `"sensor"` \| `"actuator"` | sim | `device_type` |
| `model` | string | sim | `model` |
| `sensor_type` | string \| null | sim | `sensor_type` |
| `actuator_type` | string \| null | sim | `actuator_type` |
| `firmware_version` | string \| null | sim | `firmware_version` |
| `operation_status` | string \| null | sim | `operation_status` (ex.: `online`, `offline`) |
| `last_seen_at` | string (ISO 8601 UTC) \| null | sim | `last_seen_at` |
| `adopted_at` | string (ISO 8601 UTC) | sim | `adopted_at` |

**Excluídos** da listagem (outras tools / detalhe futuro): `mqtt_topic_base`, credenciais MQTT, `parameter_ranges`, `command_spec`, `mac_address` (v1).

---

## 5. Paginação

- Implementação MVP: query Firestore `devices` where `user_id` == `{injected}` (+ `device_type` se filtro), ordenar em memória ou via índice; aplicar filtros `device_name` / `device_id` no **service** se Firestore não suportar `contains`.
- `cursor`: base64url de payload interno `{last_device_id, last_device_name, filters_hash}` — **não** documentar formato ao LLM; tratar como token opaco.
- Se `device_id` é informado e o documento não existe ou `user_id` difere → **`devices: []`** (não vazar existência cross-tenant). Opcional: código `device_not_found` só quando semântica de “get one” for tool separada no futuro; para `list_devices` v1 preferir lista vazia.

---

## 6. Erros de negócio

| Código | Quando | Mensagem sugerida (PT, para o agente repassar) |
|--------|--------|--------------------------------------------------|
| `invalid_limit` | `limit` inválido | Parâmetro de limite inválido. |
| `invalid_device_type` | enum | Tipo deve ser sensor ou actuator. |
| `invalid_cursor` | cursor | Paginação inválida; liste de novo sem cursor. |
| (Firestore indisponível) | client error | Não foi possível consultar seus dispositivos agora. |

---

## 7. Docstring da tool (texto para o modelo)

```
Lista dispositivos já adotados na conta do usuário autenticado.

Use quando o usuário pedir para ver, listar, contar ou encontrar devices,
sensores ou atuadores por nome.

Parâmetros opcionais:
- device_type: "sensor" ou "actuator" para filtrar.
- device_name: nome amigável; use device_name_match "contains" (padrão) ou "exact".
- device_id: UUID específico (retorna no máximo um, se pertencer ao usuário).
- limit / cursor: paginação (padrão limit=50).

Não adota nem registra devices. Para adicionar um device, oriente o usuário
ao fluxo de adoção na interface (QR / pareamento), não invente devices.

Retorno: lista resumida (id, nome, tipo, modelo, online/offline, last_seen).
Lista vazia significa nenhum device corresponde aos filtros.
```

---

## 8. Mapeamento frase do usuário → parâmetros

| Intenção (exemplos) | Chamada |
|---------------------|---------|
| “Todos os meus devices” | `{}` |
| “Meus sensores” | `{ "device_type": "sensor" }` |
| “Atuadores” | `{ "device_type": "actuator" }` |
| “Device da cozinha” / “sensor Sala” | `{ "device_name": "cozinha" }` ou `{ "device_name": "Sala" }` |
| “Quantos devices tenho?” | `{}` — agente conta `devices.length` (ou `total_returned` + paginar se `has_more`) |

---

## 9. Camadas de implementação (6c)

```
tools/list_devices.py   → thin FastMCP @mcp.tool()
services/devices.py     → list_devices(user_id, ListDevicesInput) → ListDevicesResult
schemas/devices.py      → ListDevicesInput, DeviceSummary, ListDevicesResult
clients/firebase.py     → (existente) Firestore
```

Testes unitários: service com Firestore mock; validadores de input; **nunca** passar `user_id` vindo do JSON da tool nos testes de integração MCP sem contexto auth.

---

## 10. Verificação

1. Usuário A com 2 sensors + 1 actuator; usuário B com 0 — `list_devices` de A retorna 3; B retorna `[]`.
2. `device_type=sensor` retorna 2.
3. `device_name` contains “sala” encontra “Sensor Sala”.
4. Token de A + `device_id` de B → `[]`.
5. Cursor: segunda página não repete itens.

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-12 | v1 — contrato `list_devices` para task 006 **6c** |
| 2026-10-12 | Implementação 6c: `server.py`, `/api/v1/mcp`, `FirebaseTokenVerifier` |
