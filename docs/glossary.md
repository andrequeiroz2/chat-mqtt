# Glossário — nomenclatura mqtt-chat

Documento **normativo** para alinhar texto em português (docs, chat, docstrings) com identificadores em inglês (código, Firestore, MQTT, tools MCP). Em conflito com código existente, **este glossário prevalece** após atualização de `docs/requirements.md`.

Regra Cursor (cita este glossário e [`docs/skills.md`](skills.md) como normativos): [`.cursor/rules/mqtt-chat-project.mdc`](../.cursor/rules/mqtt-chat-project.mdc) — *Documentos normativos*, *Agent Skills*.

---

## Regra geral

| Contexto | Idioma | Exemplo |
|----------|--------|---------|
| Documentação, comentários, docstrings | **Português** | “Registra o dispositivo do usuário no Firestore.” |
| Classes, funções, variáveis, tools MCP, campos JSON | **Inglês** | `list_devices`, `device_type`, `user_id` |

---

## Termos principais

| Termo em português (docs / UX / docstring) | Identificador em inglês (código / contrato) | Definição |
|--------------------------------------------|---------------------------------------------|-----------|
| **TomatoIA** | `tomato_ia` (config/código se necessário) | Nome do **assistente conversacional** e **marca futura do produto** (UX, prompts). Apresentação ao usuário: “TomatoIA”. Repositório/pacote `mqtt-chat` permanece até rename explícito em `docs/requirements.md`. |
| **Usuário** | `user` | Pessoa que se autentica na aplicação; dono de devices. Campo típico: `user_id` (Firebase Auth UID ou UUID estável). **NUNCA** usar `usuario` em identificadores. |
| **Provedor de identidade** | `identity_provider` | OAuth federado (MVP: **Google**) no Firebase Authentication. Valor típico em `auth_providers`: `google.com`. |
| **Perfil do usuário** | `user_profile` | Metadados de aplicação em Firestore `users/{user_id}` (ex.: `display_name`, `photo_url`), complementares ao registro Auth. **NUNCA** confundir com documento `device`. |
| **Dispositivo** / **dispositivo embarcado** | `device` | Hardware conectado (ESP32, etc.) que publica/assina MQTT. Entidade persistida: coleção/documento `devices`. **NUNCA** `dispositivo`, `embedded_device` como nome de tabela/classe, salvo termo de domínio externo citado. |
| **Identificador do dispositivo** | `device_id` | Chave pública do device (UUID ou ID estável); aparece em tópicos MQTT e Firestore. |
| **Endereço MAC** | `mac_address` | Identidade de hardware (normalizado uppercase com `:`); **unique** em `devices`; distinto de `device_id`. |
| **Base de tópico MQTT** | `mqtt_topic_base` | Prefixo MQTT único persistido (ex.: `tenants/{user_id}/devices/{device_id}`); ver [`docs/contracts/device-adoption.md`](contracts/device-adoption.md). |
| **Estado de adoção** | `adoption_status` | Em `devices`: sempre `adopted`. Ciclo em andamento: `session_status` em `adoption_sessions`. |
| **Tipo de dispositivo** | `device_type` | Discriminador do papel do hardware. **Valores permitidos (literal):** `sensor`, `actuator`. **NUNCA** `atuador`, `Sensor`, `ACTUATOR` como valor de contrato. |
| **Sensor** | `sensor` | Valor de `device_type`: lê ambiente (umidade, temperatura, etc.). Subtipo opcional: `sensor_type` (ex.: `DHT11`, `BME280`). |
| **Atuador** | `actuator` | Valor de `device_type`: age no físico (relé, motor, LED). Subtipo opcional: `actuator_type` (ex.: `relay`, `motor`). |
| **MQTT** | `MQTT` / `mqtt` | Protocolo OASIS ([spec](https://mqtt.org/mqtt-specification/)). Prefixo em libs/config: `mqtt_` (ex.: `mqtt_client`, `mqtt_username`). |
| **Broker** / **broker MQTT** | `broker` | Servidor de mensagens MQTT. **Implementação obrigatória:** Eclipse Mosquitto (`eclipse-mosquitto:2`). Metadados: `host`, `port`, credenciais — espelho conceitual de `mqtt_brokers` no `device_app`. **Não** confundir com `device`: broker é infraestrutura; device é endpoint. |
| **Cliente MQTT (backend)** | `mqtt_client` / worker | Processo Python (backend) que assina/publica no broker; **não** é o embarcado. |
| **Telemetria** | `telemetry` | Dados enviados pelo device (leituras). Tópico: `.../telemetry`. Persistência: **Firestore** (subcoleção por `device_id`), **não** SQLite/`mqtt_messages`. |
| **Comando** | `command` | Ordem ao atuador. Tópico: `.../commands`. MVP binário: `value` **0** (off) ou **1** (on) — [`actuator-binary-command.md`](contracts/actuator-binary-command.md). |
| **Estado** / **ACK** | `state` | Confirmação ou estado reportado pelo device. Tópico: `.../state`. |
| **Proprietário** | `owner` / `user_id` | Usuário associado ao device após cadastro ou adoção. |
| **Adoção** | `adoption` / `adopt` | **Única forma** de **incluir** um device na conta do usuário (registro lógico + commit Firestore/MQTT). QR → sessão → handshake → ack → commit. Ver [`docs/contracts/device-adoption.md`](contracts/device-adoption.md) §4. **Não** existe cadastro paralelo via chat/MCP. |
| **Sessão de adoção** | `adoption_session` | Estado transitório (TTL) em `adoption_sessions`; **não** substitui documento em `devices`. |
| **Token de adoção** | `claim_token` | String opaca no QR; **não** é senha MQTT. Estado **`bound`** enquanto device adotado; **pode** reutilizar após remoção/reset (contrato §3.2). |
| **Provisionamento** | `provisioning` | Criação de credenciais MQTT + ACL no Mosquitto após adoção. |
| **Inquilino** (multi-tenant) | `tenant` | Namespace lógico; na PoC pode coincidir com `user_id`. Tópico: `tenants/{user_id}/...`. |
| **Foco de sessão** (chat) | `session_focus_device_id` | Device implicitamente em pauta na sessão de chat; ver [`docs/chat-conversational-policy.md`](chat-conversational-policy.md). |
| **Snapshot de sessão** (chat) | `conversation_context` / `device_snapshot` | Metadados enxutos de devices (sem telemetria) no doc `chat_sessions`; ver task [011](../task/011-chat-session-context-policy.md). |
| **Status de operação** | `operation_status` | Presença lógica do device (`online` \| `offline`); MQTT `.../status` + LWT. Ausente no MVP conversacional = conectividade **desconhecida**, não assumir online. |
| **Política conversacional** | *(doc)* | Regras TomatoIA: [`docs/chat-conversational-policy.md`](chat-conversational-policy.md). |

---

## `device_type` (obrigatório)

| Valor EN (único permitido) | Significado PT | Capacidades típicas |
|----------------------------|----------------|---------------------|
| `sensor` | Sensor | Publica telemetria; consome comandos apenas se o firmware exigir |
| `actuator` | Atuador | Assina comandos; publica `state`; pode publicar telemetria de status |

- **DEVE** validar `device_type` com enum Pydantic ou `Literal["sensor", "actuator"]`.
- **NUNCA** persistir ou expor `actuador`, `sensor_fisico`, etc. como valor de `device_type`.

---

## Tools MCP (nome EN + descrição PT)

| Tool (inglês) | Ação em português (docstring / UX) |
|---------------|-------------------------------------|
| `list_devices` | Listar dispositivos do usuário (somente já adotados) — contrato: [`docs/contracts/mcp-list-devices.md`](contracts/mcp-list-devices.md) |
| `update_device` | Atualizar metadados de device **já adotado** (ex.: nome amigável) |
| `remove_device` | Remover device da conta (libera re-adoção — contrato §3.2) |
| `read_latest_telemetry` | Ler última telemetria — contrato: [`docs/contracts/mcp-read-latest-telemetry.md`](contracts/mcp-read-latest-telemetry.md) |
| `publish_command` | Publicar comando (actuator) |
| `get_telemetry_history` | Obter histórico para gráfico |
| `get_realtime_stream_info` | Metadados do WebSocket tempo real (UI) — [`docs/contracts/realtime-websocket.md`](contracts/realtime-websocket.md) |
| `get_user_profile` | Ler perfil do usuário autenticado (opcional; preferir deps para saudação) |
| `update_user_profile` | Atualizar campos permitidos do perfil (ex.: `display_name`) |

**Não expor no MCP (MVP):** `register_device` — **não** cria device. Inclusão **somente** via **adoção** (UI + QR); o LLM **orienta** o usuário à tela de adoção (RF-ADOPT-03). PoC com simulador/cadastro manual **não** é modelo de produção.

---

## Exemplos proibidos vs corretos

| Proibido | Correto |
|----------|---------|
| `def listar_dispositivos():` | `def list_devices():` |
| `device_type: "atuador"` | `device_type: "actuator"` |
| `usuario_id` | `user_id` |
| Docstring em inglês explicando regra de negócio | Docstring em português |
| “O broker device publicou…” (broker ≠ device) | “O **device** publicou no **broker**…” |

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-09 | Versão inicial: user/device, MQTT/broker, `device_type` ∈ {`sensor`, `actuator`} |
| 2026-10-10 | `mac_address`, `mqtt_topic_base`, `adoption_status`; link contrato adoção v1 |
| 2026-10-10 | `adoption_session`; fluxo commit tardio (contrato v1.1) |
| 2026-10-12 | Adoção = único registro de device; `register_device` fora do MCP MVP |
| 2026-10-10 | Telemetria: persistência Firestore only (sem espelho `mqtt_messages`) |
| 2026-10-10 | `identity_provider`, `user_profile`; tools opcionais de perfil (task 006) |
| 2026-10-11 | **TomatoIA** — assistente/marca (task 007) |
| 2026-10-15 | Foco/snapshot de sessão, `operation_status` (chat); link policy task 011 |
