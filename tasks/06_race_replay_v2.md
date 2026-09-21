# Task 06 — Race Replay v2: esteira, pneus, setores e pit

> **Status:** Concluída — validada visualmente no basic-host (2026-09-21)
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

**Decisão final (validação visual):** as cores são calculadas **na view,
no instante do replay**. Só existe **um roxo por setor** naquele momento;
quando o recorde cai, o detentor anterior volta a verde. O servidor ainda
envia cores pré-computadas no payload, mas a view não as usa para pintar.

A revelação é pela **fração da volta** (1/3, 2/3, 3/3), não pela soma dos
tempos de setor — essa soma iguala a duração da volta e o S3 nunca
aparecia. O setor permanece visível até o setor correspondente da volta
seguinte ser revelado. Ao lado, o tempo total da volta em branco, formato
`MM:SS:mmm` (ex.: 87.596 s → `01:27:596`).

Fonte: `/laps` (`duration_sector_1/2/3`, `lap_duration`, `lap_number`,
`date_start`).

### R5 — Status de PIT

Quando o piloto está no pit, o card exibe badge **PIT** (substituindo ou
ao lado dos setores). Janela de pit derivada de `/pit`: `date` (entrada)
+ `pit_duration` → `[entrada, entrada + duração]`. Validado: ex. Hamilton
entrou 13:19:06, `pit_duration` 22.48s, `stop_duration` 2.5s.

Complemento: `/laps.is_pit_out_lap` marca a volta de saída.

### R6 — Indicador de Safety Car / VSC no topo

Durante Safety Car, Virtual Safety Car ou corrida suspensa, um banner
**centralizado no header** mostra `VIRTUAL SAFETY CAR`, `SAFETY CAR` ou
`RACE SUSPENDED`. O bloco da direita (sessão, horário local, DRY/WET,
temperaturas) permanece fixo.

Fonte: `/race_control`. Janelas derivadas dos pares de mensagens:

| Mensagem | Efeito |
|---|---|
| `SAFETY CAR DEPLOYED` / `VSC DEPLOYED` | abre SC/VSC |
| `SAFETY CAR IN THIS LAP` / `VSC ENDING` | fecha SC/VSC |
| `RED FLAG` (fronteira de palavra) ou `SUSPENDED` | abre RED |
| `ENDING` / `RESUMED` / `RESTART` / `GREEN FLAG` | fecha RED |

`CHEQUERED FLAG` contém as letras de `RED FLAG`; a detecção usa `\bRED FLAG\b`
para não abrir uma janela falsa no fim da prova. Janela cujo fechamento
cai antes da abertura é ignorada.

Validado em Barcelona 2026: 2 janelas de VSC. Setores nulos durante essas
voltas continuam exibindo `—`, e o banner deixa claro o motivo.

### R7 — Cabeçalho da prova

País (bandeira), circuito, nome da sessão, horário de início no fuso do
circuito (`gmt_offset`), condição DRY/WET e temperaturas (ar, pista,
umidade) amostradas no instante do replay. Fontes: `/sessions`, `/meetings`,
`/weather`.

### R8 — Abandono

`dnf` vira tag cinza permanente **OUT** a partir do fim da última volta
completa; `dns` vira **DNS** desde t=0. O card escurece. Setores passam a
`--`, o tempo de volta a `--:--:----`, e o gap (`+tempo`, `+N LAPS`,
`LEADER`) some. Retardatário que segue na prova mantém o card normal e o
badge `+N LAPS`. Fonte: `/session_result` (`dnf`, `dns`, `number_of_laps`).
`dsq` não tem tag.

### R9 — Velocidades do player

`1x`, `10x`, `30x`, `60x` (padrão), `300x`.

## 3. Mapeamento de dados

| Elemento da UI | Endpoint | Campos |
|---|---|---|
| Ordem vertical | `/position` | `date`, `driver_number`, `position` |
| Grid inicial | `/position` (t=0) ou `/starting_grid` | — |
| Esteira + contador de voltas | `/laps` (só líder) | `date_start`, `lap_duration`, `lap_number` |
| Pneu atual | `/stints` | `compound`, `lap_start`, `lap_end` |
| Setores + tempo de volta | `/laps` | `duration_sector_1/2/3`, `lap_duration` (cores ao vivo na view) |
| Pit | `/pit` | `date`, `pit_duration`, `stop_duration` |
| Safety Car / VSC / suspensa | `/race_control` | `category`, `flag`, `message`, `date` |
| Cabeçalho | `/sessions`, `/meetings`, `/weather` | país, circuito, `date_start`, `gmt_offset`, temperaturas, `rainfall` |
| Abandono | `/session_result` | `dnf`, `dns`, `number_of_laps` |
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

Confortável para tool result (bem abaixo de 1 MB). A view tool em si não
entra nos grupos de cache — ver `docs/Cache_Strategy.md`, seção 4.

## 5. Casos de borda

- **Relógio:** t0 é o início da volta 1 (lights-out), não a primeira
  amostra de `/position`. Em Barcelona 2026 a formação começa ~54 min
  antes; eventos anteriores a t0 ainda montam o grid em t=0
- **Setores nulos** (voltas de safety car, in/out laps): exibir `—`; o
  banner (R6) explica SC/VSC/suspensa
- **Volta 1 sem setores completos** (largada): setores aparecem conforme
  a fração da volta
- **DNF / DNS:** ver R8. Retardatário não escurece
- **`session_key` ausente ou vazio:** a view coerciona para `'latest'`
  antes de chamar `/position`. Durante corrida ao vivo o replay é um
  snapshot
- **Erro de tool que não é JSON:** a view mostra o texto; não tenta
  `JSON.parse`

## 6. Critérios de aceite

- [x] Grid alinhado pré-start na ordem de classificação
- [x] Esteira quadriculada em loop cuja velocidade acompanha o P1
- [x] Contador de voltas incrementa quando o líder "cruza" a faixa
- [x] Círculo de pneu correto por piloto a cada stint (S/M/H)
- [x] Setores verde/amarelo/roxo, um único roxo por setor no instante do replay
- [x] Tempo total da volta em `MM:SS:mmm`
- [x] Badge PIT durante a janela de parada
- [x] Banner SC / VSC / corrida suspensa centralizado no header
- [x] Cabeçalho com país, circuito, horário local e condição da pista
- [x] Tag OUT/DNS, card escurecido, sem gap, setores e volta apagados
- [x] Velocidades 1x / 10x / 30x / 60x (padrão) / 300x
- [x] Fallback JSON em hosts sem MCP Apps (Cursor)
- [x] Validação visual no basic-host (Barcelona 2026, session 11307)

## 7. Fora de escopo (v2)

- Telemetria de velocidade/RPM (é o dashboard de volta — task futura)
- DRS, mini-setores e bandeiras de setor (amarela etc.). SC, VSC e
  bandeira vermelha **estão** no escopo via R6
- Tag de desclassificação (`dsq`)
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
- Setores revelados pela fração da volta; cores recalculadas na view
  (um roxo por setor). O payload ainda traz cores pré-computadas, não usadas
- Badge PIT; banner central de SC/VSC/RED; cabeçalho com país, circuito,
  horário local e clima
- Grid pré-start: eventos anteriores a t0 (lights-out = início da volta 1)
  ordenam o grid
- Abandono: OUT/DNS, card escurecido, gap removido, setores `--`,
  volta `--:--:----`
- Player: 1x, 10x, 30x, 60x (padrão), 300x
- `session_key` vazio vira `latest`; texto de erro da tool não é parseado
  como JSON

**Validações (Barcelona 2026, session 11307):**

- [x] Payload 238 KB (dentro da estimativa 200–250 KB)
- [x] 2 janelas VSC detectadas corretamente (13:59–14:01, 14:29–14:33)
- [x] Stints HAM: SOFT(1-11) → HARD(12-27) → MEDIUM(28-41) → HARD(42-66)
- [x] 3 pits HAM com janelas coerentes (~22s cada)
- [x] Cores: 20 roxos / 371 verdes / 3310 amarelos / 22 nulos — distribuição
      realista (roxos só em recordes)
- [x] Sintaxe JS validada (`node --check`)
- [x] Validação visual no basic-host (iterações de cabeçalho, relógio,
      cores ao vivo, abandono, tempo de volta e velocidades)
