"""Spike: MCP App view for drivers championship standings (task 05).

Renders an interactive HTML standings board (driver photo + points) in hosts
that support the MCP Apps extension. Falls back to plain JSON text otherwise.

Pattern: Custom HTML (see tasks/05_mcp_apps.md, section 3):
- A ui:// resource serves the view HTML (mime text/html;profile=mcp-app).
- The tool declares app=AppConfig(resource_uri=...) linking to that resource.
- The host renders the resource in a sandboxed iframe and forwards the tool
  result to it via the ext-apps JS SDK (loaded from unpkg, see CSP).
"""

import json

from fastmcp import FastMCP
from fastmcp.apps import AppConfig, ResourceCSP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.championship_drivers import DriversChampionshipInput
from mcp_sport.schemas.drivers import DriversInput
from mcp_sport.services import championship_drivers as championship_service
from mcp_sport.services import drivers as drivers_service

logger = get_logger("tools")

VIEW_URI = "ui://mcp-sport/standings.html"

# External origins the view loads: ext-apps JS SDK (unpkg) and F1 headshots.
_CSP = ResourceCSP(
    resource_domains=["https://unpkg.com", "https://media.formula1.com"]
)

_VIEW_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body { margin: 0; padding: 0; background: transparent; }
  body {
    font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
    color: #e8e8ec;
  }
  .board {
    display: flex; flex-direction: column; gap: 6px;
    padding: 12px; background: #15151e; border-radius: 12px;
  }
  .title {
    font-size: 13px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #9d9dab; margin: 0 4px 6px;
  }
  .row {
    display: flex; align-items: center; gap: 12px;
    background: #1f1f2b; border-radius: 8px; padding: 8px 12px;
  }
  .pos { font-size: 18px; font-weight: 800; width: 28px; color: #9d9dab; }
  .row.p1 .pos { color: #ffd700; }
  .bar { width: 4px; align-self: stretch; border-radius: 2px; }
  .photo {
    width: 44px; height: 44px; border-radius: 50%;
    object-fit: cover; background: #2b2b3a;
  }
  .info { flex: 1; min-width: 0; }
  .name { font-size: 14px; font-weight: 700; }
  .team { font-size: 11px; color: #9d9dab; }
  .pts { font-size: 18px; font-weight: 800; }
  .pts small { font-size: 10px; color: #9d9dab; font-weight: 600; }
  .empty { padding: 24px; text-align: center; color: #9d9dab; }
</style>
</head>
<body>
<div class="board" id="board"><div class="empty">Loading standings…</div></div>
<script type="module">
  import { App } from "https://unpkg.com/@modelcontextprotocol/ext-apps@0.4.0/app-with-deps";

  const app = new App({ name: "F1 Standings", version: "1.0.0" });

  function extractStandings(result) {
    const sc = result?.structuredContent;
    if (Array.isArray(sc)) return sc;
    if (Array.isArray(sc?.result)) return sc.result;
    const text = result?.content?.find(c => c.type === "text")?.text;
    if (!text) return [];
    const parsed = JSON.parse(text);
    return Array.isArray(parsed) ? parsed : (parsed.result ?? []);
  }

  function render(standings) {
    const board = document.getElementById("board");
    if (!standings.length) {
      board.innerHTML = '<div class="empty">No standings data.</div>';
      return;
    }
    const rows = standings.map(d => {
      const colour = d.team_colour ? "#" + d.team_colour : "#555";
      const photo = d.headshot_url
        ? `<img class="photo" src="${d.headshot_url}" alt="">`
        : `<div class="photo"></div>`;
      const pos = d.position_current ?? "–";
      const pts = d.points_current ?? 0;
      return `
        <div class="row ${pos === 1 ? "p1" : ""}">
          <span class="pos">${pos}</span>
          <div class="bar" style="background:${colour}"></div>
          ${photo}
          <div class="info">
            <div class="name">${d.full_name ?? "Unknown"}</div>
            <div class="team">${d.team_name ?? ""}</div>
          </div>
          <span class="pts">${pts} <small>PTS</small></span>
        </div>`;
    });
    board.innerHTML = '<div class="title">Drivers Championship</div>' + rows.join("");
  }

  app.ontoolresult = (result) => {
    try {
      render(extractStandings(result));
    } catch (err) {
      document.getElementById("board").innerHTML =
        '<div class="empty">Failed to render: ' + err.message + "</div>";
    }
  };

  await app.connect();
</script>
</body>
</html>
"""


def register(mcp: FastMCP) -> None:
    """Register the championship standings view (MCP App spike) on the server."""

    @mcp.resource(VIEW_URI, meta={"ui": {"csp": _CSP.model_dump(by_alias=True, exclude_none=True)}})
    def standings_view() -> str:
        """HTML view for the drivers championship standings MCP App."""
        return _VIEW_HTML

    @mcp.tool(app=AppConfig(resource_uri=VIEW_URI, csp=_CSP))
    def get_drivers_championship_view(
        session_key: int | str | None = None,
    ) -> str:
        """Fetch drivers championship standings and render them as a visual board.

        MCP App spike (task 05): in hosts supporting the MCP Apps extension,
        the result renders as an interactive HTML board with driver photos,
        team colors and points. In other hosts, the same data is returned as
        JSON text.

        Args:
            session_key: int | str — required in practice, positive int or
                'latest'. Race session identifier; use get_sessions with
                session_type='Race' to discover it.

        Returns:
            str: JSON array of standings entries, each with position_current,
            points_current, full_name, name_acronym, team_name, team_colour
            and headshot_url (merged from /championship_drivers and /drivers).
        """
        logger.info(
            "event=tool_call tool=get_drivers_championship_view session_key=%s",
            session_key,
        )
        standings = championship_service.get_drivers_championship(
            DriversChampionshipInput(session_key=session_key)
        )
        if not standings:
            return json.dumps([])

        resolved_session_key = standings[0].session_key
        drivers = drivers_service.get_drivers(
            DriversInput(session_key=resolved_session_key)
        )
        by_number = {d.driver_number: d for d in drivers}

        merged = []
        for entry in standings:
            driver = by_number.get(entry.driver_number)
            merged.append(
                {
                    "position_current": entry.position_current,
                    "points_current": entry.points_current,
                    "driver_number": entry.driver_number,
                    "full_name": driver.full_name if driver else None,
                    "name_acronym": driver.name_acronym if driver else None,
                    "team_name": driver.team_name if driver else None,
                    "team_colour": driver.team_colour if driver else None,
                    "headshot_url": driver.headshot_url if driver else None,
                }
            )
        merged.sort(
            key=lambda d: (d["position_current"] is None, d["position_current"] or 0)
        )
        return json.dumps(merged)
