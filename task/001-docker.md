# Task 001 — Docker: Mosquitto (broker MQTT)

> **Status:** Concluída  
> **Fase:** PoC  
> **Referências:** [`docs/requirements.md`](../docs/requirements.md) §4.1 · [`docs/glossary.md`](../docs/glossary.md) · [Eclipse Mosquitto](https://mosquitto.org/) · [Docker Hub — eclipse-mosquitto](https://hub.docker.com/_/eclipse-mosquitto)

## Objetivo

Definir e implementar a stack **Docker** local com broker **Mosquitto** para a PoC: compose reproduzível, versões fixadas, configuração documentada e teste publish/subscribe nos tópicos `tenants/{user_id}/devices/{device_id}/...`.

Esta task **concentra todo o escopo** (não há subtask separada).

---

## Matriz de versões (obrigatória na implementação)

Valores abaixo são a **referência desta task**. Ao implementar, fixar no `docker-compose.yml` e registrar aqui se houver divergência.

| Componente | Versão mínima / pin | Notas |
|------------|---------------------|--------|
| **Docker Engine** | `29.x` (dev validado: `29.8.0`) | Mínimo recomendado: **24.0+** |
| **Docker Compose** (plugin CLI) | `v2.20+` (dev validado: `v5.5.1`) | Comando: `docker compose` (não `docker-compose` v1) |
| **Compose file format** | Especificação [Compose Specification](https://docs.docker.com/compose/compose-file/) | **Não** usar `version: '3.8'` legado; arquivo moderno sem chave `version` |
| **Imagem MQTT** | `eclipse-mosquitto:2.0.21` | Pin de **patch**; série major `2` alinhada à regra do projeto. Atualizar patch apenas com registro nesta task |
| **Digest (opcional, recomendado CI)** | `eclipse-mosquitto@sha256:94f5a3d7deafa59fa3440d227ddad558f59d293c612138de841eec61bfa4d353` | Obtido após `docker pull` em 2026-10-09 |
| **Arquitetura** | `linux/amd64` ou nativa do host | Documentar se usar `platform:` no compose (Apple Silicon / ARM) |

### Política de atualização de imagem

1. **DEVE** preferir tag `2.0.x` patch, não `2` flutuante em produção.
2. **DEVE** rodar teste de publish/subscribe após qualquer bump de patch.
3. **NUNCA** trocar para EMQX ou outra imagem sem alterar `docs/requirements.md` e a regra Cursor.

---

## Entregáveis (checklist)

- [x] `docker-compose.yml` na raiz do repositório
- [x] `docker/mosquitto/mosquitto.conf`
- [x] Volume nomeado para persistência (`mosquitto_data`, `mosquitto_log`)
- [x] `.env.example` com variáveis (porta host)
- [x] Seção **Docker** no `README.md` (subir, parar, testar, versões)
- [x] Atualizar **Status** desta task para **Concluída** quando verificação passar

---

## Especificação `docker-compose.yml` (alvo)

| Campo | Valor |
|-------|--------|
| Serviço | `mosquitto` |
| `image` | `eclipse-mosquitto:2.0.21` |
| `container_name` | `mqtt-chat-mosquitto` (opcional, fixo para dev) |
| Portas | `1883:1883` (MQTT TCP PoC); **não** expor `8883` até TLS (MVP) |
| Volumes | `./docker/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro` + volume dados |
| `restart` | `unless-stopped` |
| Rede | rede bridge dedicada `mqtt-chat-net` (nome explícito) |

---

## Especificação `docker/mosquitto/mosquitto.conf` (PoC)

| Diretiva | Valor PoC | MVP (nota) |
|----------|-----------|------------|
| `listener` | `1883` | + listener `8883` com certificados |
| `allow_anonymous` | `true` **somente dev local** | `false` + `password_file` / ACL |
| `persistence` | `true` | — |
| `log_dest` | `stdout` | — |
| `log_type` | `error`, `warning`, `notice`, `information` | reduzir ruído em prod |

Documentar no README que **auth anônima é proibida fora de dev**.

---

## Tópicos e teste (verificação)

Prefixo obrigatório ([`docs/glossary.md`](../docs/glossary.md)):

- `tenants/dev-user/devices/sim-1/telemetry`
- `tenants/dev-user/devices/sim-1/commands`
- `tenants/dev-user/devices/sim-1/state`

### Procedimento de verificação

1. `docker compose up -d`
2. `docker compose ps` — serviço `running`
3. Cliente MQTT no container:

```bash
docker compose exec mosquitto sh -c \
  'mosquitto_sub -t "tenants/dev-user/devices/sim-1/telemetry" -C 1 -W 5 & sleep 1; \
   mosquitto_pub -t "tenants/dev-user/devices/sim-1/telemetry" -m "{\"metric\":\"humidity\",\"value\":42}"; wait'
```

4. `docker compose down` (ou `down -v` se teste limpo)

**Verificado:** 2026-10-09 — publish/subscribe OK.

---

## Fora de escopo (task 001)

- Simulador Python de `device` (task **002** sugerida)
- Worker backend `aiomqtt` / Firestore
- TLS, ACL por `user_id` / `device_id`, adoção QR
- Firebase, FastAPI, FastMCP

---

## Próxima task sugerida

| ID | Arquivo | Conteúdo |
|----|---------|----------|
| 002 | [002-device-simulator.md](002-device-simulator.md) | Simulador `scripts/devices/simulate_device.py` — **concluída** |

---

## Histórico desta task

| Data | Alteração |
|------|-----------|
| 2026-10-09 | Task única `001-docker.md`; versões Docker/Compose/Mosquitto especificadas |
| 2026-10-09 | Implementação concluída; digest registrado; teste MQTT OK |
