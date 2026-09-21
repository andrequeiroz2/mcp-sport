"""MCP App: animated race replay view (task 05, spike 2).

Renders a bar-chart-race style animation: cars stacked by position, horizontal
offset by gap to leader, race clock, and animated position swaps as overtakes
happened. Data: /position (order events) + /intervals (gaps) + /drivers (meta).

Fallback: hosts without MCP Apps support receive the same payload as JSON text.
"""

import json
from datetime import datetime

from fastmcp import FastMCP
from fastmcp.apps import AppConfig, ResourceCSP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.drivers import DriversInput
from mcp_sport.schemas.intervals import IntervalsInput
from mcp_sport.schemas.positions import PositionsInput
from mcp_sport.services import drivers as drivers_service
from mcp_sport.services import intervals as intervals_service
from mcp_sport.services import positions as positions_service

logger = get_logger("tools")

VIEW_URI = "ui://mcp-sport/race-replay.html"

# External origins the view loads: ext-apps JS SDK (unpkg) and F1 headshots.
_CSP = ResourceCSP(
    resource_domains=["https://unpkg.com", "https://media.formula1.com"]
)

# Target gap samples per driver after decimation (payload vs. smoothness).
_MAX_GAP_SAMPLES = 300

_VIEW_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body { margin: 0; padding: 0; background: transparent; }
  body { font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; color: #e8e8ec; }
  .wrap { background: #15151e; border-radius: 12px; padding: 12px; }
  .hud { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
  .clock { font-size: 20px; font-weight: 800; font-variant-numeric: tabular-nums; }
  .hud button {
    background: #2b2b3a; color: #e8e8ec; border: 0; border-radius: 6px;
    padding: 6px 12px; cursor: pointer; font-weight: 700;
  }
  .hud button:hover { background: #3a3a4d; }
  .hud select { background: #2b2b3a; color: #e8e8ec; border: 0; border-radius: 6px; padding: 5px; }
  .progress { flex: 1; accent-color: #e10600; }
  .track { position: relative; height: 640px; overflow: hidden;
           background: #1a1a26; border-radius: 8px; }
  .car {
    position: absolute; top: 4px; left: 0; height: 26px; width: 150px;
    display: flex; align-items: center; gap: 6px; padding: 0 8px 0 0;
    border-radius: 13px; background: #2b2b3a;
    transition: transform 0.55s ease;
    will-change: transform;
  }
  .car .photo { width: 24px; height: 24px; border-radius: 50%; object-fit: cover;
                background: #444; margin-left: 1px; }
  .car .acr { font-size: 12px; font-weight: 800; letter-spacing: 0.5px; }
  .car .gap { font-size: 10px; color: #b9b9c7; font-variant-numeric: tabular-nums; }
  .car .pos {
    position: absolute; left: -26px; width: 20px; text-align: right;
    font-size: 12px; font-weight: 800; color: #9d9dab;
  }
  .car.p1 .pos { color: #ffd700; }
  .car.flash { box-shadow: 0 0 0 2px #ffd700; }
  .car.lapped { opacity: 0.55; }
  .empty { padding: 24px; text-align: center; color: #9d9dab; }
</style>
</head>
<body>
<div class="wrap">
  <div class="hud">
    <button id="play">▶ Play</button>
    <select id="speed">
      <option value="60">60x</option>
      <option value="120" selected>120x</option>
      <option value="300">300x</option>
      <option value="900">900x</option>
    </select>
    <span class="clock" id="clock">00:00:00</span>
    <input type="range" class="progress" id="progress" min="0" max="1000" value="0">
  </div>
  <div class="track" id="track"><div class="empty">Loading race…</div></div>
</div>
<script type="module">
  import { App } from "https://unpkg.com/@modelcontextprotocol/ext-apps@0.4.0/app-with-deps";

  const app = new App({ name: "F1 Race Replay", version: "1.0.0" });

  const ROW_H = 29;          // px per position row
  const TRACK_LEFT = 30;     // px offset for position labels

  let data = null;
  let raceTime = 0, playing = false, speed = 120, lastFrame = null;
  let eventIdx = 0;                       // next position event to apply
  const order = [];                       // current order: driver_number by P1..Pn
  const cars = new Map();                 // driver_number -> element

  const $ = (id) => document.getElementById(id);

  function extractPayload(result) {
    const sc = result?.structuredContent;
    if (sc && typeof sc === "object" && sc.result) return typeof sc.result === "string" ? JSON.parse(sc.result) : sc.result;
    const text = result?.content?.find(c => c.type === "text")?.text;
    return JSON.parse(text);
  }

  function fmtClock(t) {
    const h = String(Math.floor(t / 3600)).padStart(2, "0");
    const m = String(Math.floor((t % 3600) / 60)).padStart(2, "0");
    const s = String(Math.floor(t % 60)).padStart(2, "0");
    return `${h}:${m}:${s}`;
  }

  function gapAt(driver, t) {
    const arr = data.gaps[driver];
    if (!arr || !arr.length) return null;
    let lo = 0, hi = arr.length - 1;
    if (t <= arr[0][0]) return arr[0][1];
    if (t >= arr[hi][0]) return arr[hi][1];
    while (lo < hi - 1) { const mid = (lo + hi) >> 1; (arr[mid][0] <= t ? lo = mid : hi = mid); }
    const [t0, g0] = arr[lo], [t1, g1] = arr[hi];
    if (typeof g0 !== "number" || typeof g1 !== "number") return g0; // lapped: no lerp
    return g0 + (g1 - g0) * ((t - t0) / (t1 - t0));
  }

  function applyEvents(upTo) {
    while (eventIdx < data.events.length && data.events[eventIdx][0] <= upTo) {
      const [, driver, pos] = data.events[eventIdx++];
      const cur = order.indexOf(driver);
      if (cur !== -1) order.splice(cur, 1);
      order.splice(pos - 1, 0, driver);
      const el = cars.get(driver);
      if (el && cur !== -1 && cur !== pos - 1) {
        el.classList.add("flash");
        setTimeout(() => el.classList.remove("flash"), 700);
      }
    }
  }

  function render() {
    for (let i = 0; i < order.length; i++) {
      const driver = order[i];
      const el = cars.get(driver);
      if (!el) continue;
      const gap = gapAt(driver, raceTime);
      const lapped = typeof gap === "string";
      const secs = typeof gap === "number" ? gap : null;
      el.style.transform = `translate(${TRACK_LEFT}px, ${i * ROW_H}px)`;
      el.classList.toggle("p1", i === 0);
      el.classList.toggle("lapped", lapped);
      el.querySelector(".pos").textContent = i + 1;
      el.querySelector(".gap").textContent =
        i === 0 ? "LEADER" : lapped ? gap : secs !== null ? "+" + secs.toFixed(1) + "s" : "";
    }
    $("clock").textContent = fmtClock(raceTime);
    if (document.activeElement !== $("progress"))
      $("progress").value = Math.round((raceTime / data.duration) * 1000);
  }

  function tick(now) {
    if (!playing) return;
    if (lastFrame !== null) raceTime = Math.min(raceTime + ((now - lastFrame) / 1000) * speed, data.duration);
    lastFrame = now;
    applyEvents(raceTime);
    render();
    if (raceTime >= data.duration) { playing = false; $("play").textContent = "▶ Play"; return; }
    requestAnimationFrame(tick);
  }

  function build() {
    const track = $("track");
    track.innerHTML = "";
    cars.clear(); order.length = 0; eventIdx = 0; raceTime = 0;
    for (const d of data.drivers) {
      const el = document.createElement("div");
      el.className = "car";
      el.style.borderLeft = "4px solid " + (d.team_colour ? "#" + d.team_colour : "#555");
      el.innerHTML =
        `<span class="pos"></span>` +
        (d.headshot_url ? `<img class="photo" src="${d.headshot_url}" alt="">` : `<div class="photo"></div>`) +
        `<span class="acr">${d.name_acronym ?? d.driver_number}</span>` +
        `<span class="gap"></span>`;
      track.appendChild(el);
      cars.set(d.driver_number, el);
      order.push(d.driver_number);
    }
    render();
  }

  $("play").onclick = () => {
    if (!data) return;
    if (raceTime >= data.duration) { build(); }
    playing = !playing;
    $("play").textContent = playing ? "⏸ Pause" : "▶ Play";
    lastFrame = null;
    if (playing) requestAnimationFrame(tick);
  };
  $("speed").onchange = (e) => { speed = Number(e.target.value); };
  $("progress").oninput = (e) => {
    if (!data) return;
    raceTime = (Number(e.target.value) / 1000) * data.duration;
    build(); applyEvents(raceTime); render();   // rebuild order from scratch
  };

  app.ontoolresult = (result) => {
    try {
      data = extractPayload(result);
      if (!data?.drivers?.length) {
        $("track").innerHTML = '<div class="empty">No race data.</div>';
        return;
      }
      build();
    } catch (err) {
      $("track").innerHTML = '<div class="empty">Failed to render: ' + err.message + "</div>";
    }
  };

  await app.connect();
</script>
</body>
</html>
"""


def _parse_ts(value: str) -> datetime:
    """Parse an OpenF1 ISO 8601 timestamp."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def register(mcp: FastMCP) -> None:
    """Register the race replay view (MCP App spike 2) on the server."""

    @mcp.resource(VIEW_URI, meta={"ui": {"csp": _CSP.model_dump(by_alias=True, exclude_none=True)}})
    def race_replay_view() -> str:
        """HTML view for the animated race replay MCP App."""
        return _VIEW_HTML

    @mcp.tool(app=AppConfig(resource_uri=VIEW_URI, csp=_CSP))
    def get_race_replay_view(
        session_key: int | str | None = None,
    ) -> str:
        """Replay a race as an animated position chart (bar-chart-race style).

        MCP App spike (task 05): in hosts supporting the MCP Apps extension,
        renders an animation with cars stacked by position, horizontal offset
        by gap to leader, race clock, play/pause, speed and seek controls.
        In other hosts, the same payload is returned as JSON text.

        Args:
            session_key: int | str — required in practice, positive int or
                'latest'. RACE session identifier; use get_sessions with
                session_type='Race' to discover it.

        Returns:
            str: JSON object with 'drivers' (number, acronym, team colour,
            headshot), 'events' ([t_seconds, driver_number, position] from
            /position), 'gaps' (per-driver decimated [t_seconds, gap] samples
            from /intervals; gap is float seconds or a '+N LAPS' string) and
            'duration' (race seconds). Payload is typically 100-300 KB.
        """
        logger.info(
            "event=tool_call tool=get_race_replay_view session_key=%s", session_key
        )
        positions = positions_service.get_positions(PositionsInput(session_key=session_key))
        if not positions:
            return json.dumps({"drivers": [], "events": [], "gaps": {}, "duration": 0})

        resolved_key = positions[0].session_key
        intervals = intervals_service.get_intervals(IntervalsInput(session_key=resolved_key))
        drivers = drivers_service.get_drivers(DriversInput(session_key=resolved_key))

        t0 = min(_parse_ts(p.date) for p in positions)
        t_end = max(_parse_ts(p.date) for p in positions)

        def seconds(ts: str) -> float:
            return round((_parse_ts(ts) - t0).total_seconds(), 3)

        events = sorted(
            ([seconds(p.date), p.driver_number, p.position] for p in positions),
            key=lambda e: e[0],
        )

        gaps: dict[int, list[list]] = {}
        for driver_intervals in _group_by_driver(intervals):
            stride = max(1, len(driver_intervals) // _MAX_GAP_SAMPLES)
            driver = driver_intervals[0].driver_number
            gaps[driver] = [
                [seconds(iv.date), iv.gap_to_leader]
                for iv in driver_intervals[::stride]
            ]

        payload = {
            "session_key": resolved_key,
            "duration": seconds(t_end.isoformat()),
            "drivers": [
                {
                    "driver_number": d.driver_number,
                    "name_acronym": d.name_acronym,
                    "team_name": d.team_name,
                    "team_colour": d.team_colour,
                    "headshot_url": d.headshot_url,
                }
                for d in drivers
            ],
            "events": events,
            "gaps": gaps,
        }
        result = json.dumps(payload)
        logger.info(
            "event=race_replay_payload session_key=%s drivers=%d events=%d bytes=%d",
            resolved_key,
            len(drivers),
            len(events),
            len(result),
        )
        return result


def _group_by_driver(intervals) -> list[list]:
    """Group Interval models by driver_number, each group sorted by date."""
    groups: dict[int, list] = {}
    for iv in intervals:
        groups.setdefault(iv.driver_number, []).append(iv)
    for group in groups.values():
        group.sort(key=lambda iv: iv.date)
    return list(groups.values())
