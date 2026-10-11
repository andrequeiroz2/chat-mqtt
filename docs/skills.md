# Agent Skills — mqtt-chat

Skills instaladas **no repositório** em [`.agents/skills/`](../.agents/skills/). O Cursor carrega automaticamente a partir daí.

**Regra Cursor (cita este documento e `.agents/skills/` como normativos):** [`.cursor/rules/mqtt-chat-project.mdc`](../.cursor/rules/mqtt-chat-project.mdc) — seções *Documentos normativos* e *Agent Skills*.

**Regra de uso:** não invocar todas as Skills em toda tarefa. Usar conforme a matriz abaixo. Stack e [`docs/glossary.md`](glossary.md) **prevalecem** sobre exemplos genéricos das Skills.

---

## Análise (critérios do projeto)

| Critério | Como aplicamos |
|----------|----------------|
| Popularidade | Preferência por Skills com tração em [skills.sh](https://skills.sh/); repositórios oficiais (`pydantic`, `anthropics`) pesam mais que estrelas isoladas. |
| Qualidade técnica | Exemplos executáveis, tipagem, testes — validar sempre contra docs oficiais (FastMCP, Pydantic v2, Pydantic AI). |
| Confiabilidade | **mcp-builder** e **pydantic** são oficiais/com maintainer do ecossistema; demais são comunidade — usar com revisão humana. |

### Ajustes à stack mqtt-chat

| Skill | Alinhamento | Ressalva |
|-------|-------------|----------|
| **mcp-builder** | Alta — tools IoT, Pydantic, segurança | Servidor MCP **DEVE** ser **FastMCP** (regra do projeto), não só SDK cru; cruzar com [FastMCP](https://gofastmcp.com/getting-started/welcome) e padrão `~/DEV/mcp/mcp-sport`. |
| **pydantic** | Alta — schemas, `Field`, serialização | Contratos EN; docstrings PT ([glossário](glossary.md)). |
| **building-pydantic-ai-agents** | Alta — agente de chat | Oficial Pydantic; complementa PoC do chat. |
| **pydantic-ai-harness** | Média — sessões longas | Opcional; usar só se adotarmos Harness. |
| **python-patterns** | Alta — módulos, refatoração | Complementar **clean-code**. |
| **improve-codebase-architecture** | Alta — camadas `tools/services/clients` | Snyk/skills.sh: risco médio — revisar sugestões antes de refactor grande. |
| **clean-code** | Alta — revisão | Evitar refatoração cosmética fora do escopo. |
| **vercel-composition-patterns** | Alta — arquitetura de componentes React | Foco em composição (providers, compound components); **não** é guia de performance/Next — ver [skills.sh](https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices) se precisar. Stack mqtt-chat: **Vite + React** (ignorar regras específicas de Next.js). |

**Não instaladas de propósito:** Skills de migração *→ Pydantic AI* e Logfire (instalação acidental do repo `pydantic/skills` sem `@pydantic` — removidas).

---

## Skills instaladas

| Prioridade | Skill (pasta) | Origem | Reinstalar |
|------------|---------------|--------|------------|
| 1 | `python-patterns` | [affaan-m/ecc](https://github.com/affaan-m/ecc) | `npx skills add affaan-m/ecc@python-patterns -y` |
| 2 | `improve-codebase-architecture` | [mattpocock/skills](https://github.com/mattpocock/skills) | `npx skills add mattpocock/skills@improve-codebase-architecture -y` |
| 3 | `clean-code` | [wondelai/skills](https://github.com/wondelai/skills) | `npx skills add wondelai/skills@clean-code -y` |
| 4 | `pydantic` | [pydantic/skills](https://github.com/pydantic/skills) | `npx skills add pydantic/skills@pydantic -y` |
| 5 | `mcp-builder` | [anthropics/skills](https://github.com/anthropics/skills) | `npx skills add anthropics/skills@mcp-builder -y` |
| — | `building-pydantic-ai-agents` | pydantic/skills (extra) | `npx skills add pydantic/skills@building-pydantic-ai-agents -y` |
| — | `pydantic-ai-harness` | pydantic/skills (extra) | `npx skills add pydantic/skills@pydantic-ai-harness -y` |
| 6 | `vercel-composition-patterns` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | `npx skills add vercel-labs/agent-skills@vercel-composition-patterns -y` |

**Importante:** use sempre `@nome-da-skill` ao adicionar de um monorepo — **NUNCA** `npx skills add https://github.com/pydantic/skills` sem `@`, ou instala dezenas de Skills.

---

## Quando usar (matriz)

| Tarefa | Skills |
|--------|--------|
| Implementar/revisar Python | `python-patterns`, `clean-code` |
| Definir/refatorar pastas (`tools`, `services`, `clients`) | `improve-codebase-architecture`, `python-patterns` |
| Schemas Firestore/MQTT, tools MCP, validators | `pydantic`, `clean-code` |
| Agente Pydantic AI, streaming, tools | `building-pydantic-ai-agents`, `pydantic` |
| Novo servidor MCP / tools IoT | `mcp-builder`, regra **FastMCP** + referência **mcp-sport** |
| Harness / agente longo (futuro) | `pydantic-ai-harness` |
| Frontend React (Vite), login, chat, layout | `vercel-composition-patterns` |

**Complementares (não instaladas):** `vercel-react-best-practices` (~788K installs, performance/bundle); `anthropics/skills@frontend-design` (~974K, UI visual).

---

## Histórico

| Data | Ação |
|------|------|
| 2026-10-09 | Instalação das 5 Skills solicitadas + 2 extras Pydantic AI; remoção migração/Logfire |
| 2026-10-11 | `vercel-composition-patterns` (task 006 / frontend React) |
