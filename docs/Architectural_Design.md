# Architectural Design — MCP Sport (F1)

> Documento **canônico de implementação**. Todo novo endpoint/tool deve seguir os
> padrões, estrutura e procedimentos descritos aqui. Em caso de dúvida, este
> documento prevalece sobre preferências pessoais; conflitos com as fontes
> oficiais são resolvidos conforme `docs/Technical_Reference.md`.
>
> Documentos relacionados:
> - `docs/Technical_Reference.md` — stack, versões e fontes oficiais
> - `docs/Logging_Strategy.md` — estratégia de logs
> - `docs/Cache_Strategy.md` — estratégia canônica de cache de respostas
> - `tasks/01_mcpapi.md` — primeira aplicação prática destes padrões (referência viva)

## 1. Princípios arquiteturais

1. **Tool MCP limpa (thin layer):** a função da tool apenas orquestra — monta o
   schema de entrada, delega ao service e retorna. Sem HTTP, sem validação de
   negócio, sem parsing.
2. **Separação forma vs. semântica:** Pydantic valida *forma* (tipos, faixas,
   tamanhos); validators validam *semântica* (regras de operação e negócio).
3. **Cliente HTTP único:** toda comunicação com a OpenF1 passa por
   `clients/openf1.py`. Nenhuma outra camada faz I/O de rede.
4. **A IA nunca vê o interior:** o LLM só conhece a assinatura da tool e sua
   docstring (convertidas em `inputSchema` JSON pelo FastMCP). Paths de
   endpoint, URLs e detalhes de implementação são internos e fixos em código.
5. **Falha segura e observável:** erros de rede viram exceções de domínio
   logadas; erros de validação retornam mensagens legíveis que a IA pode usar
   para se autocorrigir.
6. **Proteção contra respostas gigantes:** tools que consultam a OpenF1 exigem
   ao menos um filtro (resposta sem filtro pode chegar a ~500 KB).

## 2. Estrutura de pacotes

```
src/mcp_sport/
├── __init__.py
├── server.py                # Entrypoint canônico: instância FastMCP + registro das tools
├── cache_config.py          # Cache de respostas (ResponseCachingMiddleware, TTL por grupo)
├── exceptions.py            # Hierarquia de exceções de domínio
├── logging_config.py        # Logging em stderr (ver Logging_Strategy.md)
├── clients/
│   └── openf1.py            # Cliente HTTP único: get(path, params) -> list[dict]
├── schemas/
│   └── <recurso>.py         # Pydantic: <Recurso>Input (entrada) + modelos de saída
├── validators/
│   └── <recurso>.py         # Validações de operação/negócio por recurso
├── services/
│   ├── common.py             # build_params: mapeia campos amigáveis → chaves da API (operadores)
│   └── <recurso>.py         # Orquestração: validator → client → conversão
└── tools/
    └── <recurso>.py         # Tool MCP limpa + função register(mcp)
```

**Um módulo por recurso** em cada pacote (`drivers.py`, `laps.py`, `pit.py`...).
Recursos aqui correspondem aos endpoints da OpenF1.

## 3. Fluxo de uma chamada

```
LLM ──► tools/<recurso>.py        (assinatura tipada + docstring → inputSchema)
          │ monta <Recurso>Input (Pydantic valida forma)
          ▼
        services/<recurso>.py     (orquestra)
          │ validators/<recurso>.py  (valida semântica, normaliza valores)
          │ clients/openf1.py        (HTTP, path fixo no código)
          ▼
        OpenF1 API
          │
          ▼
        list[dict] cru ──► conversão para modelos Pydantic ──► retorno à LLM
```

Regras do fluxo:

- A tool **não** chama o cliente diretamente — sempre via service
- O service **não** define path dinâmico — path é literal fixo no código
- O validator **não** faz I/O — recebe e devolve o modelo de entrada
- O cliente **não** conhece regras de negócio — só HTTP, logs e erros de rede

## 4. Responsabilidades por camada

### 4.1 `tools/<recurso>.py`

- Assinatura **plana** (um parâmetro por filtro da API), com type hints
  completos e defaults `None` para opcionais
- Docstring no padrão da seção 5 (é a interface da IA — obrigatória e completa)
- Expõe `register(mcp: FastMCP) -> None`; `server.py` importa e registra
- Loga `event=tool_call` com os principais filtros (logger `mcp_sport.tools`)

### 4.2 `schemas/<recurso>.py`

- `<Recurso>Input`: filtros de entrada — **deve herdar de `BaseInput`**
  (`schemas/base.py`), que já provê `str_strip_whitespace` e a coerção de
  string vazia para `None` (clientes MCP enviam `""` para campos não
  preenchidos; string vazia significa "filtro ausente"). Nunca duplicar essa
  lógica nos schemas
- Campos com `Field()` — `ge/le`, `min_length/max_length`, `description`
- Modelo(s) de saída: campos anuláveis como `str | None = None`, alinhados à
  tabela de atributos da doc oficial da OpenF1
- Campos depreciados pela API: manter como opcionais e marcar na `description`

### 4.3 `validators/<recurso>.py`

- Função `validate_<recurso>_input(data) -> data`
- Regras semânticas: ao menos um filtro **com valor não-nulo** (checar valores,
  não `model_fields_set` — clientes podem enviar todos os campos como `null`),
  valores especiais (`"latest"`), normalizações (uppercase, trim), combinações
  de filtros
- Filtros de faixa: usar `validators/common.py::validate_range` (min ≤ max;
  igualdade não combina com faixa no mesmo campo) e `validate_date_range`
  (`date_from` < `date_to`, ISO 8601)
- Erros via `ToolValidationError` com mensagem legível para a IA

### 4.4 `services/<recurso>.py`

- Função pública por operação (ex.: `get_drivers(filters) -> list[Driver]`)
- Monta `params` via `services/common.py::build_params`, que inclui apenas
  campos efetivamente informados (`model_fields_set`) e traduz campos de
  faixa para chaves de operador da API usando a tabela `_OPERATOR_FIELDS`
  do próprio módulo (ex.: `speed_min → "speed>="`) — ver
  `tasks/03_operator_filters.md`, seção 3.4
- Converte a resposta crua em modelos Pydantic — única conversão permitida
  nesta fase (sem transformação de valores)

### 4.5 `clients/openf1.py`

- `get(path: str, params: dict) -> list[dict]` — único ponto de I/O
- Ignora params `None`; timeout de 10s; base URL como constante
- Serialização própria (`_build_query`): a OpenF1 faz parsing *raw* da query
  e **não decodifica chaves** — sufixos de operador (`>`, `>=`, `<`, `<=`)
  são enviados literais, concatenados ao valor sem separador `=` extra
- Encapsula `HTTPError`/`URLError`/`JSONDecodeError` em `OpenF1APIError`
- Logs `openf1_request`/`openf1_response`/`openf1_error` (logger
  `mcp_sport.openf1`)

### 4.6 `exceptions.py`

Hierarquia única de domínio:

| Exceção | Uso |
|---|---|
| `MCPSportError` | Base de todas |
| `OpenF1APIError` | Falhas de rede/HTTP/parsing na OpenF1 |
| `ToolValidationError` | Validação semântica de entrada (pré-API) |

## 5. Padrão de docstring das tools

**Sempre em inglês** — é parseada pelo FastMCP e injetada no `inputSchema` que
a IA recebe (tipos vêm dos type hints; semântica e limites vêm da docstring).

Template obrigatório:

```python
@mcp.tool()
def get_<recurso>(...) -> list[<Modelo>]:
    """<Uma linha: o que a tool faz, orientada à ação>.

    Args:
        <param>: <tipo> — <opcional/obrigatório>, <limites/faixa>,
            <o que representa>. <valores especiais, se houver>.

    Validations:
        - <regra semântica aplicada antes da chamada à API>.

    Returns:
        list[<Modelo>]: <descrição do conteúdo>. Campos anuláveis: <lista>.
        <Conversões aplicadas sobre a resposta crua, se houver>.
    """
```

Regras:

- Primeira linha curta e orientada à ação
- `Args` com tipo, obrigatoriedade, limites e significado — uma linha por campo
- `Validations` lista apenas regras **além** da tipagem
- `Returns` descreve conteúdo, campos anuláveis e conversões
- Sem prosa: cada linha informa algo que o JSON Schema não expressa sozinho

## 6. Convenções transversais

| Tema | Regra |
|---|---|
| Idioma | Código, docstrings, comentários e logs em **inglês**; `docs/` e `tasks/` em **português** |
| Type hints | Modernos (3.13+): `list[str]`, `X \| None`. Proibido `typing.List`, `Optional` |
| Modelos de dados | Sempre Pydantic; nunca `@dataclass` para DTOs/schemas |
| Logging | `stderr`, loggers `mcp_sport.<subsistema>` — ver `Logging_Strategy.md` |
| Segurança em logs | Sem credenciais, PII ou detalhes internos sensíveis |
| Entrypoint | Único e canônico: `server.py` |

## 7. Procedimento para adicionar um novo endpoint

Checklist obrigatório (copiar para a task correspondente):

```
- [ ] 1. Criar task em tasks/NN_<nome>.md com especificação do endpoint
        (campos, tipos, anuláveis, depreciações — conforme doc oficial OpenF1)
- [ ] 2. schemas/<recurso>.py: <Recurso>Input + modelo(s) de saída
- [ ] 3. validators/<recurso>.py: regras semânticas + normalizações
- [ ] 4. services/<recurso>.py: orquestração e conversão
- [ ] 5. tools/<recurso>.py: tool limpa com docstring no padrão da seção 5
- [ ] 6. server.py: registrar via <recurso>.register(mcp)
- [ ] 7. Validar: Pydantic rejeita inválidos; validator rejeita sem filtro;
        tool aparece no MCP Inspector; chamada real à API retorna modelos
- [ ] 8. Marcar critérios de aceite da task como concluídos
```

## 8. Decisões adiadas (reavaliar em fases futuras)

| Tema | Estado | Motivo do adiamento |
|---|---|---|
| Async/httpx | Adiado | `urllib` sync suficiente para chamadas únicas; reavaliar com concorrência |
| ~~Filtros com operadores (`>=`, `<=`) e temporais~~ | **Implementado (task 03)** | Sufixos `_min`/`_max` inclusivos + `date_from`/`date_to` em 9 tools |
| ~~Cache de respostas~~ | **Implementado (task 04)** | `ResponseCachingMiddleware` em `cache_config.py`, TTL por grupo de tools |
| Testes automatizados | Adiado | Validação manual via Inspector nesta fase |
| Restrição de `path` via `Literal` | **Descartado** | Falha segura via 404 + `OpenF1APIError` é suficiente |
| OpenTelemetry | Fase futura | Ver `Logging_Strategy.md`, seção 7 |
| FastAPI | Fase futura | Reservado no `Technical_Reference.md` |
| MCP Apps (dashboards HTML) | Fase futura | Extensão oficial MCP Apps + FastMCP Apps; depende das tasks 03/04 |
