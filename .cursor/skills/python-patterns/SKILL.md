---
name: python-patterns
description: Python-specific design patterns and best practices adapted to this project's stack (Python 3.13+, FastMCP, Pydantic, OpenF1 API). Covers protocols, Pydantic models, context managers, decorators, async/await, modern type hints, dependency injection, package organization, and error handling. Use when writing, reviewing, or refactoring Python code in this project, designing tools, structuring modules, or applying Pythonic patterns.
---

# Python Patterns

Padrões Python idiomáticos **adaptados à stack do projeto** (ver
`docs/Technical_Reference.md`). Em caso de conflito entre um padrão aqui e a
doc canônica, a doc canônica vence.

## Regras do projeto (prioridade máxima)

- **Código sempre em inglês:** identificadores, docstrings, comentários e
  mensagens de log. **Documentação em `docs/` e `tasks/` é sempre em português.**
  Docstrings de tools MCP são sempre em inglês (são a interface da tool com o LLM).
- **Modelos de dados: sempre Pydantic**, nunca `@dataclass` para DTOs/schemas
  de tools ou respostas da OpenF1.
- **Type hints modernos (3.13+):** `list[str]`, `dict[str, Any]`, `X | None`.
  Proibido `typing.List`, `typing.Dict`, `Optional`.
- **Tools MCP:** sempre `@mcp.tool()` do FastMCP.
- Chamadas HTTP à OpenF1: base URL `https://api.openf1.org/v1`.

## Pydantic como camada de dados

Substitui dataclasses como DTO/Value Object, com validação embutida:

```python
from pydantic import BaseModel, Field

class Driver(BaseModel):
    """Modelo de piloto (resposta OpenF1)."""
    driver_number: int
    full_name: str
    team_name: str | None = None
    session_key: int

class PitStopQuery(BaseModel):
    """Schema de entrada de uma tool."""
    session_key: int
    max_stop_duration: float = Field(gt=0, description="Duração máxima em segundos")
```

- `Field(gt=..., le=..., pattern=...)` para validação declarativa
- `model_config = ConfigDict(frozen=True)` para imutabilidade
- Docstring do modelo vira descrição do schema da tool no MCP

## Protocol (structural subtyping)

Para contratos desacoplados (ex.: cliente HTTP da OpenF1, cache):

```python
from typing import Protocol

class F1DataClient(Protocol):
    def get_drivers(self, session_key: int) -> list[Driver]: ...
    def get_pit_stops(self, session_key: int) -> list[dict]: ...

# Qualquer classe com esses métodos satisfaz o protocolo — sem herança
```

**Benefícios:** type safety sem herança, fácil mock em testes.

## Async/Await

OpenF1 é I/O-bound — prefira async nas tools quando o FastMCP suportar:

```python
import asyncio
import httpx

async def fetch_json(url: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

async def fetch_multiple(urls: list[str]) -> list[list[dict]]:
    """Execução concorrente de várias chamadas à API."""
    return await asyncio.gather(*(fetch_json(u) for u in urls))
```

**Regra de ouro:** I/O (rede, disco) → async. CPU-bound ou script simples → sync.
Não misture `urllib` síncrono com código async (bloqueia o event loop).

## Context Managers

Para gerenciamento de recursos (conexões, sessões HTTP):

```python
from contextlib import contextmanager
from collections.abc import Generator

@contextmanager
def http_session() -> Generator[httpx.Client, None, None]:
    client = httpx.Client(base_url="https://api.openf1.org/v1", timeout=10)
    try:
        yield client
    finally:
        client.close()
```

## Type Hints avançados

```python
from typing import TypeVar, ParamSpec
from collections.abc import Callable
from functools import wraps

T = TypeVar("T")
P = ParamSpec("P")

def log_call(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator type-safe que preserva a assinatura."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper
```

## Dependency Injection

Constructor injection — facilita testes e troca de implementação:

```python
class F1Service:
    def __init__(self, client: F1DataClient):
        self.client = client

    def get_driver(self, driver_number: int, session_key: int) -> Driver | None:
        drivers = self.client.get_drivers(session_key)
        return next((d for d in drivers if d.driver_number == driver_number), None)
```

## Error Handling

Hierarquia de exceções de domínio:

```python
class MCPSportError(Exception):
    """Exceção base do projeto."""

class OpenF1APIError(MCPSportError):
    """Falha na chamada à OpenF1 API."""
    def __init__(self, url: str, status_code: int):
        self.url = url
        self.status_code = status_code
        super().__init__(f"OpenF1 request failed ({status_code}): {url}")

class SessionNotFoundError(MCPSportError):
    """Session key não encontrada."""
    def __init__(self, session_key: int):
        super().__init__(f"Session {session_key} not found")
```

- Tools devem capturar exceções de I/O e retornar erro legível ao cliente MCP
- Nunca engolir exceções silenciosamente (`except: pass`)

## Package Organization

Estrutura alvo conforme o projeto cresce:

```
src/mcp_sport/
├── __init__.py
├── server.py            # Instância FastMCP e registro de tools
├── tools/               # Tools MCP por domínio
│   ├── drivers.py
│   └── pit_stops.py
├── models/              # Modelos Pydantic (schemas OpenF1)
│   └── f1.py
├── services/            # Lógica de aplicação
│   └── f1_service.py
└── clients/             # Cliente HTTP da OpenF1
    └── openf1.py
```

## Quando aplicar

- Criar novas tools MCP ou módulos
- Modelar respostas da OpenF1
- Refatorar código sync → async
- Revisar type hints e tratamento de erros
