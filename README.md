# MCP Sport — F1 Telemetry MCP 🏎️

An **MCP (Model Context Protocol)** server that exposes Formula 1 data from the
[OpenF1 API](https://openf1.org/docs/) as tools for AI assistants
(Claude Desktop, Cursor, MCP Inspector, etc.).

Full coverage: **18 tools** matching the 18 documented OpenF1 endpoints —
sessions, meetings, drivers, results, laps, pit stops, stints, telemetry,
weather, championships and more.

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13+ |
| MCP framework | FastMCP 4.x |
| Validation | Pydantic v2 |
| Data | OpenF1 API (REST, free for historical data 2023+) |
| Project management | uv + pyproject.toml |
| Transport | stdio |

## Installation

```bash
# Clone and install dependencies
git clone <repo-url> mcp-sport
cd mcp-sport
uv sync
```

## Usage

### Run the server (stdio)

```bash
.venv/bin/python src/mcp_sport/server.py
```

### MCP Inspector (web UI to test the tools)

```bash
npx @modelcontextprotocol/inspector@latest .venv/bin/python src/mcp_sport/server.py
```

In the Inspector UI: transport **STDIO**, command `.venv/bin/python`,
args `src/mcp_sport/server.py` → **Connect**.

### Claude Desktop / Cursor

Add to the client's MCP configuration:

```json
{
  "mcpServers": {
    "f1-telemetry": {
      "command": "/absolute/path/mcp-sport/.venv/bin/python",
      "args": ["/absolute/path/mcp-sport/src/mcp_sport/server.py"]
    }
  }
}
```

## Available tools (18)

| Domain | Tool | Description |
|---|---|---|
| Navigation | `get_sessions` | Sessions (practice, qualifying, sprint, race) |
| | `get_meetings` | Grand Prix and testing weekends |
| Registry | `get_drivers` | Drivers by session/meeting |
| Results | `get_session_results` | Final classification of a session |
| | `get_starting_grid` | Starting grid |
| | `get_positions` | Position history throughout a session |
| Race | `get_laps` | Lap times, sectors and speeds |
| | `get_pit_stops` | Pit stops |
| | `get_stints` | Stints and tyre compounds |
| | `get_intervals` | Real-time gaps (leader and car ahead) |
| | `get_race_control` | Flags, safety car, incidents |
| Context | `get_weather` | Track weather (per-minute samples) |
| | `get_overtakes` | Overtakes |
| | `get_team_radio` | Team radio excerpts (MP3) |
| Telemetry | `get_car_data` | Speed, RPM, gear, throttle, brake, DRS (~3.7 Hz) |
| | `get_location` | Approximate car position on the circuit (~3.7 Hz) |
| Championships | `get_drivers_championship` | Drivers standings (beta) |
| | `get_teams_championship` | Teams standings (beta) |

### Example conversation with the AI

> "How many points did Norris score in the last two races?"

The AI orchestrates: `get_sessions(session_type="Race")` to discover recent
sessions → `get_session_results(session_key=..., driver_number=4)` on each one.

## Project structure

```
src/mcp_sport/
├── server.py           # Entrypoint: FastMCP instance + tool registration
├── exceptions.py       # Domain exceptions
├── logging_config.py   # Logging to stderr (stdout is the protocol channel)
├── clients/openf1.py   # Single OpenF1 HTTP client
├── schemas/            # Pydantic: input (BaseInput) and output per endpoint
├── validators/         # Business validations per endpoint
├── services/           # Orchestration per endpoint
└── tools/              # MCP tools (thin layer) per endpoint
```

## Canonical documentation

| Document | Contents |
|---|---|
| `docs/Technical_Reference.md` | Stack, versions and official links (source of truth) |
| `docs/Architectural_Design.md` | Implementation patterns and procedure for new endpoints |
| `docs/Logging_Strategy.md` | Logging strategy (stderr + per-request telemetry) |
| `tasks/` | History of planned and executed tasks |

## Configuration

| Variable | Default | Description |
|---|---|---|
| `MCP_SPORT_LOG_LEVEL` | `INFO` | Log level on stderr (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

## Known limitations

- Historical data from **2023** onwards; real-time data requires a paid OpenF1 subscription
- `session_result` and `starting_grid` return HTTP 404 until official results are published
- Telemetry (`car_data`, `location`) returns 18–24k samples per session/driver —
  operator filters (`speed>=315`, `date>...`) are on the roadmap (task 03)
- Championship endpoints are in **beta** on OpenF1

## License

Personal study project. OpenF1 is an unofficial project, not associated in any
way with the Formula 1 companies.
