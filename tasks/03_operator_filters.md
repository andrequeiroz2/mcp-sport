# Task 03 — Filtros com operadores (comparação e intervalos temporais)

> **Status:** Concluída ✅ (9 tools com operadores — ver seção 4)
> **Fase:** 3
> **Referências canônicas:** `docs/Architectural_Design.md`,
> `docs/Technical_Reference.md`, `docs/Logging_Strategy.md`
> **Fontes oficiais:** [OpenF1 API docs](https://openf1.org/docs/) —
> exemplos oficiais `car_data?...&speed>=315` e
> `location?...&date>2023-09-16T13:03:35.200&date<2023-09-16T13:03:35.800`
> **Origem:** observação dos testes reais do Lote E (task 02, seção 6) e item
> adiado em `Architectural_Design.md`, seção 8

## 1. Objetivo

Evoluir as tools de **filtros apenas de igualdade** para **filtros com
operadores**, usando o suporte nativo da OpenF1 API a operadores na query
string (`>=`, `<=`, `>`, `<`). O objetivo prático é permitir que a IA fatie
respostas grandes — sobretudo telemetria — em vez de receber milhares de
amostras:

- "me mostre só quando o Verstappen passou de 300 km/h" → `speed>=300`
- "só a volta 8 do Hamilton" → `date>=<início da volta 8>&date<<fim>`
- "voltas mais lentas que 1m40s" → `lap_duration>=100`

### 1.1 Problema que resolve (dados reais da task 02)

| Cenário | Hoje (igualdade) | Com operadores |
|---|---|---|
| Telemetria de 1 piloto em 1 sessão | 18–24 mil amostras | Centenas (fatiado por volta/velocidade) |
| Uma volta específica | Impossível isolar | `date` no intervalo da volta |
| Eventos de alta velocidade | Varredura manual pelo LLM | `speed>=315` na API |

## 2. Como a OpenF1 suporta operadores

A API aceita operadores **no nome do parâmetro** da query string:

```
GET /v1/car_data?driver_number=55&session_key=9159&speed>=315
GET /v1/location?session_key=9161&driver_number=81&date>2023-09-16T13:03:35.200&date<2023-09-16T13:03:35.800
```

Regras observadas na documentação oficial:

- Operadores aplicáveis: `>`, `>=`, `<`, `<=` (além da igualdade padrão)
- Aplicáveis a campos **numéricos** (`speed`, `rpm`, `lap_duration`,
  `position`, `lap_number`, temperaturas, coordenadas `x/y/z`...) e
  **temporais** (`date`, `date_start`, `date_end`)
- Combináveis entre si e com filtros de igualdade na mesma query
- Intervalo temporal = par `date>` + `date<` (ou `>=`/`<=`)

> ⚠️ **Verificação obrigatória por endpoint:** a doc não publica uma tabela
> formal de "campos que aceitam operadores". Cada campo operador proposto
> deve ser validado com chamada real antes de ser exposto na tool.

## 3. Arquitetura proposta

Princípio orientador: **a IA nunca escreve operadores**. O LLM preenche
campos com nomes amigáveis (`speed_min`, `date_from`); a tradução para as
chaves da API (`speed>=`, `date>=`) é interna. Isso preserva o princípio 4 do
`Architectural_Design.md` ("a IA nunca vê o interior") e evita que o LLM
precise produzir chaves exóticas como `speed>=`.

### 3.1 Impacto por camada

```
LLM preenche: speed_min=300, date_from=..., date_to=...
        │
        ▼
schemas/<recurso>.py      novos campos opcionais com nomes amigáveis
        │
validators/<recurso>.py   regras: min <= max, from < to, coerência entre filtros
        │
services/<recurso>.py     mapeamento: speed_min → "speed>=" (tabela explícita)
        │
clients/openf1.py         serialização da query com operadores (ver 3.4)
        │
        ▼
GET /v1/car_data?...&speed>=300&date>=...&date<...
```

### 3.2 Convenção de nomes nos schemas (proposta)

| Campo amigável | Chave na API | Significado |
|---|---|---|
| `<campo>_min` | `<campo>>=` | Limite inferior inclusivo |
| `<campo>_max` | `<campo><=` | Limite superior inclusivo |
| `date_from` | `date>=` | Início do intervalo (inclusivo) |
| `date_to` | `date<=` | Fim do intervalo (inclusivo) |

Decisões embutidas na proposta (a confirmar na implementação):

- **Sufixos `_min`/`_max` inclusivos** (`>=`/`<=`) em vez de exclusivos
  (`>`/`<`): mais intuitivos para o LLM ("mínimo de 300 km/h") e cobrem o
  caso comum. Operadores exclusivos ficam fora desta fase.
- **Assinatura plana mantida** (seção 4.1 do Architectural_Design): nada de
  objetos aninhados tipo `Range(min=..., max=...)` — um parâmetro por filtro.
- **Igualdade continua existindo**: `lap_number=8` e `lap_number_min`/`max`
  podem coexistir; o validator rejeita combinações contraditórias.

### 3.3 Validações semânticas novas (validators)

- `*_min <= *_max` quando ambos informados
- `date_from < date_to` quando ambos informados
- Igualdade + faixa no mesmo campo → erro (`lap_number=8` com
  `lap_number_min=5` é contraditório)
- Formato de datas: ISO 8601 compatível com a API
- Regra de ao menos um filtro não-nulo **inalterada** (operadores também
  contam como filtro)

### 3.4 Serialização no cliente HTTP (ponto técnico crítico)

**Descobertas do spike (testes reais contra a API, 20/09/2026):**

| Experimento | Resultado | Conclusão |
|---|---|---|
| `urlencode` padrão (`speed%3E%3D=315`) | 404 "No results found" | A API **não decodifica chaves** percent-encoded |
| `urlencode(..., safe="><")` (`speed>%3D=315`) | 404 | Idem — `=` na chave também não pode ser codificado |
| `speed>314` (token sem `=`) | 2 resultados | `>` **estrito** funciona |
| `speed>315` (máx. da sessão = 315) | 404 | Confirma `>` estrito |
| `speed>=315` | 2 resultados | `>=` **inclusivo** funciona |
| `speed<100` vs `speed<=100` | 10.283 vs 10.346 | `<` estrito vs `<=` inclusivo |
| Valores de data codificados (`%3A`) | OK | Valores **são** decodificados normalmente |

**Regra de serialização implementada** (`clients/openf1.py::_build_query`):
a API faz parsing *raw* da query string. Chave com sufixo de operador
(`>`, `>=`, `<`, `<=`) é concatenada ao valor **sem separador `=` adicional**
(`speed>=` + `315` → `speed>=315`); chaves de igualdade usam `key=value`.
Valores passam por `quote()` normalmente.

> O cliente continua sem conhecer regras de negócio: ele apenas serializa as
> chaves que o service entregar. A tradução `speed_min → "speed>="` vive no
> **service**, via tabela `_OPERATOR_FIELDS` por recurso, aplicada pelo
> helper compartilhado `services/common.py::build_params`.

### 3.5 Docstrings das tools

Atualizar a seção `Args` das tools afetadas com os novos parâmetros, sempre
em inglês, explicando o efeito em linguagem de domínio:

```
Args:
    speed_min: int — optional, minimum speed in km/h (inclusive).
        Use to isolate high-speed samples (e.g., 300 for straights only).
    date_from / date_to: str — optional, ISO 8601 UTC bounds (inclusive).
        Use lap date_start values to isolate a single lap.
```

## 4. Escopo por tool (implementado)

Legenda: 🎯 prioridade máxima · ✅ implementado e verificado com chamada real ·
⏸️ adiado (baixa utilidade prática)

| Tool | Operadores implementados | Status |
|---|---|---|
| `get_car_data` | `speed`, `rpm`, `throttle`, `n_gear`, `drs` (min/max) + `date_from/to` | ✅ 🎯 |
| `get_location` | `x`, `y`, `z` (min/max) + `date_from/to` | ✅ 🎯 |
| `get_laps` | `lap_number`, `lap_duration`, `duration_sector_1/2/3`, `i1/i2/st_speed` (min/max) + `date_from/to` (sobre `date_start`) | ✅ |
| `get_weather` | `air/track_temperature`, `humidity`, `rainfall`, `wind_speed` (min/max) + `date_from/to` | ✅ |
| `get_intervals` | `date_from/to` | ✅ |
| `get_positions` | `position` (min/max) + `date_from/to` | ✅ |
| `get_race_control` | `lap_number` (min/max) + `date_from/to` | ✅ |
| `get_pit_stops` | `lap_number`, `lane_duration` (min/max) + `date_from/to` | ✅ |
| `get_stints` | `lap_start`, `lap_end`, `tyre_age_at_start` (min/max) | ✅ |
| `get_overtakes`, `get_sessions`, `get_meetings`, `get_session_results`, `get_starting_grid` | — | ⏸️ reavaliar se surgir demanda |
| `get_drivers`, `get_team_radio`, championships | nenhum (campos textuais ou já pontuais) | — |

## 5. Exemplos de uso esperados (IA → tool → API)

| Pergunta do usuário | Parâmetros da tool | Query gerada |
|---|---|---|
| "Quando o Verstappen passou de 300 km/h em Monza?" | `session_key=11361, driver_number=3, speed_min=300` | `car_data?session_key=11361&driver_number=3&speed>=300` |
| "Telemetria da volta 8 do Hamilton" | `session_key=..., driver_number=44, date_from=<date_start volta 8>, date_to=<date_start volta 9>` | `car_data?...&date>=...&date<...` |
| "Voltas abaixo de 1m20s em Suzuka" | `session_key=11253, lap_duration_max=80` | `laps?session_key=11253&lap_duration<=80` |
| "Choveu em algum momento da corrida?" | `session_key=..., rainfall_min=1` | `weather?session_key=...&rainfall>=1` |

> Nota: "volta 8" exige duas chamadas encadeadas (primeiro `get_laps` para
> obter `date_start` das voltas 8 e 9, depois `get_car_data` com o intervalo).
> As docstrings devem ensinar esse padrão à IA — é o mesmo encadeamento que
> as tools compostas futuras (e os dashboards da fase de MCP Apps) vão
> encapsular.

## 6. Relação com as próximas fases

- **Task 04 (cache):** operadores mudam os argumentos → mudam a chave de
  cache do `ResponseCachingMiddleware`. Consultas fatiadas repetidas (ex: a
  mesma volta consultada por um dashboard interativo) serão servidas do
  cache. Ordem importa: operadores primeiro, cache depois.
- **MCP Apps (dashboards):** o dashboard de telemetria depende desta task —
  sem `date_from/to` não há como isolar uma volta para renderizar.

## 7. Critérios de aceite

- [x] Decisão registrada: sufixos `_min/_max` **inclusivos** (`>=`/`<=`);
      exclusivos (`>`/`<`) fora de escopo
- [x] Teste real de serialização: `urlencode` padrão **rejeitado** (API não
      decodifica chaves); implementado encoder próprio `_build_query` —
      ver seção 3.4
- [x] Tabela de mapeamento campo→operador no service de cada recurso
      (`_OPERATOR_FIELDS`) + helper compartilhado `services/common.py::build_params`
- [x] Validators rejeitam `min > max`, `from >= to` e igualdade+faixa no
      mesmo campo, com mensagens legíveis para a IA
      (`validators/common.py::validate_range` / `validate_date_range`)
- [x] `clients/openf1.py` serializa chaves com operadores sem conhecer
      regras de negócio
- [x] Docstrings atualizadas (inglês) ensinando o padrão de encadeamento
      para isolar voltas (`get_laps` → `date_start` → `get_car_data`)
- [x] Verificação com chamadas reais — resultados em 20/09/2026:

  | Teste | Resultado |
  |---|---|
  | `car_data` speed≥300 (Sainz, sessão 9159) | **72 amostras** (vs 18.470 sem filtro) |
  | `car_data` rpm≥11000 + throttle≥99 combinados | 1.886 amostras |
  | `location` com `date_from/to` (exemplo da doc oficial) | 2 amostras |
  | `laps` voltas 8–10 do Hamilton (Suzuka 2026) | 3 voltas |
  | `laps` `date_from/to` sobre `date_start` | 6 voltas |
  | `laps` `lap_duration<=100` | 942 voltas |
  | `weather` humidity≥50 | 124 amostras |
  | `weather` rainfall≥1 em Suzuka 2026 | 404 — vazio legítimo (não choveu) |
  | `positions` position≤3 (pódio) | 40 registros |
  | `race_control` lap≥50 | 9 eventos |
  | `pit` lane_duration≤25s | 22 paradas |
  | `stints` tyre_age≥2 | 2 stints (idades 2 e 3 — correto) |
  | `intervals` `date_from/to` (5 min) | 1.587 amostras |

- [x] Bugs latentes encontrados na verificação e corrigidos:
      `Lap.segments_sector_*` agora `list[int | None]` (API envia `null` por
      mini-setor); `Weather.humidity` agora `float` (API envia `51.6`)
- [x] `Architectural_Design.md` seção 8 atualizada (operadores: Implementado)
- [ ] Validação no MCP Inspector: telemetria de uma volta retorna volume
      compatível com contexto de LLM — **pendente: requer reload do servidor
      no Cursor/Inspector para carregar as novas assinaturas**

## 8. Fora de escopo

- Operadores exclusivos (`>`, `<` puros)
- Filtros `OR` / listas de valores (a API não documenta suporte)
- Deduplicação de registros (decisão adiada da task 02)
- Cache (task 04) e MCP Apps (fase posterior)
