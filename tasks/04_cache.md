# Task 04 — Cache de respostas (ResponseCachingMiddleware)

> **Status:** Concluída ✅ (20/09/2026)
> **Fase:** 3
> **Referências canônicas:** `docs/Architectural_Design.md`,
> `docs/Technical_Reference.md`, `docs/Logging_Strategy.md`
> **Fontes oficiais:**
> [FastMCP — Middleware](https://gofastmcp.com/servers/middleware) (seção Caching),
> [FastMCP — Storage Backends](https://gofastmcp.com/servers/storage-backends)
> **Origem:** pesquisa de cache solicitada pelo usuário (20/09/2026) e item
> "Cache de respostas" do `Architectural_Design.md`, seção 8

## 1. Objetivo

Adicionar cache de respostas das tools usando o middleware **oficial do
FastMCP** (`ResponseCachingMiddleware`), reduzindo latência (nossos logs
mostram ~1–3s por chamada à OpenF1) e carga na API pública — sem escrever
lógica de cache própria.

Ganhos esperados por caso de uso:

| Cenário | Sem cache | Com cache |
|---|---|---|
| IA encadeia tools na mesma sessão (sessions → laps → car_data) | 3 requests à API | 2º+ acessos instantâneos |
| Dashboard MCP App interativo (futuro) chama tools a cada clique | 1 request por clique | Absorvido pelo cache |
| Mesma pergunta refeita em outra conversa | Nova request | Hit (se TTL válido) |

## 2. Mecanismo oficial (pesquisa na documentação)

### 2.1 `ResponseCachingMiddleware`

```python
from fastmcp.server.middleware.caching import (
    ResponseCachingMiddleware,
    CallToolSettings,
    ListToolsSettings,
)

mcp.add_middleware(ResponseCachingMiddleware(
    list_tools_settings=ListToolsSettings(ttl=30),
    call_tool_settings=CallToolSettings(included_tools=["expensive_tool"]),
))
```

Fatores relevantes extraídos da documentação oficial:

- **Granularidade por operação:** settings independentes para
  `on_call_tool`, `on_list_tools`, `on_read_resource`, `on_list_resources`,
  `on_list_prompts`, `on_get_prompt`
- **Config por settings class:** `enabled`, `ttl` (segundos),
  `included_*` / `excluded_*` (whitelist/blacklist de itens)
- **Chave do cache:** método + **argumentos** + versão do componente +
  token de acesso do caller. Como cada combinação de filtros gera chave
  distinta, os operadores da task 03 (`speed_min=300` vs `speed_min=310`)
  cacheiam separadamente — comportamento correto
- **stdio (nosso transporte):** callers não autenticados dividem uma única
  partição anônima — sem risco de vazamento entre usuários
- **Alerta oficial:** dados dependentes de contexto fora dos argumentos
  (headers, estado de sessão HTTP) não entram na chave. **Não se aplica a
  nós:** nossas tools são funções puras dos argumentos

### 2.2 Storage backends (via `py-key-value-aio`)

| Backend | Persistência | Multi-processo | Quando usar |
|---|---|---|---|
| `MemoryStore` (padrão) | ❌ perde no restart | ❌ | Desenvolvimento, uso local no Cursor |
| `FileTreeStore` | ✅ disco (1 JSON por chave) | ❌ | Produção single-server |
| `RedisStore` | ✅ | ✅ | Deploy distribuído (fase futura) |

Notas da documentação:

- `FileTreeStore` **exige** strategies de sanitização
  (`FileTreeV1KeySanitizationStrategy` +
  `FileTreeV1CollectionSanitizationStrategy`) — sem elas, chaves com
  caracteres especiais quebram o filesystem
- `RedisStore` requer dependência opcional `pip install 'py-key-value-aio[redis]'`
- **Verificar na implementação:** se `py-key-value-aio` já vem como
  dependência transitiva do FastMCP 4.x ou precisa ser adicionada ao
  `pyproject.toml` (registrar no `Technical_Reference.md` se entrar)

## 3. Arquitetura no nosso projeto

Ponto de encaixe único: `server.py` — nenhuma camada existente muda.

```
server.py
  │
  ├─ mcp = FastMCP("mcp-sport")
  ├─ mcp.add_middleware(ResponseCachingMiddleware(...))   ← NOVO
  └─ registro das 18 tools (inalterado)
```

Princípios preservados:

- **Zero invasão:** tools, services, validators e client não sabem que o
  cache existe (middleware é transversal por design)
- **Configuração por env var:** nível/TTLs ajustáveis sem alterar código,
  seguindo o precedente de `MCP_SPORT_LOG_LEVEL` (ver `Logging_Strategy.md`)
- **Logs:** o middleware emite logs próprios; verificar logger utilizado e
  alinhar ao padrão `mcp_sport.<subsistema>` se necessário

## 4. Estratégia de TTL por tool (proposta)

Critério: **volatilidade do dado**, não da tool. Dados históricos da OpenF1
são imutáveis após publicação; o risco está em consultas sobre sessões
**em andamento** — sobretudo via `session_key="latest"`, que é uma janela
móvel.

| Grupo | Tools | TTL proposto | Justificativa |
|---|---|---|---|
| Navegação histórica | `get_meetings`, `get_sessions` | 24h | Calendário de anos passados é imutável; ano corrente muda raramente |
| Resultados oficiais | `get_session_results`, `get_starting_grid` | 6h | Publicados uma vez; pequena janela cobre correções |
| Dados de sessão encerrada | `get_drivers`, `get_laps`, `get_pit_stops`, `get_stints`, `get_positions`, `get_race_control`, `get_overtakes`, `get_team_radio` | 1h | Imutáveis após a sessão; TTL moderado cobre sessões recentes |
| Telemetria | `get_car_data`, `get_location` | 1h | Idem; payload grande = maior ganho de cache |
| Clima | `get_weather` | 30min | Atualizado por minuto durante a sessão |
| Tempo real | `get_intervals` | 30s | Atualizado a cada ~4s em corridas ao vivo |
| Campeonatos (beta) | `get_drivers_championship`, `get_teams_championship` | 1h | Só muda após corridas |
| Infra | `on_list_tools` | 30s | Barato; evita rebuild a cada handshake |

### 4.1 ⚠️ O problema do `"latest"`

A chave de cache inclui os **argumentos literais**. `session_key="latest"`
durante um fim de semana de corrida ao vivo aponta para dados que mudam a
cada minuto — com TTL de 1h, a IA receberia dados **stale** (ex: classificação
da volta 20 quando a corrida está na volta 50).

Opções (decidir na implementação):

| Opção | Como | Trade-off |
|---|---|---|
| **A. TTL global curto** | Todas as tools com TTL ≤ 60s | Simples, mas desperdiça o ganho para dados históricos |
| **B. TTL longo + documentar** | Docstrings alertam que `"latest"` pode vir cacheado | Risco de resposta stale silenciosa |
| **C. Híbrido (recomendada)** | TTLs da tabela acima; docstrings das tools orientam a IA a **resolver `"latest"` → `session_key` concreto** via `get_sessions` antes de consultas analíticas | Máximo aproveitamento; depende de disciplina da IA (docstring) |

A opção C é natural porque a IA já precisa descobrir `session_key`s para
a maioria das consultas — `"latest"` é atalho, não norma.

## 5. Decisões tomadas na implementação

1. **Backend inicial:** `MemoryStore` (padrão, zero config). `FileTreeStore`
   disponível via `MCP_SPORT_CACHE_BACKEND=file` + `MCP_SPORT_CACHE_DIR`
   (default `.cache/mcp_sport`, adicionado ao `.gitignore`)
2. **Master switch:** `MCP_SPORT_CACHE_ENABLED` (default: `true`) —
   validado: com `false` o servidor sobe com `event=cache_disabled`
3. **TTLs:** módulo dedicado `cache_config.py` com a tabela da seção 4
4. **Dependência:** `py-key-value-aio` **já vem com o FastMCP 4.0.5** —
   nenhuma dependência nova no `pyproject.toml`

### 5.1 Descobertas do código-fonte do FastMCP 4.0.5 (levantamento real)

Lendo a fonte de `fastmcp.server.middleware.caching`:

- **Settings são `TypedDict`** (`ttl`, `enabled`, `included_tools`,
  `excluded_tools`) — não dataclasses nem modelos Pydantic
- **TTL é por operação, não por tool:** `CallToolSettings(ttl=...)` vale para
  todas as tools daquela instância. TTL por grupo de tools é obtido com
  **múltiplas instâncias do middleware** com `included_tools` disjuntos —
  uma tool que não casa com a lista é passada adiante (`call_next`) sem
  cachear, então cada tool é cacheada por exatamente uma instância
- **Erros nunca são cacheados:** resultados com `is_error=True` passam
  direto — uma falha transitória da OpenF1 não fica "presa" pelo TTL
- **`max_item_size` padrão: 1 MB** — itens maiores falham silenciosamente
  (não cacheiam). Consequência prática: telemetria de sessão inteira
  (>1 MB) nunca é cacheada; respostas fatiadas pelos operadores da task 03
  (dezenas/centenas de amostras) cacheiam normalmente. **Comportamento
  desejável** — mantido o default
- **TTL default do middleware:** 1h para tools/resources, 5min para listas

## 6. Relação com as outras fases

- **Task 03 (operadores) — concluída, pré-requisito:** argumentos entram na
  chave de cache; consultas fatiadas (`speed_min=300`) cacheiam de forma
  independente e correta
- **MCP Apps (futuro):** o dashboard interativo chama tools a cada interação
  do usuário — o cache é o que torna essa interatividade viável sem martelar
  a OpenF1

## 7. Critérios de aceite

- [x] `ResponseCachingMiddleware` registrado em `server.py` com TTLs por
      grupo de tools (seção 4) — via `cache_config.py::setup_cache`,
      uma instância do middleware por grupo (ver seção 5.1)
- [x] Config via env vars: `MCP_SPORT_CACHE_ENABLED`,
      `MCP_SPORT_CACHE_BACKEND`, `MCP_SPORT_CACHE_DIR`
- [x] Dependência verificada: `py-key-value-aio` já é transitiva do
      FastMCP 4.0.5 — nada a adicionar
- [x] `.gitignore` atualizado (`.cache/`) para o backend `file`
- [x] Decisão sobre `"latest"` (seção 4.1): **opção C (híbrida)** — TTLs
      longos + nota nas docstrings das tools sensíveis a dados ao vivo
      (`get_car_data`, `get_location`, `get_positions`, `get_weather`)
      orientando a resolver `"latest"` → `session_key` concreto
- [x] Validação empírica (20/09/2026, via `fastmcp.Client` in-process):

  | Chamada | Resultado | Requests à API |
  |---|---|---|
  | `get_laps` voltas 8–10 (1ª vez) | 3 voltas, 913ms | 1 (miss) |
  | `get_laps` voltas 8–10 (2ª vez, idêntica) | 3 voltas, instantâneo | **1 (HIT — sem nova request)** |
  | `get_laps` voltas 8–12 (args diferentes) | 5 voltas, 710ms | 2 (miss — chave distinta) |

- [x] `Architectural_Design.md` seção 8 atualizada (cache: Implementado)
- [ ] Validação no Cursor: **pendente reload do servidor MCP** para carregar
      o middleware (servidor em stdio roda o código do momento do start)

## 8. Fora de escopo

- Redis / deploy distribuído (fase futura, junto com transporte HTTP)
- Cache de listas de tools/resources além do TTL padrão
- Invalidação manual/administrativa de cache (a API não oferece webhooks;
  TTL é o único mecanismo)
- Rate limiting (middleware oficial existe —
  `fastmcp.server.middleware.rate_limiting` — mas protege o **nosso**
  servidor de clientes, não se aplica ao nosso cenário de cliente da OpenF1)
