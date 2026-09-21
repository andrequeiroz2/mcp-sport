# Logging Strategy — MCP Sport (F1)

> Estratégia canônica de logs do projeto. Complementa `docs/Technical_Reference.md`.
> Fontes: [spec MCP 2026-07-28 — Logging](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/logging)
> e [FastMCP — Client Logging](https://gofastmcp.com/servers/logging).

## 1. Contexto e decisão

Na spec MCP `2026-07-28`, o mecanismo de Logging do protocolo
(`notifications/message` + capability `logging`) está **depreciado** (SEP-2577).
Novas implementações **não devem** adotá-lo como estratégia principal; a direção
oficial é:

- **stdio** → logs em `stderr`
- **observabilidade estruturada** → OpenTelemetry (fase futura)

Além disso, o controle de verbosidade é **por requisição**: o cliente envia
`io.modelcontextprotocol/logLevel` no `_meta` da requisição e as notificações
são request-scoped (não existe mais nível global definido pelo cliente).

**Decisão:** estratégia em duas camadas (server-side principal + client-facing
moderada), sem depender do mecanismo depreciado para observabilidade.

## 2. Restrição do transporte stdio

O servidor roda em **stdio**: `stdout` é o canal do protocolo JSON-RPC.
**Nenhum log ou `print()` pode ir para `stdout`** — corrompe o protocolo.
Todo log server-side vai para `stderr`.

> **Nota:** clientes MCP (Cursor, Inspector) exibem **todas** as linhas de
> `stderr` com rótulo `[error]`, independentemente do nível real do log.
> É apenas a forma como o cliente apresenta o stream — verifique o nível
> no próprio conteúdo da linha (`INFO`, `ERROR`, ...), não no rótulo.

## 3. Camada 1 — Server-side (principal)

- Módulo `logging` padrão do Python, handler em `stderr`
- Configuração centralizada em `src/mcp_sport/logging_config.py`
- Logger raiz do projeto: `mcp_sport`, com filhos hierárquicos por subsistema:

| Logger | Responsabilidade |
|---|---|
| `mcp_sport.tools` | Entrada/saída e duração das tools |
| `mcp_sport.openf1` | Chamadas à OpenF1 API (URL, status, latência). HTTP 429/503 gera `event=openf1_retry` em warning antes da nova tentativa |

- Nível via env var `MCP_SPORT_LOG_LEVEL` (default: `INFO`)
- Formato estruturado: `timestamp level logger event key=value ...`
- Campos padronizados: `event`, `session_key`, `driver_number`, `duration_ms`, `url`

## 4. Camada 2 — Client-facing (telemetria por requisição)

Uso **moderado** e consciente da depreciação, apenas para UX em clientes de
desenvolvimento (MCP Inspector):

- `ctx.info()` — progresso de operações longas
- `ctx.warning()` — situações anômalas que não impedem a execução
- `ctx.error()` — antes de relançar exceções de I/O da OpenF1
- `extra={...}` para metadados estruturados (ex.: `session_key`, `duration_ms`)

Níveis disponíveis no FastMCP: `ctx.debug()`, `ctx.info()`, `ctx.warning()`,
`ctx.error()`.

## 5. Níveis de severidade (RFC 5424)

| Nível | Uso no projeto |
|---|---|
| `debug` | Entrada/saída de funções, payloads (sem dados sensíveis) |
| `info` | Progresso de operações, chamadas à OpenF1 concluídas |
| `warning` | Respostas vazias da API, parâmetros fora do esperado |
| `error` | Falhas de I/O, timeouts, erros operacionais |
| `critical`+ | Falhas que impedem o servidor de operar |

## 6. Regras de segurança (obrigatórias)

- **Nunca** logar credenciais, tokens ou secrets
- **Nunca** logar dados pessoais identificáveis
- Não expor detalhes internos do sistema que auxiliem ataques
- Rate limit em logs dentro de loops (agregar, não logar por item)
- Validar/sanitizar dados antes de incluí-los em `extra` ou mensagens

## 7. Roadmap

| Fase | Ação |
|---|---|
| Fase 1 (atual) | Camada 1 (stderr) implementada + Camada 2 moderada nas tools |
| Fase futura | Avaliar OpenTelemetry para métricas/traces das chamadas à OpenF1 |
| Contínuo | Remover usos de `notifications/message` se a spec remover o recurso |
