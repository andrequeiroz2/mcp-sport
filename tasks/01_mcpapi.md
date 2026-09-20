# Task 01 — Implementação da API OpenF1 no MCP (FastMCP)

> **Status:** Concluída ✅
> **Fase:** 1
> **Referências canônicas:** `docs/Technical_Reference.md`, `docs/Logging_Strategy.md`
> **Fonte de dados:** [OpenF1 API](https://openf1.org/docs/) — base URL `https://api.openf1.org/v1`

## 1. Objetivo

Implementar a primeira versão real do servidor MCP de Fórmula 1, substituindo os
exemplos de teste em `src/mcp_sport/mcp_f1.py`, começando pela tool
`get_drivers` (endpoint `[/drivers](https://openf1.org/docs/#drivers)`) como
**padrão de referência** para todas as tools futuras.

## 2. Avaliação do contexto e decisões

### 2.1 Decisões aprovadas


| #   | Decisão                                                                                                          | Justificativa                                                                                                                         |
| --- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | **Tool MCP limpa (thin layer)** — a função da tool só orquestra: valida entrada → chama serviço → retorna modelo | Docstring vira descrição da tool para o LLM; corpo curto facilita leitura e manutenção                                                |
| D2  | **Pacote de schemas por tool** (`schemas/`) — tipagem de entrada e saída em Pydantic, um módulo por tool         | Conforme `docs/Technical_Reference.md` (Pydantic é a camada de validação); schema de entrada vira o `inputSchema` JSON da tool no MCP |
| D3  | **Pacote de validações por tool** (`validators/`) — regras de negócio e de operação separadas da tipagem         | Pydantic valida *forma*; validators validam *semântica* (ex.: `session_key` vs `meeting_key`, combinações de filtros)                 |
| D4  | **Cliente HTTP único** (`clients/openf1.py`) — montagem de URL, query params e parsing centralizados             | Elimina duplicação de `urlopen` + `json.loads` em cada tool (problema do script atual)                                                |
| D5  | **Docstring padronizada** (template da seção 4) espelhando as melhores práticas MCP                              | A docstring é a interface do LLM com a tool: deve cobrir entrada, tipos, obrigatoriedade, limites, validações, saída e conversões     |
| D6  | **Logging nas camadas** conforme `docs/Logging_Strategy.md`                                                      | `mcp_sport.tools` nas tools, `mcp_sport.openf1` no cliente HTTP                                                                       |


### 2.2 Fatos relevantes da API (extraídos da doc oficial e do dump real)

- **Todos os parâmetros de filtro são opcionais** — `/drivers` sem filtro retorna
o histórico completo (~500 KB no dump analisado). A tool deve incentivar
filtros para evitar respostas gigantes ao LLM.
- `session_key` e `meeting_key` aceitam o valor especial `**latest**` (sessão /
meeting atual ou mais recente) — tipo `int | str` na entrada, com validação.
- A API permite filtrar por **qualquer atributo** (exceto arrays), com operadores
na query (`>=`, `<=`, etc.). Nesta task, apenas filtros de igualdade.
- Campo `**country_code` está depreciado** (remoção ao fim da temporada 2026) —
manter no modelo como opcional, marcado como deprecated.
- Campos **anuláveis** na prática: `headshot_url`, `country_code`, `team_colour`,
`first_name`, `last_name`, `broadcast_name` — todos `str | None` na saída.
- `team_colour` é hexadecimal **RRGGBB sem `#`** (ex.: `"3671C6"`).
- Dados históricos (2023+) são gratuitos e sem autenticação.

## 3. Arquitetura alvo

```
src/mcp_sport/
├── __init__.py
├── server.py                  # Instância FastMCP + registro das tools
├── logging_config.py          # (já existe)
├── clients/
│   ├── __init__.py
│   └── openf1.py              # Cliente HTTP: get(path, params) -> list[dict]
├── schemas/
│   ├── __init__.py
│   └── drivers.py             # DriversInput (entrada) + Driver (saída)
├── validators/
│   ├── __init__.py
│   └── drivers.py             # Validações de operação/negócio
├── services/
│   ├── __init__.py
│   └── drivers.py             # Orquestra cliente + validadores + conversão
└── tools/
    ├── __init__.py
    └── drivers.py             # Tool MCP limpa (thin layer)
```

**Fluxo de uma chamada:**

```
LLM → tool (tools/drivers.py)
      → valida entrada (Pydantic via assinatura + validators/drivers.py)
      → services/drivers.py → clients/openf1.py → OpenF1 API
      → converte dicts → list[Driver] (Pydantic)
      → retorna ao LLM
```

## 4. Padrão de docstring das tools

**Docstrings são sempre em inglês** — elas são a interface da tool com o LLM
(viram a descrição da tool no protocolo MCP) e seguem a convenção de código do
projeto (código em inglês; apenas documentação em `docs/` e `tasks/` é em
português).

Template obrigatório:

```python
@mcp.tool()
def get_drivers(...) -> list[Driver]:
    """<Uma linha: o que a tool faz, orientada à ação>.

    Args:
        <param>: <tipo> — <obrigatório/opcional>, <limites/faixa>,
            <o que representa>. <valor especial, se houver>.

    Validations:
        - <regra de negócio/operação aplicada antes da chamada à API>.

    Returns:
        list[Driver]: <descrição do conteúdo>. Campos anuláveis: <lista>.
        <Conversões aplicadas sobre a resposta crua da API, se houver>.
    """
```

Regras:

- Primeira linha curta e orientada à ação (é o que o LLM lê primeiro)
- `Args` com tipo, obrigatoriedade, limites e significado de cada campo
- `Validations` lista regras além da tipagem (ex.: valor especial `latest`)
- `Returns` descreve a saída, campos anuláveis e conversões
- Sem prosa desnecessária — cada linha deve informar algo que o schema JSON
da tool não expressa sozinho

## 5. Especificação da tool `get_drivers`

### 5.1 Entrada (`DriversInput` — `schemas/drivers.py`)


| Campo           | Tipo        | Obrigatório | Limites / validação                                |
| --------------- | ----------- | ----------- | -------------------------------------------------- |
| `session_key`   | `int | str` | Não         | `int > 0` ou literal `"latest"`                    |
| `meeting_key`   | `int | str` | Não         | `int > 0` ou literal `"latest"`                    |
| `driver_number` | `int`       | Não         | `1–99` (números de temporada F1)                   |
| `first_name`    | `str`       | Não         | `1–100` chars, sem vazio                           |
| `last_name`     | `str`       | Não         | `1–100` chars, sem vazio                           |
| `full_name`     | `str`       | Não         | `1–200` chars                                      |
| `name_acronym`  | `str`       | Não         | exatamente 3 letras, normalizado para maiúsculas   |
| `team_name`     | `str`       | Não         | `1–100` chars                                      |
| `country_code`  | `str`       | Não         | 3 letras (ISO), maiúsculas — **deprecated na API** |


**Validações de operação (`validators/drivers.py`):**

- `session_key`/`meeting_key`: aceitar apenas `int` positivo ou `"latest"`
(case-insensitive, normalizado para minúsculas)
- Ao menos **um filtro** deve ser informado (proteção contra resposta de ~500 KB)
- `name_acronym`: validar `^[A-Z]{3}$` após normalização

### 5.2 Saída (`Driver` — `schemas/drivers.py`)


| Campo            | Tipo  | Anulável | Observação                           |
| ---------------- | ----- | -------- | ------------------------------------ |
| `meeting_key`    | `int` | Não      |                                      |
| `session_key`    | `int` | Não      |                                      |
| `driver_number`  | `int` | Não      |                                      |
| `broadcast_name` | `str` | Sim      | Nome exibido na TV                   |
| `full_name`      | `str` | Sim      |                                      |
| `first_name`     | `str` | Sim      |                                      |
| `last_name`      | `str` | Sim      |                                      |
| `name_acronym`   | `str` | Sim      | 3 letras                             |
| `team_name`      | `str` | Sim      |                                      |
| `team_colour`    | `str` | Sim      | Hex RRGGBB sem `#`                   |
| `headshot_url`   | `str` | Sim      | URL da foto                          |
| `country_code`   | `str` | Sim      | **Deprecated** (remoção fim de 2026) |


**Conversões:** nenhuma transformação de valores nesta task — a conversão é
apenas `dict` (JSON cru) → `Driver` (Pydantic), com campos ausentes tratados
como `None`.

### 5.3 Cliente HTTP (`clients/openf1.py`)

- Função `get(path: str, params: dict) -> list[dict]`
- Base URL `https://api.openf1.org/v1` como constante
- Ignora params com valor `None`; serializa demais na query string
- Logs: `event=openf1_request` / `openf1_response` / `openf1_error`
(logger `mcp_sport.openf1`, conforme `docs/Logging_Strategy.md`)
- Exceções de I/O encapsuladas em `OpenF1APIError` (ver skill `python-patterns`)

## 6. Critérios de aceite

- [x] Estrutura de pacotes da seção 3 criada
- [x] `get_drivers` registrada e listada no MCP Inspector
- [x] Docstring segue o template da seção 4
- [x] Entrada validada por Pydantic + validators (testar: sem filtros → erro;
  ```
  `session_key="latest"` → aceito; `driver_number=0` → erro)
  ```
- [x] Saída tipada como `list[Driver]`
- [x] Logs em `stderr` nos eventos definidos; `stdout` intacto
- [x] Código e docstrings 100% em inglês; documentação (`docs/`, `tasks/`) em português
- [x] `mcp_f1.py` removido ou reduzido a alias de `server.py`

## 7. Fora de escopo (próximas tasks)

- Demais endpoints (sessions, meetings, laps, pit, position, ...)
- Filtros com operadores (`>=`, `<=`) e filtros temporais
- Async/httpx (avaliar quando houver múltiplas chamadas concorrentes)
- Cache de respostas
- Testes automatizados

