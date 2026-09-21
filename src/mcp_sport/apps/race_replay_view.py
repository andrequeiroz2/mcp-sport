"""MCP App: animated race replay view (task 06 — v2).

Bar-chart-race style replay: cars stacked by official position, checkered
treadmill paced by the leader (new lap opens when the leader crosses), tyre
compound badges (F1 convention: red S / yellow M / white H), per-sector times
with broadcast colors (purple = overall best so far, green = personal best,
yellow = slower), PIT badges and a Safety Car / VSC banner.

Data: /position (order) + /intervals (gaps) + /laps (sectors, leader laps)
+ /stints (tyres) + /pit (pit windows) + /race_control (SC/VSC/red flag)
+ /drivers + /sessions + /meetings (header) + /weather (track condition)
+ /session_result (retirements). Sector colors are recomputed in the view
at the displayed instant; the payload still carries unused baked colors.

Fallback: hosts without MCP Apps support receive the same payload as JSON text.
"""

import json
import re
from datetime import datetime
from typing import Any

from fastmcp import FastMCP
from fastmcp.apps import AppConfig, ResourceCSP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.drivers import DriversInput
from mcp_sport.schemas.intervals import IntervalsInput
from mcp_sport.schemas.laps import LapsInput
from mcp_sport.schemas.meetings import MeetingsInput
from mcp_sport.schemas.pit_stops import PitStopsInput
from mcp_sport.schemas.positions import PositionsInput
from mcp_sport.schemas.race_control import RaceControlInput
from mcp_sport.schemas.session_results import SessionResultsInput
from mcp_sport.schemas.sessions import SessionsInput
from mcp_sport.schemas.stints import StintsInput
from mcp_sport.schemas.weather import WeatherInput
from mcp_sport.services import drivers as drivers_service
from mcp_sport.services import intervals as intervals_service
from mcp_sport.services import laps as laps_service
from mcp_sport.services import meetings as meetings_service
from mcp_sport.services import pit_stops as pit_stops_service
from mcp_sport.services import positions as positions_service
from mcp_sport.services import race_control as race_control_service
from mcp_sport.services import session_results as session_results_service
from mcp_sport.services import sessions as sessions_service
from mcp_sport.services import stints as stints_service
from mcp_sport.services import weather as weather_service

logger = get_logger("tools")

VIEW_URI = "ui://mcp-sport/race-replay.html"

# External origins the view loads: ext-apps JS SDK (unpkg) and F1 headshots.
_CSP = ResourceCSP(
    resource_domains=["https://unpkg.com", "https://media.formula1.com"]
)

# Target gap samples per driver after decimation (payload vs. smoothness).
_MAX_GAP_SAMPLES = 300

# Sector color codes embedded in the payload (precomputed server-side,
# broadcast-style "best so far" — see _compute_sector_colors).
_SECTOR_NO_TIME = -1
_SECTOR_SLOWER = 0    # yellow: worse than personal best
_SECTOR_PB = 1        # green: personal best so far
_SECTOR_OVERALL = 2   # purple: overall best so far

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
  .lapcounter { font-size: 14px; font-weight: 800; color: #9d9dab;
                font-variant-numeric: tabular-nums; }
  .hud button {
    background: #2b2b3a; color: #e8e8ec; border: 0; border-radius: 6px;
    padding: 6px 12px; cursor: pointer; font-weight: 700;
  }
  .hud button:hover { background: #3a3a4d; }
  .hud select { background: #2b2b3a; color: #e8e8ec; border: 0; border-radius: 6px; padding: 5px; }
  .progress { flex: 1; accent-color: #e10600; }
  .track { position: relative; height: 640px; overflow: hidden;
           background: #1a1a26; border-radius: 8px; }
  .strip {
    position: absolute; top: 0; bottom: 0; left: 580px; width: 26px;
    background-image:
      linear-gradient(45deg, #d8d8d8 25%, #2b2b2b 25%, #2b2b2b 75%, #d8d8d8 75%),
      linear-gradient(45deg, #d8d8d8 25%, #2b2b2b 25%, #2b2b2b 75%, #d8d8d8 75%);
    background-size: 13px 13px;
    background-position: 0 0, 6.5px 6.5px;
    opacity: 0.9; border-radius: 3px;
  }
  .strip.flash { box-shadow: 0 0 14px 3px rgba(255,255,255,0.55); }
  .car {
    position: absolute; top: 4px; left: 0; height: 26px;
    display: flex; align-items: center; gap: 6px; padding: 0 8px 0 0;
    border-radius: 13px; background: #2b2b3a;
    transition: transform 0.55s ease;
    will-change: transform;
  }
  .car .photo { width: 24px; height: 24px; border-radius: 50%; object-fit: cover;
                background: #444; margin-left: 1px; }
  .car .acr { font-size: 12px; font-weight: 800; letter-spacing: 0.5px; width: 30px; }
  .car .gap { font-size: 10px; color: #b9b9c7; font-variant-numeric: tabular-nums;
              width: 52px; }
  .car .pos {
    position: absolute; left: -26px; width: 20px; text-align: right;
    font-size: 12px; font-weight: 800; color: #9d9dab;
  }
  .car.p1 .pos { color: #ffd700; }
  .car.flash { box-shadow: 0 0 0 2px #ffd700; }
  .car.retired { opacity: 0.45; }
  .tyre {
    width: 18px; height: 18px; border-radius: 50%; flex: none;
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 900;
  }
  .sectors { display: flex; gap: 3px; }
  .sec {
    font-size: 10px; font-variant-numeric: tabular-nums; font-weight: 700;
    background: #15151e; border-radius: 4px; padding: 2px 4px; min-width: 44px;
    text-align: center; color: #6d6d80;
  }
  .sec.yellow { color: #e8e000; }
  .sec.green { color: #00d060; }
  .sec.purple { color: #c26bff; }
  .laptime {
    font-size: 10px; font-variant-numeric: tabular-nums; font-weight: 700;
    color: #fff; min-width: 68px; text-align: right;
  }
  .pitbadge {
    font-size: 9px; font-weight: 900; background: #e10600; color: #fff;
    border-radius: 4px; padding: 2px 5px; letter-spacing: 0.5px;
  }
  .outbadge {
    font-size: 9px; font-weight: 900; background: #6e6e7a; color: #fff;
    border-radius: 4px; padding: 2px 5px; letter-spacing: 0.5px;
  }
  .empty { padding: 24px; text-align: center; color: #9d9dab; }
  .header {
    position: relative; display: flex; justify-content: space-between; align-items: center;
    gap: 16px; margin-bottom: 10px; padding-bottom: 10px;
    border-bottom: 1px solid #2b2b3a;
  }
  .header-main { display: flex; align-items: center; gap: 10px; min-width: 0; }
  .racestatus {
    display: none; position: absolute; left: 50%; transform: translateX(-50%);
    padding: 4px 14px; border-radius: 6px;
    font-size: 13px; font-weight: 800; letter-spacing: 1px; white-space: nowrap;
  }
  .racestatus.on { display: block; }
  .racestatus.sc, .racestatus.vsc { background: #b8a400; color: #15151e; }
  .racestatus.red { background: #e10600; color: #fff; }
  .flag { width: 40px; height: 27px; object-fit: cover; border-radius: 3px; background: #2b2b3a; }
  .htitle { font-size: 15px; font-weight: 800; }
  .hsub { font-size: 12px; color: #9d9dab; }
  .header-meta {
    margin-left: auto; flex: none; text-align: right; white-space: nowrap;
    font-size: 12px; font-variant-numeric: tabular-nums;
  }
  .hstart { color: #b9b9c7; }
  .cond { font-weight: 800; letter-spacing: 0.6px; margin-left: 8px; }
  .cond.dry { color: #00d060; }
  .cond.wet { color: #4db4ff; }
  .htemps { color: #e8e8ec; }
</style>
</head>
<body>
<div class="wrap">
  <div class="header" id="header"></div>
  <div class="hud">
    <button id="play">▶ Play</button>
    <select id="speed">
      <option value="1">1x</option>
      <option value="10">10x</option>
      <option value="30">30x</option>
      <option value="60" selected>60x</option>
      <option value="300">300x</option>
    </select>
    <span class="clock" id="clock">00:00:00</span>
    <span class="lapcounter" id="lapcounter"></span>
    <input type="range" class="progress" id="progress" min="0" max="1000" value="0">
  </div>
  <div class="track" id="track"><div class="empty">Loading race…</div></div>
</div>
<script type="module">
  import { App } from "https://unpkg.com/@modelcontextprotocol/ext-apps@0.4.0/app-with-deps";

  const app = new App({ name: "F1 Race Replay", version: "2.0.0" });

  const ROW_H = 29;          // px per position row
  const TRACK_LEFT = 30;     // px offset for position labels
  const STRIP_W = 13;        // checker pattern tile px (one lap of scroll)

  const TYRE_STYLE = {
    SOFT:         { bg: "#e8002d", fg: "#fff", letter: "S" },
    MEDIUM:       { bg: "#fff200", fg: "#15151e", letter: "M" },
    HARD:         { bg: "#f0f0f0", fg: "#15151e", letter: "H" },
    INTERMEDIATE: { bg: "#43b02a", fg: "#fff", letter: "I" },
    WET:          { bg: "#0067ff", fg: "#fff", letter: "W" },
  };
  let data = null;
  let raceTime = 0, playing = false, speed = 60, lastFrame = null;
  let eventIdx = 0;
  let lastLeaderLap = 0;
  const order = [];
  const cars = new Map();

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
  function fmtSec(v) { return typeof v === "number" ? v.toFixed(3) : "—"; }
  function fmtLap(seconds) {
    if (typeof seconds !== "number") return "—";
    const totalMs = Math.round(seconds * 1000);
    const mins = Math.floor(totalMs / 60000);
    const secs = Math.floor((totalMs % 60000) / 1000);
    const ms = totalMs % 1000;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}:${String(ms).padStart(3, "0")}`;
  }

  function fmtStart(iso, offset) {
    if (!iso) return "";
    const d = new Date(iso);
    let shift = 0;
    if (offset) {
      const sign = offset.trim().startsWith("-") ? -1 : 1;
      const parts = offset.replace("-", "").split(":").map(Number);
      shift = sign * ((parts[0] || 0) * 60 + (parts[1] || 0));
    }
    const local = new Date(d.getTime() + shift * 60000);
    const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    const dd = String(local.getUTCDate()).padStart(2, "0");
    const hh = String(local.getUTCHours()).padStart(2, "0");
    const mm = String(local.getUTCMinutes()).padStart(2, "0");
    return `${dd} ${months[local.getUTCMonth()]} ${local.getUTCFullYear()}  ${hh}:${mm}`;
  }

  function weatherAt(t) {
    const arr = data.weather;
    if (!arr || !arr.length) return null;
    let lo = 0, hi = arr.length - 1;
    if (t < arr[0][0]) return arr[0];
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (arr[mid][0] <= t) lo = mid; else hi = mid - 1;
    }
    return arr[lo];
  }

  function renderHeader() {
    const r = data.race;
    const header = $("header");
    if (!r) { header.style.display = "none"; return; }
    header.style.display = "";
    const place = [r.circuit_short_name, r.location, r.country_name].filter(Boolean).join(" · ");
    header.innerHTML =
      `<div class="header-main">` +
        (r.country_flag ? `<img class="flag" src="${r.country_flag}" alt="">` : "") +
        `<div><div class="htitle">${r.meeting_name ?? r.circuit_short_name ?? ""}</div>` +
        `<div class="hsub">${place}</div></div></div>` +
      `<div class="racestatus" id="racestatus"></div>` +
      `<div class="header-meta">` +
        `<div class="hstart">${r.session_name ?? "Race"} · ${fmtStart(r.date_start, r.gmt_offset)}</div>` +
        `<div><span class="cond" id="cond"></span> <span class="htemps" id="temps"></span></div>` +
      `</div>`;
  }

  function renderConditions() {
    const sample = weatherAt(raceTime);
    const cond = $("cond");
    const temps = $("temps");
    if (!cond || !temps) return;
    if (!sample) { cond.textContent = ""; temps.textContent = ""; return; }
    const wet = sample[3] === 1;
    cond.textContent = wet ? "WET" : "DRY";
    cond.className = "cond " + (wet ? "wet" : "dry");
    const air = sample[1], track = sample[2], hum = sample[4];
    const bits = [];
    if (typeof air === "number") bits.push(`Air ${air.toFixed(1)}°C`);
    if (typeof track === "number") bits.push(`Track ${track.toFixed(1)}°C`);
    if (typeof hum === "number") bits.push(`${hum.toFixed(0)}%`);
    temps.textContent = bits.join("  ·  ");
  }

  // binary search: index of the last lap with t_start <= t (-1 if none)
  function lapIndexAt(laps, t) {
    if (!laps || !laps.length || t < laps[0][1]) return -1;
    let lo = 0, hi = laps.length - 1;
    while (lo < hi) { const mid = (lo + hi + 1) >> 1; (laps[mid][1] <= t ? lo = mid : hi = mid - 1); }
    return lo;
  }
  function lapAt(laps, t) {
    const i = lapIndexAt(laps, t);
    return i < 0 ? null : laps[i];
  }

  function gapAt(driver, t) {
    const arr = data.gaps[driver];
    if (!arr || !arr.length) return null;
    let lo = 0, hi = arr.length - 1;
    if (t <= arr[0][0]) return arr[0][1];
    if (t >= arr[hi][0]) return arr[hi][1];
    while (lo < hi - 1) { const mid = (lo + hi) >> 1; (arr[mid][0] <= t ? lo = mid : hi = mid); }
    const [t0, g0] = arr[lo], [t1, g1] = arr[hi];
    if (typeof g0 !== "number" || typeof g1 !== "number") return g0;
    return g0 + (g1 - g0) * ((t - t0) / (t1 - t0));
  }

  function tyreAt(driver, lapNumber) {
    const stints = data.stints[driver];
    if (!stints || lapNumber == null) return null;
    for (const [start, end, compound] of stints)
      if (lapNumber >= start && lapNumber <= end) return compound;
    return null;
  }

  function inPit(driver, t) {
    const pits = data.pits[driver];
    if (!pits) return false;
    return pits.some(([a, b]) => t >= a && t <= b);
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

  // One purple per sector at race time t: the single fastest time set so far.
  // Anyone who held it earlier and is still showing that time goes green.
  function bestsAt(t) {
    const overall = [
      { time: Infinity, driver: null, at: Infinity },
      { time: Infinity, driver: null, at: Infinity },
      { time: Infinity, driver: null, at: Infinity },
    ];
    const personal = new Map();
    for (const [driverKey, laps] of Object.entries(data.laps)) {
      const driver = Number(driverKey);
      const pb = [Infinity, Infinity, Infinity];
      for (let n = 0; n < laps.length; n++) {
        const lap = laps[n];
        const tStart = lap[1], dur = lap[2], next = laps[n + 1];
        for (let i = 0; i < 3; i++) {
          const value = lap[3 + i];
          if (typeof value !== "number") continue;
          const at = (typeof dur === "number" && dur > 0)
            ? tStart + dur * ((i + 1) / 3)
            : (next ? next[1] : Infinity);
          if (at > t) continue;
          if (value < pb[i]) pb[i] = value;
          const rec = overall[i];
          const faster = value < rec.time - 0.0005;
          const tieEarlier = Math.abs(value - rec.time) <= 0.0005 && at < rec.at;
          if (faster || tieEarlier) overall[i] = { time: value, driver, at };
        }
      }
      personal.set(driver, pb);
    }
    return { overall, personal };
  }

  function sectorClass(driver, i, value, bests) {
    if (typeof value !== "number") return "";
    const rec = bests.overall[i];
    if (rec.driver === driver && Math.abs(value - rec.time) < 0.0005) return "purple";
    const pb = bests.personal.get(driver);
    if (pb && pb[i] < Infinity && Math.abs(value - pb[i]) < 0.0005) return "green";
    return "yellow";
  }

  function renderSectors(el, driver, laps, t, bests) {
    const boxes = el.querySelectorAll(".sec");
    const idx = lapIndexAt(laps, t);
    if (idx < 0) {
      boxes.forEach(b => { b.textContent = "—"; b.className = "sec"; });
      const empty = el.querySelector(".laptime");
      if (empty) empty.textContent = "—";
      return;
    }
    const cur = laps[idx];
    const prev = idx > 0 ? laps[idx - 1] : null;
    const [, tStart, dur] = cur;
    // Reveal sectors by lap progress, not cumulative sector sums: the sums
    // equal the lap duration, so S3 would only reveal exactly when the next
    // lap starts (and would never be shown).
    const frac = (typeof dur === "number" && dur > 0)
      ? Math.min(Math.max((t - tStart) / dur, 0), 1) : 0;
    for (let i = 0; i < 3; i++) {
      const src = frac >= (i + 1) / 3 ? cur : prev;
      if (!src || typeof src[3 + i] !== "number") {
        boxes[i].textContent = "—";
        boxes[i].className = "sec";
        continue;
      }
      boxes[i].textContent = fmtSec(src[3 + i]);
      boxes[i].className = "sec " + sectorClass(driver, i, src[3 + i], bests);
    }
    const total = el.querySelector(".laptime");
    const done = frac >= 1 ? cur : prev;
    const lapDur = done ? done[2] : null;
    total.textContent = fmtLap(lapDur);
  }

  function render() {
    // treadmill follows the leader
    const leader = order[0];
    const leaderLap = leader != null ? lapAt(data.laps[leader], raceTime) : null;
    let fraction = 0, lapNum = 0;
    if (leaderLap) {
      lapNum = leaderLap[0];
      const [, tStart, dur] = leaderLap;
      fraction = (typeof dur === "number" && dur > 0)
        ? Math.min(Math.max((raceTime - tStart) / dur, 0), 1) : 0;
    }
    const strip = document.querySelector(".strip");
    if (strip) {
      const off = -((lapNum - 1 + fraction) * STRIP_W * 4);
      strip.style.backgroundPosition = `${off}px 0, ${off + 6.5}px 6.5px`;
      if (lapNum !== lastLeaderLap && lapNum > 0) {
        strip.classList.add("flash");
        setTimeout(() => strip.classList.remove("flash"), 600);
        lastLeaderLap = lapNum;
      }
    }
    $("lapcounter").textContent =
      lapNum > 1 || fraction > 0 ? `LAP ${Math.max(lapNum, 1)}/${data.total_laps}` : "GRID";

    const STATUS_LABEL = { VSC: "VIRTUAL SAFETY CAR", SC: "SAFETY CAR", RED: "RACE SUSPENDED" };
    const sc = (data.sc || []).find(([a, b]) => raceTime >= a && raceTime <= b);
    const banner = $("racestatus");
    if (banner) {
      banner.className = "racestatus" + (sc ? " on " + String(sc[2]).toLowerCase() : "");
      banner.textContent = sc ? (STATUS_LABEL[sc[2]] || sc[2]) : "";
    }

    const bests = bestsAt(raceTime);
    for (let i = 0; i < order.length; i++) {
      const driver = order[i];
      const el = cars.get(driver);
      if (!el) continue;
      const gap = gapAt(driver, raceTime);
      const lapped = typeof gap === "string";
      const secs = typeof gap === "number" ? gap : null;
      el.style.transform = `translate(${TRACK_LEFT}px, ${i * ROW_H}px)`;
      el.classList.toggle("p1", i === 0);
      el.querySelector(".pos").textContent = i + 1;
      el.querySelector(".gap").textContent =
        i === 0 ? "LEADER" : lapped ? gap : secs !== null ? "+" + secs.toFixed(1) + "s" : "";

      const lap = lapAt(data.laps[driver], raceTime);
      renderSectors(el, driver, data.laps[driver], raceTime, bests);

      const tyre = tyreAt(driver, lap ? lap[0] : null);
      const tyreEl = el.querySelector(".tyre");
      const style = tyre && TYRE_STYLE[tyre];
      tyreEl.style.background = style ? style.bg : "#3a3a4d";
      tyreEl.style.color = style ? style.fg : "#9d9dab";
      tyreEl.textContent = style ? style.letter : "?";

      el.querySelector(".pitbadge").style.display = inPit(driver, raceTime) ? "" : "none";
      const retired = (data.retirements || []).find(row => row[0] === driver);
      const out = el.querySelector(".outbadge");
      const abandoned = retired && raceTime >= retired[1];
      el.classList.toggle("retired", !!abandoned);
      out.style.display = abandoned ? "" : "none";
      if (abandoned) {
        out.textContent = retired[2];
        el.querySelector(".gap").textContent = "";
        el.querySelectorAll(".sec").forEach(box => { box.textContent = "--"; box.className = "sec"; });
        el.querySelector(".laptime").textContent = "--:--:----";
      }
    }
    renderConditions();
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
    track.innerHTML = '<div class="strip"></div>';
    cars.clear(); order.length = 0; eventIdx = 0; lastLeaderLap = 0;
    renderHeader();
    for (const d of data.drivers) {
      const el = document.createElement("div");
      el.className = "car";
      el.style.borderLeft = "4px solid " + (d.team_colour ? "#" + d.team_colour : "#555");
      el.innerHTML =
        `<span class="pos"></span>` +
        (d.headshot_url ? `<img class="photo" src="${d.headshot_url}" alt="">` : `<div class="photo"></div>`) +
        `<span class="acr">${d.name_acronym ?? d.driver_number}</span>` +
        `<span class="tyre"></span>` +
        `<span class="sectors"><span class="sec">—</span><span class="sec">—</span><span class="sec">—</span></span>` +
        `<span class="laptime">—</span>` +
        `<span class="gap"></span>` +
        `<span class="pitbadge" style="display:none">PIT</span>` +
        `<span class="outbadge" style="display:none">OUT</span>`;
      track.appendChild(el);
      cars.set(d.driver_number, el);
      order.push(d.driver_number);
    }
    applyEvents(raceTime);
    render();
  }

  $("play").onclick = () => {
    if (!data) return;
    if (raceTime >= data.duration) { raceTime = 0; build(); }
    playing = !playing;
    $("play").textContent = playing ? "⏸ Pause" : "▶ Play";
    lastFrame = null;
    if (playing) requestAnimationFrame(tick);
  };
  $("speed").onchange = (e) => { speed = Number(e.target.value); };
  $("progress").oninput = (e) => {
    if (!data) return;
    raceTime = (Number(e.target.value) / 1000) * data.duration;
    build();
  };

  app.ontoolresult = (result) => {
    try {
      const text = result?.content?.find(c => c.type === "text")?.text ?? "";
      if (result?.isError || (text && text[0] !== "{" && text[0] !== "[")) {
        $("track").innerHTML = '<div class="empty">' + (text || "Tool error") + "</div>";
        return;
      }
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


def _group_by_driver(items: list, key: str) -> dict[int, list]:
    """Group models by driver_number, each group sorted by the given date attr."""
    groups: dict[int, list] = {}
    for item in items:
        groups.setdefault(item.driver_number, []).append(item)
    for group in groups.values():
        group.sort(key=lambda item: getattr(item, key))
    return groups


def _compute_sector_colors(laps: list) -> dict[int, tuple[int, int, int]]:
    """Compute broadcast-style sector colors (best-so-far) for every lap.

    Laps are processed in chronological completion order. Per sector:
    purple = new overall best at that moment, green = new personal best,
    yellow = slower, -1 = no time.

    Returns:
        Map id(lap) -> (color_s1, color_s2, color_s3) using the _SECTOR_*
        codes. id() is safe here: laps are alive for the whole payload build.
    """
    def completion(lap) -> datetime:
        end = _parse_ts(lap.date_start)
        if isinstance(lap.lap_duration, (int, float)):
            from datetime import timedelta

            end = end + timedelta(seconds=lap.lap_duration)
        return end

    ordered = sorted(laps, key=completion)
    personal_best: dict[int, list[float | None]] = {}
    overall_best: list[float | None] = [None, None, None]
    colors: dict[int, tuple[int, int, int]] = {}

    for lap in ordered:
        sectors = [lap.duration_sector_1, lap.duration_sector_2, lap.duration_sector_3]
        pb = personal_best.setdefault(lap.driver_number, [None, None, None])
        lap_colors = []
        for i, value in enumerate(sectors):
            if not isinstance(value, (int, float)):
                lap_colors.append(_SECTOR_NO_TIME)
                continue
            if overall_best[i] is None or value <= overall_best[i]:
                lap_colors.append(_SECTOR_OVERALL)
                overall_best[i] = value
                pb[i] = value if pb[i] is None else min(pb[i], value)
            elif pb[i] is None or value <= pb[i]:
                lap_colors.append(_SECTOR_PB)
                pb[i] = value
            else:
                lap_colors.append(_SECTOR_SLOWER)
        colors[id(lap)] = tuple(lap_colors)
    return colors


def _neutral_kind(message: str, flag: str | None, category: str | None) -> str | None:
    """Classify a race-control message as a neutralisation, if it opens one."""
    text = message.upper()
    flag_name = (flag or "").upper()
    if "VSC" in text:
        return "VSC"
    if category == "SafetyCar" or "SAFETY CAR" in text:
        return "SC"
    # Word boundary: "CHEQUERED FLAG" contains the letters of "RED FLAG".
    if flag_name == "RED" or re.search(r"\bRED FLAG\b", text) or "SUSPENDED" in text:
        return "RED"
    return None


def _neutral_ends(message: str, flag: str | None, kind: str) -> bool:
    """Whether this message closes the open neutralisation of the given kind."""
    text = message.upper()
    flag_name = (flag or "").upper()
    if kind in ("SC", "VSC"):
        return "ENDING" in text or "IN THIS LAP" in text
    return (
        "ENDING" in text
        or "RESUMED" in text
        or "RESTART" in text
        or bool(re.search(r"\bGREEN FLAG\b", text))
    )


def _neutralisation_windows(messages: list, seconds, duration: float) -> list[list]:
    """Build [t_start, t_end, kind] windows for SC, VSC and red-flag stoppages."""
    windows: list[list] = []
    open_window: list | None = None
    for msg in sorted(messages, key=lambda item: item.date or ""):
        if not msg.date:
            continue
        text = (msg.message or "").upper()
        kind = _neutral_kind(msg.message or "", msg.flag, msg.category)
        t = seconds(msg.date)
        if (
            open_window is not None
            and t >= open_window[0]
            and _neutral_ends(msg.message or "", msg.flag, open_window[1])
        ):
            windows.append([open_window[0], t, open_window[1]])
            open_window = None
            continue
        opens = kind == "RED" or (kind in ("SC", "VSC") and "DEPLOYED" in text)
        if open_window is None and opens and not _neutral_ends(msg.message or "", msg.flag, kind or ""):
            open_window = [t, kind]
    if open_window is not None:
        windows.append([open_window[0], duration, open_window[1]])
    return windows


def _retirements(results: list, laps_payload: dict[int, list[list]], duration: float) -> list[list]:
    """Permanent abandonment markers: [driver_number, t_seconds, label].

    DNF becomes visible at the end of the driver's last completed lap.
    DNS is visible from the start. The tag stays on for the rest of the replay.
    """
    markers: list[list] = []
    for result in results:
        if result.dnf:
            label = "OUT"
        elif result.dns:
            label = "DNS"
        else:
            continue
        driver_laps = laps_payload.get(result.driver_number, [])
        if result.dns or not result.number_of_laps:
            t_out = 0.0
        else:
            last = next((lap for lap in driver_laps if lap[0] == result.number_of_laps), None)
            if last is None:
                t_out = duration
            elif isinstance(last[2], (int, float)):
                t_out = round(last[1] + last[2], 3)
            else:
                t_out = last[1]
        markers.append([result.driver_number, t_out, label])
    return markers


def register(mcp: FastMCP) -> None:
    """Register the race replay view (MCP App, task 06) on the server."""

    @mcp.resource(VIEW_URI, meta={"ui": {"csp": _CSP.model_dump(by_alias=True, exclude_none=True)}})
    def race_replay_view() -> str:
        """HTML view for the animated race replay MCP App."""
        return _VIEW_HTML

    @mcp.tool(app=AppConfig(resource_uri=VIEW_URI, csp=_CSP))
    def get_race_replay_view(
        session_key: int | str | None = None,
    ) -> str:
        """Replay a race as an animated position chart (bar-chart-race style).

        MCP App (task 06): in hosts supporting the MCP Apps extension, renders
        cars stacked by official position with a checkered treadmill paced by
        the leader (a new lap opens when the leader crosses), tyre compound
        badges (red S / yellow M / white H), per-sector times with broadcast
        colors recomputed at the displayed instant (one purple per sector,
        green = personal best, yellow = slower), the lap time as MM:SS:mmm,
        PIT badges, a centered Safety Car / VSC / race-suspended banner, and
        a header with circuit, local start time and track conditions. Retired
        cars show a permanent OUT or DNS tag and drop gap, sectors and lap
        time. In other hosts the same payload is returned as JSON text.

        Args:
            session_key: int | str — optional, positive int or 'latest'.
                Defaults to 'latest' when omitted. RACE session identifier;
                use get_sessions with session_type='Race' to discover it.
                During a live race, 'latest' yields a snapshot of the data
                available so far.

        Returns:
            str: JSON object with 'drivers' (meta), 'events' (position
            changes [t, driver, position]), 'gaps' (decimated [t, gap] per
            driver; gap is float seconds or '+N LAPS'), 'laps' (per driver:
            [lap, t_start, lap_duration, s1, s2, s3, color1, color2, color3];
            the baked colors are best-so-far at set time and the HTML view
            ignores them, recomputing a single live purple), 'stints', 'pits',
            'retirements' ([driver, t, 'OUT'|'DNS']), 'sc' ([t_start, t_end,
            'VSC'|'SC'|'RED']), 'weather', 'race' (meeting, circuit, flag,
            local start), 'total_laps', 'duration' and 'session_key'.
            Times are seconds from lights-out (lap 1), not the first position
            sample. Payload is typically 200-400 KB. Not response-cached.
        """
        if session_key is None or (isinstance(session_key, str) and not session_key.strip()):
            session_key = "latest"
        logger.info(
            "event=tool_call tool=get_race_replay_view session_key=%s", session_key
        )
        positions = positions_service.get_positions(PositionsInput(session_key=session_key))
        if not positions:
            return json.dumps({"drivers": [], "events": [], "gaps": {}, "duration": 0})

        resolved_key = positions[0].session_key
        intervals = intervals_service.get_intervals(IntervalsInput(session_key=resolved_key))
        drivers = drivers_service.get_drivers(DriversInput(session_key=resolved_key))
        laps = laps_service.get_laps(LapsInput(session_key=resolved_key))
        stints = stints_service.get_stints(StintsInput(session_key=resolved_key))
        pit_stops = pit_stops_service.get_pit_stops(PitStopsInput(session_key=resolved_key))
        race_control = race_control_service.get_race_control(
            RaceControlInput(session_key=resolved_key)
        )
        sessions = sessions_service.get_sessions(SessionsInput(session_key=resolved_key))
        session = sessions[0] if sessions else None
        meeting = None
        if session is not None:
            meetings = meetings_service.get_meetings(
                MeetingsInput(meeting_key=session.meeting_key)
            )
            meeting = meetings[0] if meetings else None
        weather = weather_service.get_weather(WeatherInput(session_key=resolved_key))
        session_results = session_results_service.get_session_results(
            SessionResultsInput(session_key=resolved_key)
        )

        # t0 is lights-out (lap 1), not the first position sample. OpenF1 starts
        # /position on the grid / formation lap — in Barcelona 2026 that is
        # ~54 minutes before the race. Events before t0 still apply at t=0 and
        # build the starting order.
        lap1_starts = [
            _parse_ts(lap.date_start)
            for lap in laps
            if lap.lap_number == 1 and lap.date_start is not None
        ]
        t0 = min(lap1_starts) if lap1_starts else min(_parse_ts(p.date) for p in positions)
        t_end = max(_parse_ts(p.date) for p in positions)

        def seconds(ts: str) -> float:
            return round((_parse_ts(ts) - t0).total_seconds(), 3)

        duration = seconds(t_end.isoformat())

        events = sorted(
            ([seconds(p.date), p.driver_number, p.position] for p in positions),
            key=lambda e: e[0],
        )

        gaps: dict[int, list[list]] = {}
        for driver, driver_intervals in _group_by_driver(intervals, "date").items():
            stride = max(1, len(driver_intervals) // _MAX_GAP_SAMPLES)
            gaps[driver] = [
                [seconds(iv.date), iv.gap_to_leader]
                for iv in driver_intervals[::stride]
            ]

        sector_colors = _compute_sector_colors(laps)
        laps_payload: dict[int, list[list]] = {}
        for driver, driver_laps in _group_by_driver(laps, "date_start").items():
            laps_payload[driver] = [
                [
                    lap.lap_number,
                    seconds(lap.date_start),
                    lap.lap_duration,
                    lap.duration_sector_1,
                    lap.duration_sector_2,
                    lap.duration_sector_3,
                    *sector_colors[id(lap)],
                ]
                for lap in driver_laps
                if lap.date_start is not None
            ]

        total_laps = max((lap.lap_number for lap in laps), default=0)
        retirements = _retirements(session_results, laps_payload, duration)

        stints_payload: dict[int, list[list]] = {}
        for driver, driver_stints in _group_by_driver(stints, "lap_start").items():
            stints_payload[driver] = [
                [s.lap_start, s.lap_end if s.lap_end is not None else total_laps, s.compound]
                for s in driver_stints
            ]

        pits_payload: dict[int, list[list[float]]] = {}
        for stop in pit_stops:
            duration_s = stop.pit_duration or stop.lane_duration or stop.stop_duration
            if stop.date is None or not isinstance(duration_s, (int, float)):
                continue
            entry = seconds(stop.date)
            pits_payload.setdefault(stop.driver_number, []).append(
                [entry, round(entry + duration_s, 3)]
            )

        sc_payload = _neutralisation_windows(race_control, seconds, duration)

        weather_payload = [
            [
                seconds(sample.date),
                sample.air_temperature,
                sample.track_temperature,
                sample.rainfall,
                sample.humidity,
            ]
            for sample in sorted(weather, key=lambda item: item.date or "")
            if sample.date is not None
        ]
        info = meeting or session
        payload: dict[str, Any] = {
            "session_key": resolved_key,
            "duration": duration,
            "total_laps": total_laps,
            "race": {
                "meeting_name": meeting.meeting_name if meeting else None,
                "session_name": session.session_name if session else None,
                "country_name": info.country_name if info else None,
                "country_flag": meeting.country_flag if meeting else None,
                "circuit_short_name": info.circuit_short_name if info else None,
                "location": info.location if info else None,
                "date_start": session.date_start if session else None,
                "gmt_offset": session.gmt_offset if session else None,
            },
            "weather": weather_payload,
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
            "laps": laps_payload,
            "stints": stints_payload,
            "pits": pits_payload,
            "retirements": retirements,
            "sc": sc_payload,
        }
        result = json.dumps(payload)
        logger.info(
            "event=race_replay_payload session_key=%s drivers=%d events=%d laps=%d sc_windows=%d bytes=%d",
            resolved_key,
            len(drivers),
            len(events),
            len(laps),
            len(sc_payload),
            len(result),
        )
        return result
