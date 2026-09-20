# Task 02 — Cobertura completa dos endpoints da OpenF1 API

> **Status:** Concluída ✅ (18/18)
> **Fase:** 2
> **Referências canônicas:** `docs/Architectural_Design.md` (procedimento da
> seção 7 é **obrigatório** por endpoint), `docs/Technical_Reference.md`,
> `docs/Logging_Strategy.md`
> **Fonte:** [OpenF1 API docs](https://openf1.org/docs/) — base URL
> `https://api.openf1.org/v1`

## 1. Objetivo

Implementar tools MCP para **todos os endpoints documentados da OpenF1 API**,
seguindo rigorosamente os padrões do `Architectural_Design.md`: tool limpa,
`BaseInput` nos schemas, validators por recurso, service como orquestrador,
cliente HTTP único e docstring no padrão canônico.

**Fluxo de trabalho:** o usuário libera os endpoints um a um (ou em lotes).
A cada liberação: implementar → validar (Pydantic, validator, Inspector,
chamada real) → marcar no checklist da seção 3.

## 2. Regras gerais aplicáveis a todos os endpoints

- Herdar schemas de entrada de `BaseInput` (`schemas/base.py`)
- Exigir ao menos um filtro **com valor não-nulo** por tool
- `session_key`/`meeting_key`: `int | str` positivo ou `"latest"`
- Campos depreciados pela API: manter opcionais e marcar na `description`
- Datas: aceitar formatos compatíveis com a API (ISO 8601 preferencial);
  filtros temporais com operadores (`date>`, `date<`) ficam para fase futura —
  nesta fase, apenas filtros de igualdade
- Respostas com registros duplicados pela própria API (observado em
  `/drivers`): não deduplicar nesta fase — decisão adiada
- Endpoints em **beta** (`championship_drivers`, `championship_teams`):
  documentar a instabilidade na docstring da tool

## 3. Checklist de endpoints (18)

Legenda: ✅ implementado e validado · ⬜ aguardando liberação

| # | Endpoint | Path | Tool | Status |
|---|---|---|---|---|
| 1 | Drivers | `/drivers` | `get_drivers` | ✅ (task 01) |
| 2 | Sessions | `/sessions` | `get_sessions` | ✅ (Lote A) |
| 3 | Meetings | `/meetings` | `get_meetings` | ✅ (Lote A) |
| 4 | Session result | `/session_result` | `get_session_results` | ✅ (Lote B) |
| 5 | Laps | `/laps` | `get_laps` | ✅ (Lote C) |
| 6 | Pit | `/pit` | `get_pit_stops` | ✅ (Lote C) |
| 7 | Position | `/position` | `get_positions` | ✅ (Lote B) |
| 8 | Starting grid | `/starting_grid` | `get_starting_grid` | ✅ (Lote B) |
| 9 | Stints | `/stints` | `get_stints` | ✅ (Lote C) |
| 10 | Intervals | `/intervals` | `get_intervals` | ✅ (Lote C) |
| 11 | Race control | `/race_control` | `get_race_control` | ✅ (Lote C) |
| 12 | Weather | `/weather` | `get_weather` | ✅ (Lote D) |
| 13 | Car data | `/car_data` | `get_car_data` | ✅ (Lote E) |
| 14 | Location | `/location` | `get_location` | ✅ (Lote E) |
| 15 | Overtakes | `/overtakes` | `get_overtakes` | ✅ (Lote D) |
| 16 | Team radio | `/team_radio` | `get_team_radio` | ✅ (Lote D) |
| 17 | Drivers championship (beta) | `/championship_drivers` | `get_drivers_championship` | ✅ (Lote F) |
| 18 | Teams championship (beta) | `/championship_teams` | `get_teams_championship` | ✅ (Lote F) |

## 4. Especificação resumida por endpoint

Detalhes completos de campos na [doc oficial](https://openf1.org/docs/).
Ao implementar cada um, transcrever a tabela de atributos oficial para o
schema de saída (tipos + anuláveis) e detalhar a docstring.

### 4.1 Sessions — `/sessions`
Períodos de atividade em pista (Practice, Qualifying, Sprint, Race).
Filtros típicos: `session_key`, `meeting_key`, `year`, `country_name`,
`session_name`, `session_type`, `circuit_key`, `location`.
Saída: `session_key`, `meeting_key`, `session_name`, `session_type`,
`date_start`, `date_end`, `gmt_offset`, `country_*`, `circuit_*`, `location`,
`year`, `is_cancelled`.

### 4.2 Meetings — `/meetings`
Grandes Prêmios / fins de semana de teste.
Filtros típicos: `meeting_key`, `year`, `country_name`, `circuit_key`,
`meeting_name`, `location`.
Saída: `meeting_key`, `meeting_name`, `meeting_official_name`, `date_start`,
`date_end`, `gmt_offset`, `country_*`, `circuit_*` (inclui `circuit_image`,
`circuit_info_url`, `circuit_type`), `location`, `year`, `is_cancelled`.

### 4.3 Session result — `/session_result`
Classificação final de uma sessão (disponível minutos após publicação oficial).
Filtros típicos: `session_key` (praticamente obrigatório na prática),
`driver_number`, `position`.
Saída: `position`, `driver_number`, `number_of_laps`, `dnf`, `dns`, `dsq`,
`duration`, `gap_to_leader`, `meeting_key`, `session_key`.
Atenção: `duration` e `gap_to_leader` podem ser **arrays** em qualifying
(Q1/Q2/Q3) — modelar como `float | list | None`.

### 4.4 Laps — `/laps`
Detalhes por volta.
Filtros típicos: `session_key`, `driver_number`, `lap_number`.
Saída: `lap_number`, `lap_duration`, `duration_sector_1/2/3`,
`i1_speed`, `i2_speed`, `st_speed`, `is_pit_out_lap`,
`segments_sector_1/2/3` (arrays de int — ver tabela de valores na doc),
`date_start`, `meeting_key`, `session_key`.

### 4.5 Pit — `/pit`
Passagens pelo pit lane.
Filtros típicos: `session_key`, `driver_number`, `lap_number`.
Saída: `date`, `driver_number`, `lap_number`, `lane_duration`,
`stop_duration` (só a partir do GP dos EUA 2024), `pit_duration`
(**deprecated** — mesmo valor de `lane_duration`), `meeting_key`, `session_key`.

### 4.6 Position — `/position`
Posições ao longo de uma sessão.
Filtros típicos: `session_key` ou `meeting_key`, `driver_number`.
Saída: `date`, `driver_number`, `position`, `meeting_key`, `session_key`.

### 4.7 Starting grid — `/starting_grid`
Grid de largada (disponível após publicação oficial).
Filtros típicos: `session_key`, `driver_number`, `position`.
Saída: `position`, `driver_number`, `lap_duration`, `meeting_key`,
`session_key`.

### 4.8 Stints — `/stints`
Stints (períodos contínuos de pilotagem).
Filtros típicos: `session_key`, `driver_number`, `stint_number`, `compound`.
Saída: `compound` (SOFT/MEDIUM/HARD/...), `driver_number`, `lap_start`,
`lap_end`, `stint_number`, `tyre_age_at_start`, `meeting_key`, `session_key`.

### 4.9 Intervals — `/intervals`
Intervalos em tempo real entre pilotos (só corridas, ~4s de atualização).
Filtros típicos: `session_key`, `driver_number`.
Saída: `date`, `driver_number`, `gap_to_leader`, `interval`
(ambos `float | str | None` — podem ser `"+1 LAP"` ou `null` para o líder),
`meeting_key`, `session_key`.

### 4.10 Race control — `/race_control`
Eventos de direção de prova (flags, safety car, incidentes).
Filtros típicos: `session_key`, `driver_number`, `flag`, `category`, `scope`.
Saída: `category`, `date`, `driver_number` (anulável), `flag`, `lap_number`,
`message`, `qualifying_phase`, `scope`, `sector`, `meeting_key`, `session_key`.

### 4.11 Weather — `/weather`
Clima na pista (atualização por minuto).
Filtros típicos: `meeting_key`, `session_key`.
Saída: `date`, `air_temperature`, `track_temperature`, `humidity`,
`pressure`, `rainfall`, `wind_direction` (0–359°), `wind_speed`,
`meeting_key`, `session_key`.

### 4.12 Car data — `/car_data`
Telemetria do carro (~3.7 Hz). **Alto volume** — reforçar obrigatoriedade de
filtros restritivos (`session_key` + `driver_number`).
Saída: `brake` (0/100), `date`, `drs` (ver tabela de valores na doc),
`n_gear` (0–8), `rpm`, `speed`, `throttle`, `driver_number`, `meeting_key`,
`session_key`.

### 4.13 Location — `/location`
Posição aproximada do carro no circuito (~3.7 Hz). **Alto volume** — mesma
restrição de `car_data`.
Saída: `date`, `x`, `y`, `z`, `driver_number`, `meeting_key`, `session_key`.

### 4.14 Overtakes — `/overtakes`
Ultrapassagens (só corridas; dados podem ser incompletos).
Filtros típicos: `session_key`, `overtaking_driver_number`,
`overtaken_driver_number`, `position`.
Saída: `date`, `overtaking_driver_number`, `overtaken_driver_number`,
`position`, `meeting_key`, `session_key`.

### 4.15 Team radio — `/team_radio`
Trechos de rádio (seleção limitada; cobertura reduzida desde 2026 —
documentar limitação na docstring).
Filtros típicos: `session_key`, `driver_number`.
Saída: `date`, `driver_number`, `recording_url`, `meeting_key`, `session_key`.

### 4.16 Drivers championship (beta) — `/championship_drivers`
Classificação do campeonato de pilotos (só sessões de corrida).
Filtros típicos: `session_key`, `driver_number`.
Saída: `position_current`, `position_start`, `points_current`,
`points_start`, `driver_number`, `meeting_key`, `session_key`.

### 4.17 Teams championship (beta) — `/championship_teams`
Classificação do campeonato de equipes (só sessões de corrida).
Filtros típicos: `session_key`, `team_name`.
Saída: `position_current`, `position_start`, `points_current`,
`points_start`, `team_name`, `meeting_key`, `session_key`.

## 5. Critérios de aceite (por endpoint)

Seguir o procedimento da seção 7 do `Architectural_Design.md`:

- [ ] Schema herda `BaseInput`; saída fiel à tabela oficial de atributos
- [ ] Validator: ao menos um filtro não-nulo + regras específicas do recurso
- [ ] Service e tool conforme camadas; docstring no padrão canônico
- [ ] Registro em `server.py`
- [ ] Validação: Pydantic rejeita inválidos; chamada real à API retorna modelos
- [ ] Marcar endpoint como ✅ na seção 3

## 6. Ordem sugerida de implementação

> **⚠️ Observação importante dos testes reais (Lote E):** mesmo com os filtros
> restritivos (`session_key` + `driver_number`), uma sessão completa de um
> piloto retorna **18–24 mil amostras** — grande demais para o contexto de um
> LLM. A proteção atual evita o pior caso (histórico inteiro), mas o caso
> comum ainda é pesado. Isso fortalece o item adiado no
> `Architectural_Design.md`: **filtros com operadores** (`speed>=315`,
> `date>...`, `date<...`) — a API suporta nativamente e é a forma correta de
> fatiar telemetria ("só quando passou de 300 km/h", "só a volta 8").
> **Tratar como task 03 após fechar os 18 endpoints.**

1. **Lote A (navegação):** `sessions`, `meetings` — pré-requisito para a IA
   descobrir `session_key`s
2. **Lote B (resultados):** `session_result`, `starting_grid`, `position` —
   viabiliza "pontos do piloto nas últimas N corridas"
3. **Lote C (corrida):** `laps`, `pit`, `stints`, `intervals`, `race_control`
4. **Lote D (contexto):** `weather`, `overtakes`, `team_radio`
5. **Lote E (telemetria pesada):** `car_data`, `location` — exigem filtros
   restritivos
6. **Lote F (beta):** `championship_drivers`, `championship_teams`
