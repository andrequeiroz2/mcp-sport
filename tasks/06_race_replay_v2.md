# Task 06 — Race Replay v2: esteira, pneus, setores e pit

> **Status:** Planejada — aguardando aprovação para implementar
> **Criada em:** 2026-09-21
> **Documentos relacionados:** `tasks/05_mcp_apps.md` (spike base validado),
> `docs/Architectural_Design.md` (seção 4.7 — padrão `apps/`),
> `src/mcp_sport/apps/race_replay_view.py` (v1 em produção)

## 1. Contexto

A v1 do race replay (`get_race_replay_view`) foi validada no basic-host:
ordem vertical por posição oficial, cards alinhados à esquerda, cronômetro,
play/pause/velocidade/seek. Esta task é a evolução para uma experiência
próxima da transmissão de TV da F1.

## 2. Requisitos funcionais

### R1 — Grid pré-largada

Antes do start, os cards aparecem alinhados na **ordem de classificação
(grid)**: P1, P2, P3... A ordem inicial já vem dos primeiros eventos de
`/position` (validado: `[t=0, driver 63, P1]` em Barcelona 2026).
Opcional: cruzar com `/starting_grid` para a ordem oficial do grid.

### R2 — Faixa quadriculada em esteira

À frente dos cards, uma **faixa quadriculada vertical** (linha de
chegada/largada). Ao dar start:

- A faixa se move para a esquerda como uma **esteira** (loop contínuo)
- A **velocidade de rotação da esteira acompanha o P1**: o progresso do
  líder na volta atual define o deslocamento
- Quando o líder **cruza a faixa** (completa a volta), uma **nova volta se
  abre**: contador de voltas incrementa (`LAP 12/66`)

**Modelo de animação:** não temos posição do líder em tempo real — temos o
timestamp de conclusão de cada volta (`/laps.date_start` + `lap_duration`).
O progresso intra-volta do líder é **interpolado linearmente** entre o
início e o fim da volta corrente. A esteira é um padrão quadriculado em
loop cujo offset horizontal = fração da volta do líder.

### R3 — Pneus (convenção visual da F1)

Cada card exibe o composto atual do piloto como **círculo colorido com
letra**:

| Composto | Círculo | Letra |
|---|---|---|
| SOFT | 🔴 vermelho | S |
| MEDIUM | 🟡 amarelo | M |
| HARD | ⚪ branco | H |
| INTERMEDIATE/WET (se houver) | 🟢 verde / 🔵 azul | I / W |

Fonte: `/stints` (`compound`, `lap_start`, `lap_end`, `tyre_age_at_start`).
O composto exibido é o do stint que cobre a **volta atual do piloto**
naquele instante da corrida. Validado em Barcelona 2026: compounds
SOFT/MEDIUM/HARD presentes.

### R4 — Tempos de setor com cores de transmissão

Cada card exibe os **3 setores da volta em curso** (ou da última volta
completa), preenchendo progressivamente conforme o piloto os completa.
Convenção de cores da F1:

| Cor | Significado |
|---|---|
| 🟣 **Roxo** | Melhor setor de **todos os pilotos** até aquele momento |
| 🟢 **Verde** | Melhor setor **pessoal** do piloto até aquele momento |
| 🟡 **Amarelo** | Pior que o melhor pessoal |

**Decisão de implementação:** as cores são **pré-computadas no servidor**
no estilo "ao vivo" (best-so-far: cada setor é comparado com os melhores
tempos registrados até aquela volta, não com a corrida inteira). A view
apenas renderiza a cor recebida — zero lógica de classificação no JS.

Fonte: `/laps` (`duration_sector_1/2/3`, `lap_number`, `date_start`).
Validado: setores presentes por volta (ex.: 24.267 / 33.672 / 25.637).

### R5 — Status de PIT

Quando o piloto está no pit, o card exibe badge **PIT** (substituindo ou
ao lado dos setores). Janela de pit derivada de `/pit`: `date` (entrada)
+ `pit_duration` → `[entrada, entrada + duração]`. Validado: ex. Hamilton
entrou 13:19:06, `pit_duration` 22.48s, `stop_duration` 2.5s.

Complemento: `/laps.is_pit_out_lap` marca a volta de saída.

### R6 — Indicador de Safety Car / VSC no topo

Durante períodos de Safety Car ou Virtual Safety Car, o HUD exibe um
banner no topo: **🟨 SAFETY CAR** ou **🟨 VSC**.

Fonte: `/race_control`, categoria `SafetyCar`. As janelas são derivadas
dos pares de mensagens:

| Mensagem | Efeito |
|---|---|
| `SAFETY CAR DEPLOYED` / `VSC DEPLOYED` | abre a janela |
| `SAFETY CAR IN THIS LAP` / `VSC ENDING` | fecha a janela |

Validado em Barcelona 2026: 2 janelas de VSC (13:59–14:01 e 14:29–14:33).
Setores nulos durante essas voltas continuam exibindo `—` (ver 5), e o
banner deixa claro o motivo.

## 3. Mapeamento de dados

| Elemento da UI | Endpoint | Campos |
|---|---|---|
| Ordem vertical | `/position` | `date`, `driver_number`, `position` |
| Grid inicial | `/position` (t=0) ou `/starting_grid` | — |
| Esteira + contador de voltas | `/laps` (só líder) | `date_start`, `lap_duration`, `lap_number` |
| Pneu atual | `/stints` | `compound`, `lap_start`, `lap_end` |
| Setores + cores | `/laps` | `duration_sector_1/2/3` (cores pré-computadas no servidor) |
| Pit | `/pit` | `date`, `pit_duration`, `stop_duration` |
| Safety Car / VSC | `/race_control` | `category='SafetyCar'`, `message`, `date` |
| Cards (foto, cor, sigla) | `/drivers` | `headshot_url`, `team_colour`, `name_acronym` |

## 4. Payload (estimativa)

| Bloco | Volume | Tamanho |
|---|---|---|
| events (posições) | 613 | ~15 KB |
| gaps decimados | ~300/piloto | ~90 KB |
| laps + setores + cores | 22 × ~66 voltas ≈ 1.450 | ~90 KB |
| stints | 22 × 2–4 | ~3 KB |
| pit windows | ~25 | ~2 KB |
| SC/VSC windows | ~2–6 | <1 KB |
| drivers meta | 22 | ~4 KB |
| **Total** | | **~200–250 KB** ✅ |

Dentro do limite de 1 MB do cache e confortável para tool result.

## 5. Casos de borda

- **Setores nulos** (voltas de safety car, in/out laps): exibir `—` **e
  banner Safety Car/VSC no topo** (R6) deixa claro o motivo
- **Volta 1 sem setores completos** (largada): setores aparecem a partir
  da primeira volta cronometrada
- **DNF**: piloto para de gerar laps — card congela com badge **OUT**
- **Retardatários**: manter comportamento da v1 (badge `+N LAPS`, opaco)
- **`session_key='latest'`**: resolve para a última corrida concluída;
  durante corrida ao vivo o replay é um snapshot (dados param no momento
  da chamada) — documentar na docstring

## 6. Critérios de aceite

- [ ] Grid alinhado pré-start na ordem de classificação
- [ ] Esteira quadriculada em loop cuja velocidade acompanha o P1
- [ ] Contador de voltas incrementa quando o líder "cruza" a faixa
- [ ] Círculo de pneu correto por piloto a cada stint (S/M/H)
- [ ] Setores com cores verde/amarelo/roxo (best-so-far, pré-computado)
- [ ] Badge PIT durante a janela de parada
- [ ] Banner SAFETY CAR / VSC no topo durante as janelas de neutralização
- [ ] Fallback JSON continua funcionando em hosts sem MCP Apps
- [ ] Validação visual no basic-host com Barcelona 2026 (session 11307)

## 7. Fora de escopo (v2)

- Telemetria de velocidade/RPM (é o dashboard de volta — task futura)
- DRS, mini-setores, bandeiras de pista (amarela, vermelha etc. — SC/VSC
  **está** no escopo via R6)
- Modo "ao vivo" (polling durante corrida real)

## 8. Log de execução

### 2026-09-21 — v2 implementada

**Servidor (`apps/race_replay_view.py`):**

- Payload v2: `events` + `gaps` (v1) + `laps` (por piloto: volta, t_start,
  duração, 3 setores + 3 cores) + `stints` + `pits` (janelas entrada→saída)
  + `sc` (janelas SC/VSC) + `total_laps`
- **Cores de setor pré-computadas** (`_compute_sector_colors`): laps
  ordenados por timestamp de conclusão; roxo = novo melhor geral no momento,
  verde = novo melhor pessoal, amarelo = mais lento, -1 = sem tempo
- Janelas SC/VSC derivadas de `/race_control` categoria `SafetyCar`
  (pares DEPLOYED → ENDING/IN THIS LAP; janela aberta fecha em `duration`)

**View:**

- Esteira quadriculada (padrão checker CSS) cujo scroll acompanha a fração
  da volta do líder; flash + incremento do contador `LAP n/N` ao cruzar
- Círculo de pneu por stint (S/M/H/I/W com cores oficiais)
- Setores revelados progressivamente conforme o tempo cumulativo da volta
  passa; cores vêm prontas do payload
- Badge PIT na janela da parada; banner 🟨 SC/VSC no topo
- Grid pré-start: eventos de posição em t=0 ordenam o grid

**Validações (Barcelona 2026, session 11307):**

- [x] Payload 238 KB (dentro da estimativa 200–250 KB)
- [x] 2 janelas VSC detectadas corretamente (13:59–14:01, 14:29–14:33)
- [x] Stints HAM: SOFT(1-11) → HARD(12-27) → MEDIUM(28-41) → HARD(42-66)
- [x] 3 pits HAM com janelas coerentes (~22s cada)
- [x] Cores: 20 roxos / 371 verdes / 3310 amarelos / 22 nulos — distribuição
      realista (roxos só em recordes)
- [x] Sintaxe JS validada (`node --check`)
- [ ] Validação visual no basic-host
