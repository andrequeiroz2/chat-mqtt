# Política conversacional — TomatoIA (chat)

> **Status:** v1 (normativo para MVP conversacional)  
> **Task:** [011-chat-session-context-policy.md](../task/011-chat-session-context-policy.md)  
> **Precedência:** abaixo [`requirements.md`](requirements.md); acima do system prompt do agente e de improviso do modelo  
> **Relacionado:** [`glossary.md`](glossary.md), [`contracts/mcp-read-latest-telemetry.md`](contracts/mcp-read-latest-telemetry.md), [`contracts/realtime-websocket.md`](contracts/realtime-websocket.md), [007](../task/007-tomatoia-chat-guardrails.md), [009](../task/009-adoption-guided-chat-ux.md)

Documento normativo para **resolução de device**, **clarificação**, **pós-adoção**, **presença (online/offline/desconhecido)** e **copy fixa** em português. Implementação: resolver em `services/` + agente redige dentro dos templates quando indicado.

---

## 1. Escopo

- **In-scope:** devices **adotados** do `user_id` autenticado; telemetria via tools; tempo real via UI/WebSocket orientado pelo chat; adoção **orientada à UI** (sem tool de handshake).
- **Fora:** valores numéricos ou estado ao vivo **inventados**; telemetria só de RAG; confirmação estilo “tem certeza?” para **leitura** ou **tempo real**.

---

## 2. Clarificação vs confirmação

| Mecanismo | Uso | Exemplo |
|-----------|-----|---------|
| **Clarificação** | Não há **um** device ou intenção clara | “Qual sensor: *Sala* ou *Quintal*?” |
| **Confirmação** | Ação que **altera** o físico ou remove device | “Confirmar ligar o relé *Garagem*?” |

**Regra:** ambiguidade de leitura → **clarificar** quando o resolver não reduzir a um único candidato; **nunca** confirmação para `read_latest_telemetry` ou início de tempo real.

---

## 3. Resolução de device (ordem)

1. Match de **nome** na utterance (`contains` / `exact`, alinhado a `list_devices`).
2. **Foco de sessão** (`session_focus_device_id`) se pedido compatível.
3. Contagem/heurísticas (ex.: exatamente **1 sensor** e **0 atuadores** para telemetria clara).
4. Se ainda ≠ 1 candidato → **clarificar** (lista curta, chips quando a UI suportar).

**Foco de sessão**

- Após **adoção commitada**, o device adotado vira foco automaticamente.
- Permanece até o usuário **falar de outro** device (nome, escolha na clarificação) ou a UI emitir mudança de foco (fase posterior).
- **Sem** expiração por minutos.

Detalhe de persistência: [`contracts/chat-session-context.md`](contracts/chat-session-context.md).

---

## 4. Tabela de gatilhos

| ID | Gatilho | Ação |
|----|---------|------|
| G1 | Leitura/telemetria, 1 sensor, 0 atuadores | Executar `read_latest_telemetry`; citar `{device_name}` |
| G2 | Leitura/telemetria, 1 sensor, ≥1 atuador | Esclarecer intenção (sensor vs atuador) — §5 |
| G3 | Leitura, ≥2 sensores, sem match nome, foco não desempata | Clarificar lista de sensores |
| G4 | Match nome → exatamente 1 device | Executar conforme `device_type` e capacidade |
| G5 | Match nome → 0 ou ≥2 | Clarificar |
| G6 | Foco válido + pedido compatível | Usar foco se resolver = 1 |
| G7 | Alvo atuador, pedido “leitura” de sensor | Instruir: estado, comando — §6 |
| G8 | Turno zero pós-adoção, `sensor` | Oferecer última leitura + tempo real (se online — §7) |
| G9 | Turno zero pós-adoção, `actuator` | Estado/comando; **sem** tempo real |
| G10 | Comando / destrutivo | Confirmação obrigatória (contrato futuro `publish_command`) |
| G11 | Última leitura, device resolvido, offline ou desconhecido | §7 + templates **T1–T4** |
| G12 | Tempo real, device resolvido, offline ou desconhecido | §7; templates **T5–T6**; **não** abrir stream |
| G13 | Inventário ("quantos/quais/tenho devices/sensores/atuadores") | Responder do snapshot (`list_devices` determinístico, sem LLM) — task 021 |
| G14 | Metadado de adoção ("que dia/quando foi registrado/adotado") | Responder `adopted_at` do snapshot; alvo: nome citado → foco → device único; ≥2 sem alvo → clarificar — task 022 |

---

## 5. Frota mista (G2) — esclarecer intenção

Quando o usuário pede algo como “última leitura” e existe **1 sensor** e **≥1 atuador**:

- **Não** assumir o sensor em silêncio.
- Pergunta curta + opções: leitura do sensor `{device_name}` **ou** estado/comando de qual atuador.

**Template T-INTENT-MIXED** (fixo; preencher nomes):

> Você quer a **última leitura do sensor** **{sensor_name}** ou saber o **estado de um atuador** (relé, etc.)?  
> • Sensor: **{sensor_name}**  
> • Atuadores: **{actuator_names_list}**

---

## 6. Atuador (G7)

- **Não** tratar “última leitura” como sinônimo oculto de `state`.
- Explicar em uma frase o que o atuador faz na plataforma (comandos, estado reportado).
- Oferecer: ver **último estado reportado** (`last_reported_state`) ou **último comando** enviado pela plataforma, quando existirem.

---

## 7. Presença: online, offline, desconhecido

### 7.1 Definição (MVP)

| Valor | Condição | Tratamento |
|-------|----------|------------|
| **online** | `operation_status == "online"` | Tempo real permitido (G12 não bloqueia). |
| **offline** | `operation_status == "offline"` | §7.2 e §7.3. |
| **desconhecido** | `operation_status` **ausente** ou valor não reconhecido | **Não** assumir online. Copy “não sei se está conectado”; §7.2/7.3 com templates **T3**, **T6**. |

Fonte: documento `devices` (`operation_status`, `last_seen_at`), alimentado pelo worker via MQTT `.../status` (LWT). Telemetria histórica: subcoleção `telemetry` — independente de online **agora**.

### 7.2 Última leitura (G11)

| Conectividade | `has_telemetry` | Comportamento |
|---------------|-----------------|---------------|
| offline | sim | Mostrar readings + template **T1** |
| offline | não | Template **T2** |
| desconhecido | sim | Mostrar readings + template **T3** |
| desconhecido | não | Template **T4** |
| online | sim/não | Resposta normal; se online sem dados, informar “ainda sem leituras registradas”. |

**Proibido:** rotular amostra stale como “agora”, “ao vivo” ou “temperatura atual” quando offline/desconhecido.

### 7.3 Tempo real (G12)

| Conectividade | Comportamento |
|---------------|---------------|
| **offline** | **Não** invocar `start_realtime_telemetry`; **não** montar bubble WebSocket. Template **T5**. |
| **desconhecido** | Idem (tratar como não elegível para live). Template **T6**. |
| **online** | Fluxo normal de tempo real. |

Opcional após **T5**/**T6**: oferecer última leitura registrada (G11) se `has_telemetry`.

---

## 8. Templates PT fixos (alertas e presença)

Placeholders (preenchidos pelo backend/agente a partir de tools; **não** inventar):

| Placeholder | Origem |
|-------------|--------|
| `{device_name}` | `display_name` ou fallback |
| `{readings_block}` | Texto curto das métricas (ex.: “23,4 °C, 61 % umidade”) |
| `{received_at}` | ISO UTC da amostra (`received_at` telemetria) |
| `{last_seen_at}` | ISO UTC do device, se existir; senão omitir frase |

### T1 — Última leitura + offline + com telemetria

> **Última leitura registrada** do sensor **{device_name}** (em **{received_at}**): {readings_block}.  
> **Atenção:** o sensor está **offline** no momento{last_seen_suffix}. Esse valor **não** é ao vivo.

`{last_seen_suffix}` = vazio ou: ` (última atividade em **{last_seen_at}**)` quando `last_seen_at` existir.

### T2 — Última leitura + offline + sem telemetria

> O sensor **{device_name}** está **offline**{last_seen_suffix} e **ainda não há leituras registradas** na plataforma (ou nenhuma foi guardada). Quando o sensor voltar a publicar, as leituras aparecerão aqui.

### T3 — Última leitura + conectividade desconhecida + com telemetria

> **Não sei se o sensor **{device_name}** está conectado agora** (sem status de presença).  
> **Última leitura registrada** (em **{received_at}**): {readings_block}. Esse valor **pode não** refletir o momento atual.

### T4 — Última leitura + desconhecido + sem telemetria

> **Não sei se o sensor **{device_name}** está conectado** e **não há leituras registradas** ainda. Verifique energia e Wi‑Fi no dispositivo ou aguarde a primeira publicação.

### T5 — Tempo real + offline

> O sensor **{device_name}** está **offline**{last_seen_suffix}. **Não dá para acompanhar leituras em tempo real** agora.  
> Quer ver a **última leitura registrada**?

(Só executar G11 se o usuário aceitar ou pedir de novo.)

### T6 — Tempo real + conectividade desconhecida

> **Não sei se o sensor **{device_name}** está conectado** (sem status de presença). **Não vou abrir o acompanhamento em tempo real** até haver confirmação de que está online.  
> Posso mostrar a **última leitura registrada**, se existir.

---

## 9. Pós-adoção (turno zero)

Após adoção **commitada** (UI 009):

1. Definir **foco de sessão** no device adotado.
2. Mensagem proativa: parabéns + **“O que você quer fazer agora?”**
3. Opções dependem de `device_type`:
   - **Sensor:** última leitura; tempo real **somente se** `operation_status == online` (senão copy **T5**/orientação).
   - **Atuador:** estado / comando; sem tempo real.

Futuras ações entram como novos chips/intents na mesma estrutura.

**Template T-POST-ADOPT** (corpo fixo; preencher `{device_name}`, `{device_type_pt}`):

> Pronto! O dispositivo **{device_name}** ({device_type_pt}) foi adicionado à sua conta. **O que você quer fazer agora?**

`device_type_pt`: “sensor” | “atuador” (UX PT; contrato permanece `sensor` | `actuator`).

---

## 10. Comandos de atuador (ligar / desligar → 0 / 1)

O usuário **não** conhece o payload MQTT. Sinónimos comuns mapeiam para **valor digital**:

| Intenção PT | Valor enviado ao device |
|-------------|-------------------------|
| ligar, ativar, acionar, abrir, … | **1** (on) |
| desligar, desativar, fechar, … | **0** (off) |

Contrato técnico: [`contracts/actuator-binary-command.md`](contracts/actuator-binary-command.md).

**Fluxo (G10):**

1. Resolver identifica **atuador** + verbo de potência (ou pergunta se falta).
2. Resposta de **confirmação** com nome do atuador, ação em PT e valor **0** ou **1**.
3. Contexto guarda `pending_actuator_command` até **sim** / **confirmo** ou cancelamento.
4. Após confirmação, backend publica em `.../commands` e atualiza `last_command*` quando disponível.

**Template T-COMMAND-CONFIRM:**

> Vou **{verb_pt}** o atuador **{device_name}** (comando digital **{binary_value}** — **0** = desligado, **1** = ligado).  
> Responda **sim** para confirmar ou **não** para cancelar.

**Template T-COMMAND-SENT:**

> Comando enviado: **{verb_pt}** **{device_name}** (`value`: **{binary_value}**).

**Template T-COMMAND-POWER-ASK:**

> Quer **ligar (1)** ou **desligar (0)** o atuador **{device_name}**?

---

## 11. UX — identificadores

- **Nunca** mostrar `device_id` (UUID) na copy voltada ao usuário (chat, templates, erros).
- Usar **`device_name`** (nome amigável) ou rótulos genéricos: “seu sensor”, “Atuador 2”, etc.
- `device_id` permanece **somente** em contratos internos (tools, Firestore, WebSocket, foco de sessão).

---

## 12. Papel do LLM vs resolver

| Peça | Faz |
|------|-----|
| **Resolver** (`services/`) | G1–G12, elegibilidade, offline, candidatos |
| **Tools** | Dados reais (telemetria, listagem) |
| **TomatoIA** | Redação em PT; **usar templates T1–T6, T-INTENT-MIXED, T-POST-ADOPT** quando o resolver indicar `template_id`; pode acrescentar **uma** frase curta contextual, **sem** alterar fatos (valores, datas, online/offline) |

### 12.1 Autoridade primária (normativo — 018)

O **resolver determinístico é a autoridade primária** de intenção e device. Turnos cobertos por G1–G12 ou por intents com `short_circuit` (leitura, histórico/gráfico, tempo real, comando de atuador, MAC/IP, tópicos MQTT) **não** passam pelo LLM — a resposta vem de template ou de execução direta em `services/`.

O **LLM** (Pydantic AI) cobre somente o **long tail** não resolvido: conversação geral in-scope, listagens abertas, pedidos que o resolver marcou como `pass_through`. Nesses casos, o system prompt (seções Escopo / Tools / Proibições / Erros) e o `output_type` estruturado (`scope` + `reply`) são as rédeas; proibições críticas de dados continuam garantidas pelas **tools** (que leem Firestore) e nunca pelo improviso do modelo.

### 12.2 Heurísticas de período do resolver (histórico/gráfico)

Parsing PT em `services/resolver_turn.py` (normativo para o MVP):

| Utterance (exemplos) | Parâmetro aplicado |
|----------------------|--------------------|
| “últimos **N** dias” | `days = N` (limitado a 1–30) |
| “semana”, “última semana”, “7 dias” | `days = 7` (default) |
| “último dia” | `days = 1` |
| “último dia **com registros**” | `last_day_with_data = true` (restringe ao dia calendário UTC da leitura mais recente) |
| “temperatura” / “umidade” no texto | `metric` correspondente; ausente → métrica mais frequente no período |

---

## 13. Histórico

| Data | Alteração |
|------|-----------|
| 2026-10-15 | v1 — policy inicial; gatilhos G1–G12; templates T1–T6; desconhecido se `operation_status` ausente |
| 2026-10-16 | §10 — NL atuador → 0/1; confirmação G10; templates T-COMMAND-* |
| 2026-10-16 | §11 — proibido expor device_id ao usuário |
| 2026-10-18 | §12.1 — resolver como autoridade primária; §12.2 — heurísticas de período (task 018) |
