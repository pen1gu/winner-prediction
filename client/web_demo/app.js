const matchesEl = document.getElementById("matches");
const statusEl = document.getElementById("statusText");
const reloadBtn = document.getElementById("reloadBtn");
const limitSelect = document.getElementById("limitSelect");
const template = document.getElementById("matchCardTemplate");

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

function renderMatches(matches) {
  matchesEl.innerHTML = "";

  if (!matches.length) {
    matchesEl.innerHTML = "<p>조회된 경기 데이터가 없습니다.</p>";
    return;
  }

  matches.forEach((match) => {
    const node = template.content.cloneNode(true);
    node.querySelector(".teams").textContent = `${match.home_team} vs ${match.away_team}`;
    node.querySelector(".score").textContent = `${formatNum(match.score.home)} : ${formatNum(match.score.away)}`;
    node.querySelector(".meta").textContent = [
      `리그: ${match.league_name || "-"}`,
      `라운드: ${match.match_round || "-"}`,
      `일시: ${toDisplayDate(match.match_date)}`,
      `경기장: ${match.stadium || "-"}`,
      `상태: ${match.finished ? "종료" : "진행 예정/중"}`
    ].join(" | ");

    const stats = node.querySelector(".stats");
    stats.appendChild(createStat("xG (홈/원정)", `${formatNum(match.stats.home_xg)} / ${formatNum(match.stats.away_xg)}`));
    stats.appendChild(createStat("점유율 (홈/원정)", `${formatNum(match.stats.home_possession, "%")} / ${formatNum(match.stats.away_possession, "%")}`));
    stats.appendChild(createStat("슈팅 (홈/원정)", `${formatNum(match.stats.home_shots)} / ${formatNum(match.stats.away_shots)}`));
    stats.appendChild(createStat("유효슈팅 (홈/원정)", `${formatNum(match.stats.home_shots_on_target)} / ${formatNum(match.stats.away_shots_on_target)}`));

    matchesEl.appendChild(node);
  });
}

async function loadMatches() {
  const limit = Number(limitSelect.value || 10);
  setStatus("데이터 로딩 중...");

  try {
    const response = await fetch(`/api/matches/latest?limit=${limit}`);
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.message || "알 수 없는 오류");
    }

    renderMatches(payload.matches || []);
    setStatus(`완료: ${payload.count}건`);
  } catch (error) {
    console.error(error);
    matchesEl.innerHTML = "<p>데이터를 불러오지 못했습니다.</p>";
    setStatus(`오류: ${error.message}`, true);
  }
}

reloadBtn.addEventListener("click", loadMatches);
window.addEventListener("DOMContentLoaded", loadMatches);
