/**
 * FastAPI: /api/v1/…
 * client/demo_server.py(8080): 목록만 /api/matches/latest — 예측·시각화는 FastAPI 필요
 */
let endpoints = {
  list: "/api/v1/matches/latest",
  prediction: (id) => `/api/v1/predictions/matches/${id}/outcomes`,
  teamStats: (id) => `/api/v1/visualization/matches/${id}/team-stats`,
  lineup: (id) => `/api/v1/visualization/matches/${id}/lineup-ratings`,
  hasV1: true,
};

const matchesEl = document.getElementById("matches");
const statusEl = document.getElementById("statusText");
const reloadBtn = document.getElementById("reloadBtn");
const limitSelect = document.getElementById("limitSelect");
const template = document.getElementById("matchCardTemplate");

/** @type {WeakMap<HTMLElement, boolean>} */
const detailLoaded = new WeakMap();

function toDisplayDate(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("ko-KR");
}

function formatNum(v, suffix = "") {
  if (v === null || v === undefined) return "-";
  return `${v}${suffix}`;
}

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

function createStat(label, value) {
  const box = document.createElement("div");
  box.className = "stat-box";
  box.innerHTML = `
    <div class="stat-label">${label}</div>
    <div class="stat-value">${value}</div>
  `;
  return box;
}

function apiErrorMessage(data, response) {
  if (!data) return response.statusText || "오류";
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((x) => x.msg || JSON.stringify(x)).join(", ");
  }
  return data.message || "요청 실패";
}

async function fetchJson(url) {
  const response = await fetch(url);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const err = new Error(apiErrorMessage(data, response));
    err.status = response.status;
    throw err;
  }
  return data;
}

function fmtPct(x) {
  return `${(x * 100).toFixed(1)}%`;
}

function fmtProb01(x) {
  return Number(x).toFixed(4);
}

function renderProbBars(homeName, awayName, home, draw, away, { showNumeric = true } = {}) {
  const sum = home + draw + away;
  const sumLine = showNumeric
    ? `<p class="prob-sum muted">소프트맥스 확률 합계: <strong>${fmtProb01(sum)}</strong> (이론상 1.0)</p>`
    : "";
  const num = (x) =>
    showNumeric
      ? `<div class="bar-numeric">표시 퍼센트: <strong>${fmtPct(x)}</strong> · 확률값(0~1): <strong>${fmtProb01(x)}</strong></div>`
      : "";

  return `
    <div class="detail-block">
      <h3 class="detail-title">승무패 예측</h3>
      ${sumLine}
      <div class="bar-row">
        <span class="bar-label">${escapeHtml(homeName)} 승</span>
        <div class="bar-track"><div class="bar-fill bar-home" style="width:${home * 100}%"></div></div>
        <span class="bar-pct">${fmtPct(home)}</span>
      </div>
      ${num(home)}
      <div class="bar-row">
        <span class="bar-label">무승부</span>
        <div class="bar-track"><div class="bar-fill bar-draw" style="width:${draw * 100}%"></div></div>
        <span class="bar-pct">${fmtPct(draw)}</span>
      </div>
      ${num(draw)}
      <div class="bar-row">
        <span class="bar-label">${escapeHtml(awayName)} 승</span>
        <div class="bar-track"><div class="bar-fill bar-away" style="width:${away * 100}%"></div></div>
        <span class="bar-pct">${fmtPct(away)}</span>
      </div>
      ${num(away)}
    </div>
  `;
}

function renderOutcomesStrip(homeTeam, awayTeam, outcomes) {
  const el = document.createElement("div");
  el.className = "outcomes-strip-inner";
  if (!outcomes || outcomes.home == null) {
    el.innerHTML = `<span class="outcomes-missing muted">예측 없음 (라인업 미비 또는 비활성)</span>`;
    return el;
  }
  const h = outcomes.home;
  const d = outcomes.draw;
  const a = outcomes.away;
  el.innerHTML = `
    <span class="outcomes-label muted">모델 승률</span>
    <span class="outcome-pill pill-home" title="확률값 ${fmtProb01(h)}">${escapeHtml(homeTeam)} ${fmtPct(h)}</span>
    <span class="outcome-pill pill-draw" title="확률값 ${fmtProb01(d)}">무 ${fmtPct(d)}</span>
    <span class="outcome-pill pill-away" title="확률값 ${fmtProb01(a)}">${escapeHtml(awayTeam)} ${fmtPct(a)}</span>
  `;
  return el;
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function renderTeamMetrics(homeName, awayName, metrics) {
  const rows = (metrics || []).filter(
    (m) => m.home != null || m.away != null
  );
  if (!rows.length) {
    return `<div class="detail-block"><h3 class="detail-title">팀 스탯 비교</h3><p class="muted">표시할 수치가 없습니다.</p></div>`;
  }
  let html = `<div class="detail-block"><h3 class="detail-title">팀 스탯 비교</h3>`;
  for (const m of rows) {
    const h = m.home != null ? Number(m.home) : 0;
    const a = m.away != null ? Number(m.away) : 0;
    const max = Math.max(h, a, 1e-6);
    html += `
      <div class="metric-group">
        <div class="metric-label">${escapeHtml(m.label)}</div>
        <div class="metric-dual">
          <span class="metric-team">${escapeHtml(homeName)}</span>
          <div class="bar-track metric-track"><div class="bar-fill bar-home" style="width:${(h / max) * 100}%"></div></div>
          <span class="metric-num">${m.home != null ? formatNum(m.home) : "-"}</span>
        </div>
        <div class="metric-dual">
          <span class="metric-team">${escapeHtml(awayName)}</span>
          <div class="bar-track metric-track"><div class="bar-fill bar-away" style="width:${(a / max) * 100}%"></div></div>
          <span class="metric-num">${m.away != null ? formatNum(m.away) : "-"}</span>
        </div>
      </div>
    `;
  }
  html += "</div>";
  return html;
}

function renderLineup(homeName, awayName, players) {
  if (!players || !players.length) {
    return `<div class="detail-block"><h3 class="detail-title">라인업 레이팅</h3><p class="muted">데이터가 없습니다.</p></div>`;
  }
  const maxR = Math.max(...players.map((p) => p.model_rating || 0), 1);
  let html = `<div class="detail-block"><h3 class="detail-title">라인업 모델 레이팅</h3>`;
  for (const p of players) {
    const side = p.is_home ? homeName : awayName;
    const w = ((p.model_rating || 0) / maxR) * 100;
    const mr = p.match_rating != null ? ` · 경기평점 ${p.match_rating}` : "";
    html += `
      <div class="lineup-row">
        <div class="lineup-meta">
          <span class="lineup-name">${escapeHtml(p.name)}</span>
          <span class="lineup-side">${escapeHtml(side)}${mr}</span>
        </div>
        <div class="bar-track"><div class="bar-fill ${p.is_home ? "bar-home" : "bar-away"}" style="width:${w}%"></div></div>
        <span class="lineup-rating">${formatNum(p.model_rating)}</span>
      </div>
    `;
  }
  html += "</div>";
  return html;
}

async function loadDetailPanel(matchId, homeName, awayName, panel) {
  const loading = panel.querySelector(".detail-loading");
  const content = panel.querySelector(".detail-content");
  loading.hidden = false;
  content.hidden = true;
  content.innerHTML = "";

  if (!endpoints.prediction) {
    loading.hidden = true;
    content.innerHTML =
      "<p class=\"muted\">예측·팀 스탯·라인업은 FastAPI 서버(<code>uvicorn server.app.main:app</code>)로 접속할 때만 사용할 수 있습니다.</p>";
    content.hidden = false;
    return;
  }

  let pred;
  let teamStats;
  let lineup;
  const errors = [];

  try {
    pred = await fetchJson(endpoints.prediction(matchId));
  } catch (e) {
    errors.push(`예측: ${e.message}`);
  }
  try {
    teamStats = await fetchJson(endpoints.teamStats(matchId));
  } catch (e) {
    errors.push(`팀 스탯: ${e.message}`);
  }
  try {
    lineup = await fetchJson(endpoints.lineup(matchId));
  } catch (e) {
    errors.push(`라인업: ${e.message}`);
  }

  let html = "";
  if (errors.length) {
    html += `<div class="detail-errors">${errors.map((t) => `<p>${escapeHtml(t)}</p>`).join("")}</div>`;
  }
  if (pred) {
    html += renderProbBars(
      pred.home_team_name || homeName,
      pred.away_team_name || awayName,
      pred.home,
      pred.draw,
      pred.away
    );
  }
  if (teamStats && teamStats.metrics) {
    html += renderTeamMetrics(
      teamStats.home_team_name || homeName,
      teamStats.away_team_name || awayName,
      teamStats.metrics
    );
  }
  if (lineup && lineup.players) {
    html += renderLineup(
      lineup.home_team_name || homeName,
      lineup.away_team_name || awayName,
      lineup.players
    );
  }

  loading.hidden = true;
  content.innerHTML = html || "<p class=\"muted\">표시할 데이터가 없습니다.</p>";
  content.hidden = false;
}

function renderMatches(matches) {
  matchesEl.innerHTML = "";

  if (!matches.length) {
    matchesEl.innerHTML = "<p>조회된 경기 데이터가 없습니다.</p>";
    return;
  }

  matches.forEach((match) => {
    const node = template.content.cloneNode(true);
    const card = node.querySelector(".match-card");
    card.dataset.matchId = String(match.match_id);

    node.querySelector(".teams").textContent = `${match.home_team} vs ${match.away_team}`;
    node.querySelector(".score").textContent = `${formatNum(match.score.home)} : ${formatNum(match.score.away)}`;
    node.querySelector(".meta").textContent = [
      `리그: ${match.league_name || "-"}`,
      `라운드: ${match.match_round || "-"}`,
      `일시: ${toDisplayDate(match.match_date)}`,
      `경기장: ${match.stadium || "-"}`,
      `상태: ${match.finished ? "종료" : "진행 예정/중"}`,
    ].join(" | ");

    const stripHost = node.querySelector(".outcomes-strip");
    stripHost.appendChild(
      renderOutcomesStrip(match.home_team, match.away_team, match.outcomes)
    );

    const stats = node.querySelector(".stats");
    stats.appendChild(
      createStat("xG (홈/원정)", `${formatNum(match.stats.home_xg)} / ${formatNum(match.stats.away_xg)}`)
    );
    stats.appendChild(
      createStat("점유율 (홈/원정)", `${formatNum(match.stats.home_possession, "%")} / ${formatNum(match.stats.away_possession, "%")}`)
    );
    stats.appendChild(
      createStat("슈팅 (홈/원정)", `${formatNum(match.stats.home_shots)} / ${formatNum(match.stats.away_shots)}`)
    );
    stats.appendChild(
      createStat("유효슈팅 (홈/원정)", `${formatNum(match.stats.home_shots_on_target)} / ${formatNum(match.stats.away_shots_on_target)}`)
    );

    const panel = node.querySelector(".detail-panel");
    const btn = node.querySelector(".btn-detail");
    btn.addEventListener("click", () => {
      const open = panel.hidden;
      panel.hidden = !open;
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      if (open && !detailLoaded.get(panel)) {
        detailLoaded.set(panel, true);
        loadDetailPanel(match.match_id, match.home_team, match.away_team, panel);
      }
    });

    matchesEl.appendChild(node);
  });
}

async function loadMatches() {
  const limit = Number(limitSelect.value || 10);
  setStatus("데이터 로딩 중…");

  try {
    const params = new URLSearchParams({ limit: String(limit) });
    if (endpoints.hasV1) params.set("include_outcomes", "true");
    const response = await fetch(`${endpoints.list}?${params.toString()}`);
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(apiErrorMessage(payload, response));
    }

    renderMatches(payload.matches || []);
    setStatus(`완료: ${payload.count}건`);
  } catch (error) {
    console.error(error);
    matchesEl.innerHTML = "<p>데이터를 불러오지 못했습니다.</p>";
    setStatus(`오류: ${error.message}`, true);
  }
}

async function initEndpoints() {
  try {
    const r = await fetch("/api/v1/health");
    if (r.ok) return;
  } catch (_) {
    /* ignore */
  }
  try {
    const r = await fetch("/api/health");
    if (r.ok) {
      endpoints = {
        list: "/api/matches/latest",
        prediction: null,
        teamStats: null,
        lineup: null,
        hasV1: false,
      };
    }
  } catch (_) {
    /* keep default FastAPI paths */
  }
}

reloadBtn.addEventListener("click", loadMatches);
window.addEventListener("DOMContentLoaded", async () => {
  await initEndpoints();
  loadMatches();
});
