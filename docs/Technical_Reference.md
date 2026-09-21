# Technical Reference — MCP Sport (F1)

> Documento **canônico** do projeto. Todas as decisões técnicas, padrões de código e
> implementações devem seguir as referências listadas aqui. Em caso de dúvida ou
> conflito, a **documentação oficial listada abaixo é a fonte da verdade**.

## 1. Visão Geral do Projeto

Servidor **MCP (Model Context Protocol)** para consumo da **OpenF1 API** (dados de
Fórmula 1), expondo ferramentas (tools) para clientes MCP (Claude Desktop, MCP
Inspector, Cursor, etc.).

### Fase 1 — Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | **Python 3.13+** |
| Framework MCP | **FastMCP 4.x** |
| SDK base | **MCP Python SDK** (dependência transitiva do FastMCP) |
| API de dados | **OpenF1 API** (REST, pública) |
| Validação de dados | **Pydantic** |
| HTTP/API (fases futuras) | **FastAPI** |
| Gerenciador de projeto/deps | **uv** (pyproject.toml) |

## 2. Model Context Protocol (MCP)

Especificação e conceitos do protocolo. Referência para entender o ciclo de vida,
transportes (stdio/HTTP), tools, resources, prompts e a arquitetura cliente-servidor.

| Tópico | Link |
|---|---|
| Introdução / Getting Started | https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro |
| Especificação (2026-07-28) | https://modelcontextprotocol.io/specification/2026-07-28 |
| Arquitetura | https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture |
| Build Server | https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server |
| Build Client | https://modelcontextprotocol.io/docs/2026-07-28/develop/build-client |

**Versão da spec adotada:** `2026-07-28`

## 3. FastMCP

Framework principal do servidor. É a camada de implementação usada no dia a dia
(decorators `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`, CLI `fastmcp run` /
`fastmcp dev inspector`, transports, etc.).

| Tópico | Link |
|---|---|
| Site oficial | https://gofastmcp.com/ |
| Quickstart | https://gofastmcp.com/getting-started/quickstart |
| Instalação | https://gofastmcp.com/getting-started/installation |
| Servers | https://gofastmcp.com/servers/server |
| Apps | https://gofastmcp.com/apps/overview |
| Clients | https://gofastmcp.com/clients/client |
| Índice para LLMs | https://gofastmcp.com/llms.txt |

**Versão adotada:** `>= 4.0.5` (pin em `pyproject.toml`)

### 3.1 MCP Apps (views HTML)

Padrão adotado: **Custom HTML**. Sem dependência `prefab-ui`.

| Peça | Referência |
|---|---|
| FastMCP Apps | https://gofastmcp.com/apps/overview |
| SDK JS no iframe | `https://unpkg.com/@modelcontextprotocol/ext-apps@0.4.0/app-with-deps` |
| Repo e host de validação (`examples/basic-host`) | https://github.com/modelcontextprotocol/ext-apps |

O SDK JS fica em **0.4.0** (mesma versão do exemplo oficial `qr-server`;
wire protocol compatível com hosts 1.x e 2.x). CSP `resourceDomains` declara
`unpkg.com` e `media.formula1.com`.

O Cursor não renderiza MCP Apps (resultado cai no JSON). A validação visual
é no `basic-host`. Detalhe de implementação: `docs/Architectural_Design.md`,
seção 4.7.

## 4. MCP Python SDK

SDK oficial de baixo nível, base do FastMCP. Consultar para detalhes de protocolo,
tipos e comportamentos não expostos diretamente pelo FastMCP.

| Tópico | Link |
|---|---|
| Documentação | https://py.sdk.modelcontextprotocol.io/ |
| Get Started | https://py.sdk.modelcontextprotocol.io/get-started/ |
| Instalação | https://py.sdk.modelcontextprotocol.io/get-started/installation/ |
| What's New | https://py.sdk.modelcontextprotocol.io/whats-new/ |
| Migração | https://py.sdk.modelcontextprotocol.io/migration/ |
| API Reference | https://py.sdk.modelcontextprotocol.io/api/mcp/ |

## 5. OpenF1 API

Fonte de dados de Fórmula 1 (tempo real e histórico): sessões, pilotos, voltas,
pit stops, telemetria, clima, etc.

| Tópico | Link |
|---|---|
| Documentação | https://openf1.org/docs/ |

**Base URL:** `https://api.openf1.org/v1`

## 6. FastAPI

Reservado para fases futuras (exposição HTTP própria, gateways, endpoints auxiliares,
integração com o transporte HTTP do MCP).

| Tópico | Link |
|---|---|
| Documentação | https://fastapi.tiangolo.com/ |
| Tutorial | https://fastapi.tiangolo.com/tutorial/ |
| Avançado | https://fastapi.tiangolo.com/advanced/ |
| Referência | https://fastapi.tiangolo.com/reference/ |

## 7. Pydantic

Validação e serialização de dados: modelos de resposta da OpenF1, schemas de
entrada/saída das tools.

| Tópico | Link |
|---|---|
| Get Started (Validation) | https://pydantic.dev/docs/validation/latest/get-started/ |

## 8. Repositórios de Referência (GitHub)

Código-fonte, issues e exemplos oficiais.

| Projeto | Repositório |
|---|---|
| FastMCP | https://github.com/PrefectHQ/fastmcp |
| MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk |
| MCP Servers (exemplos oficiais) | https://github.com/modelcontextprotocol/servers |
| FastAPI | https://github.com/fastapi/fastapi |
| Pydantic | https://github.com/pydantic/pydantic |

## 9. Regras de Uso deste Documento

1. **Fonte da verdade:** qualquer implementação deve ser validada contra os links
   oficiais acima antes de assumir comportamento por memória.
2. **Versões:** mudanças de versão (FastMCP, SDK, spec MCP) devem ser registradas
   neste arquivo junto com o changelog oficial correspondente.
3. **Novas tecnologias:** só entram no projeto após serem adicionadas aqui com suas
   referências oficiais.
4. **Ordem de consulta:** FastMCP (docs) → MCP Python SDK → Especificação MCP →
   repositórios GitHub (issues/exemplos).
