# Cache Strategy — MCP Sport (F1)

> Documento **canônico** da estratégia de cache de respostas. Toda decisão
> sobre cache deve seguir o descrito aqui; mudanças de comportamento exigem
> atualização deste documento no mesmo commit.
>
> Documentos relacionados:
> - `docs/Technical_Reference.md` — stack e fontes oficiais
> - `docs/Architectural_Design.md` — arquitetura geral e estrutura de pacotes
> - `docs/Logging_Strategy.md` — padrão de logs (inclui eventos de cache)
> - `tasks/04_cache.md` — histórico de planejamento, spike e validação

## 1. Objetivo e escopo

Reduzir latência (~1–3s por chamada à OpenF1) e carga na API pública
cacheando **respostas de tools MCP**. O cache é:

- **Transversal:** nenhuma camada (tools, services, validators, client)
  conhece sua existência
- **Sem código próprio:** usa exclusivamente o middleware oficial do FastMCP
- **Configurável por ambiente:** ligar/desligar e trocar backend sem alterar
  código

Fora de escopo: cache distribuído (Redis), invalidação manual, cache de
resources e prompts. O servidor expõe resources `ui://` (HTML das views);
eles não passam pelo `ResponseCachingMiddleware`.

## 2. Mecanismo oficial

Implementação: `fastmcp.server.middleware.caching.ResponseCachingMiddleware`
([documentação oficial](https://gofastmcp.com/servers/middleware#caching)).

### 2.1 Chave de cache

Derivada de: **método + argumentos + versão do componente + token de acesso
do caller**. Consequências inequívocas para este projeto:

1. Argumentos diferentes → chaves diferentes → entradas independentes
   (ex.: `speed_min=300` e `speed_min=310` cacheiam separadamente)
2. Transporte stdio (nosso caso): todos os callers dividem uma **partição
   anônima única** — não há isolamento por usuário, nem necessidade dele
3. Nossas tools são **funções puras dos argumentos** (nada depende de
   headers ou estado de sessão), portanto o cache é semanticamente seguro

### 2.2 Garantias do middleware (verificadas no código-fonte do FastMCP 4.0.5)

| Comportamento | Garantia |
|---|---|
| Erros (`is_error=True`) | **Nunca cacheados** — falhas transitórias da OpenF1 não ficam presas pelo TTL |
| Itens > 1 MB (`max_item_size` default) | **Não cacheados** (falha silenciosa). Telemetria de sessão inteira fica de fora; respostas fatiadas (task 03) cacheiam normalmente |
| TTL default | 1h para tools; 5min para listas — **sempre sobrescrevemos** (seção 4) |
| Settings (`CallToolSettings` etc.) | `TypedDict` com `ttl`, `enabled`, `included_tools`, `excluded_tools` |

### 2.3 Padrão multi-instância (decisão arquitetural central)

O FastMCP define TTL **por operação**, não por tool. Para obter TTL por
grupo de tools, registramos **uma instância do middleware por grupo**, com
listas `included_tools` **disjuntas**.

Funcionamento garantido pela fonte: uma tool fora do `included_tools` de uma
instância é passada adiante (`call_next`) **sem ser cacheada por ela**,
caindo na próxima instância da cadeia. Como as listas são disjuntas, cada
tool é cacheada por exatamente uma instância, com o TTL do seu grupo.

```
tools/call: get_laps(...)
  │
  ▼
instância 1 (24h: meetings, sessions)   → não inclui → call_next
instância 2 (6h: results, grid)         → não inclui → call_next
instância 3 (1h: laps, car_data, ...)   → INCLUI:
  ├─ HIT  → retorna ToolResult cacheado (a tool nem executa)
  └─ MISS → executa → se sucesso e ≤ 1 MB → armazena com TTL do grupo
```

## 3. Estrutura

Ponto de encaixe único no código:

```
src/mcp_sport/
├── cache_config.py     # TUDO sobre cache vive aqui
└── server.py           # única linha de integração: setup_cache(mcp)
```

`cache_config.py` tem exatamente três blocos:

| Bloco | Responsabilidade |
|---|---|
| `_TOOL_TTL_GROUPS` | Dados: pares `(ttl_segundos, [tools])`, disjuntos |
| `_build_storage()` | Backend via env vars (`None` = memória, padrão do FastMCP) |
| `setup_cache(mcp)` | Master switch + registra 1 middleware por grupo + 1 para `tools/list` |

## 4. Tabela canônica de TTLs

Critério de grupo: **volatilidade do dado**, não a tool em si.

| Grupo | TTL | Tools | Justificativa |
|---|---|---|---|
| Navegação | **24h** | `get_meetings`, `get_sessions` | Calendário histórico é imutável |
| Resultados oficiais | **6h** | `get_session_results`, `get_starting_grid` | Publicados uma vez; janela cobre correções |
| Sessão/telemetria | **1h** | `get_drivers`, `get_laps`, `get_pit_stops`, `get_stints`, `get_positions`, `get_race_control`, `get_overtakes`, `get_team_radio`, `get_car_data`, `get_location`, `get_drivers_championship`, `get_teams_championship` | Imutáveis após a sessão; telemetria é o maior ganho (payload grande) |
| Clima | **30min** | `get_weather` | Atualiza por minuto durante sessão |
| Tempo real | **30s** | `get_intervals` | Atualiza a cada ~4s em corridas ao vivo |
| `tools/list` | **30s** | (operação de listagem) | Handshake do cliente não rebuilda a cada conexão |
| Views (exceção) | — | `get_drivers_championship_view`, `get_race_replay_view` | Fora de `_TOOL_TTL_GROUPS`. Chamam `services/` direto, então não reaproveitam o cache das tools de dados, e o resultado é um payload composto regenerado a cada chamada |

**Regra obrigatória:** toda nova tool de dados deve ser adicionada a
exatamente um grupo em `_TOOL_TTL_GROUPS` no mesmo PR que a registra em
`server.py`. View tools (`apps/`) ficam de fora, pela exceção da tabela.

## 5. Configuração (variáveis de ambiente)

| Variável | Valores | Default | Efeito |
|---|---|---|---|
| `MCP_SPORT_CACHE_ENABLED` | `true`/`1`/`yes` (case-insensitive); qualquer outro = off | `true` | Master switch. Off = servidor idêntico ao comportamento sem cache |
| `MCP_SPORT_CACHE_BACKEND` | `memory` / `file` | `memory` | Backend de armazenamento |
| `MCP_SPORT_CACHE_DIR` | path | `.cache/mcp_sport` | Diretório do backend `file` (ignorado no git) |

Segue o precedente de `MCP_SPORT_LOG_LEVEL` (`Logging_Strategy.md`):
configuração de ambiente, nunca de código.

## 6. Storage backends

Via `py-key-value-aio` (já transitiva do FastMCP 4.0.5 — **não** adicionar
ao `pyproject.toml` enquanto for assim).

| Backend | Quando usar | Observações |
|---|---|---|
| `memory` (default) | Uso local (Cursor, Inspector) | Perde no restart do servidor — aceitável, cache é otimização, não estado |
| `file` (`FileTreeStore`) | Persistir entre restarts | **Obrigatório** passar as strategies de sanitização V1 (sem elas, chaves com caracteres especiais corrompem paths) — já implementado em `_build_storage()` |
| Redis | Deploy distribuído | **Fora de escopo** nesta fase; requer extra `py-key-value-aio[redis]` |

## 7. A ressalva do `"latest"`

A chave de cache usa os **argumentos literais**. `session_key="latest"` é
uma janela móvel: durante uma sessão ao vivo, uma resposta cacheada pode
ficar desatualizada até o limite do TTL do grupo.

**Decisão canônica (opção híbrida, task 04 seção 4.1):** TTLs longos são
mantidos, e as docstrings das tools sensíveis a dados ao vivo
(`get_car_data`, `get_location`, `get_positions`, `get_weather`) orientam a
IA a **resolver `"latest"` → `session_key` concreto via `get_sessions`**
antes de análises. Toda nova tool que aceitar `"latest"` e tiver TTL ≥ 30min
deve carregar a mesma nota na docstring.

## 8. Observabilidade

Logger `mcp_sport.cache` (filho do root, segue `Logging_Strategy.md`):

| Evento | Quando |
|---|---|
| `event=cache_group ttl_seconds=N tools=...` | Boot: um por grupo registrado |
| `event=cache_enabled backend=memory\|file` | Boot: cache ativo |
| `event=cache_disabled` | Boot: master switch off |

**Como verificar hit/miss em runtime:** o par
`openf1_request`/`openf1_response` (logger `mcp_sport.openf1`) só aparece em
**miss**. Duas chamadas idênticas → apenas um `openf1_request`. Este é o
teste canônico de sanidade do cache (executado na validação da task 04).

## 9. Como alterar (procedimentos)

| Mudança | Onde | Cuidado |
|---|---|---|
| Nova tool de dados | `_TOOL_TTL_GROUPS` | Exatamente um grupo; docstring com nota de cache se aceitar `"latest"`. View tools ficam de fora (seção 4) |
| Novo TTL | Constante + tupla em `_TOOL_TTL_GROUPS` | Atualizar a tabela da seção 4 **no mesmo commit** |
| Trocar backend padrão | `_build_storage()` | Manter `None` = memória como caminho zero-config |
| Desligar temporariamente | env var, **nunca** removendo código | `MCP_SPORT_CACHE_ENABLED=false` |

## 10. Referências oficiais

- [FastMCP — Middleware (Caching)](https://gofastmcp.com/servers/middleware)
- [FastMCP — Storage Backends](https://gofastmcp.com/servers/storage-backends)
- [py-key-value-aio (GitHub)](https://github.com/strawgate/py-key-value) —
  implementação dos backends
- Código-fonte consultado: `fastmcp.server.middleware.caching` (FastMCP
  4.0.5, instalado no `.venv` do projeto)
