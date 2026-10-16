# Contrato — comando binário de atuador (0/1)

> **Status:** v1 (MVP)  
> **Normativo com:** [`device-adoption.md`](device-adoption.md) §6.2, [`chat-conversational-policy.md`](../chat-conversational-policy.md)  
> **Task:** [011](../task/011-chat-session-context-policy.md) · tool MCP `publish_command` (011-h)

## 1. Propósito

O usuário fala em linguagem natural (**ligar**, **ativar**, **abrir**, **desligar**, **fechar**, …). A plataforma **normaliza** para um comando digital binário enviado ao firmware:

| Valor MQTT `value` | Significado |
|--------------------|-------------|
| **0** | off / desligado / fechado |
| **1** | on / ligado / aberto (ação ativa) |

O embarcado **não** precisa interpretar sinônimos em português — só **0** e **1** (JSON number).

## 2. Payload MQTT (`.../commands`)

```json
{
  "action": "set",
  "channel": 1,
  "value": 1,
  "command_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Campo | Tipo MVP | Notas |
|-------|----------|--------|
| `action` | `"set"` | Fixo MVP relé/canal único |
| `channel` | int | Default **1**; futuro: `command_spec` |
| `value` | **0 \| 1** (integer) | **Normativo MVP** para firmware mqtt-chat |
| `command_id` | UUID string | Idempotência / correlação com `state` |

**Compatibilidade:** PoC/simulador podem aceitar `boolean`; firmware produção (ESP32) deve usar **0/1** conforme este contrato.

## 3. Mapeamento linguagem natural (PT)

Implementação: `services/actuator_command_language.py`.

| Classe | Exemplos de utterance | `value` |
|--------|------------------------|---------|
| **Ligar (on)** | ligar, liga, ligue, ativar, ativa, acionar, aciona, abrir, abre, energizar | **1** |
| **Desligar (off)** | desligar, desliga, desligue, desativar, desativa, fechar, fecha, feche, cortar | **0** |

- **Ambíguo** (nenhum verbo de potência): perguntar “ligar (**1**) ou desligar (**0**)?”.
- **G10:** confirmação explícita antes de publicar (ver policy § confirmação de comando).

## 4. Persistência pós-envio

Documento `devices/{device_id}` — [`device-adoption.md`](device-adoption.md) §2.1 (011-d):

- `last_command` — espelho resumido do payload (sem secrets)
- `last_command_at` — ISO UTC

Tool MCP **`publish_command`** (`device_id`, `value` 0|1, `channel` opcional) delega a `services/actuator_command_service.py` e exige fila MQTT da API.

## 5. Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-16 | v1 — valor integer 0/1; mapeamento NL PT |
