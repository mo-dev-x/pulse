import { apiFetch, apiCall, requireAuth } from "./auth.js";
import { notify, runAsyncUI } from "./notify.js";
import { initLanguageControls } from "./i18n.js";
import { initThemeToggle, initOfflineBanner } from "./theme.js";

let dailyChart = null;
let weeklyChart = null;
let emotionChart = null;
let selectedZoneId = null;
let latestAnalyticsDate = null;

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();

  const dateInput = document.getElementById("analyticsDate");
  const today = new Date().toISOString().slice(0, 10);
  dateInput.value = today;
  dateInput.addEventListener("change", async () => {
    await loadAnalytics(dateInput.value);
  });

  await loadAnalytics(today);
});

async function loadAnalytics(dateValue) {
  latestAnalyticsDate = dateValue;
  const dateInput = document.getElementById("analyticsDate");

  await runAsyncUI({
    fn: () => Promise.all([
      apiCall("analytics/campus", () =>
        apiFetch(`/api/analytics/campus?date=${dateValue}`, { method: "GET" })
      ),
      loadDailySeries(dateValue),
      loadWeeklySeries(dateValue),
    ]),
    onLoad:    () => { if (dateInput) dateInput.disabled = true; },
    onSuccess: async ([campus, dailySeries, weeklySeries]) => {
      renderCampusOverview(campus);
      renderDailyChart(dailySeries);
      renderWeeklyChart(weeklySeries);
      renderEmotionChart(campus.campus_overview?.emotion_distribution || {});
      const defaultZone = (campus.zone_breakdown || []).find((zone) => zone.zone_id) || null;
      selectedZoneId = defaultZone?.zone_id || null;
      renderZoneBreakdown(campus.zone_breakdown || []);
      await loadZoneActivity(selectedZoneId);
    },
    onError:   (err) => {
      notify(err.message || "Could not load analytics. Check your connection and try again.", "error");
    },
    onFinally: () => { if (dateInput) dateInput.disabled = false; },
  });
}

async function loadDailySeries(dateValue) {
  const target = new Date(dateValue);
  const requests = [];
  for (let offset = 6; offset >= 0; offset -= 1) {
    const current = new Date(target);
    current.setDate(current.getDate() - offset);
    requests.push(apiFetch(`/api/analytics/daily?date=${current.toISOString().slice(0, 10)}`, { method: "GET" }));
  }
  return Promise.all(requests);
}

async function loadWeeklySeries(dateValue) {
  const target = new Date(dateValue);
  const monday = new Date(target);
  monday.setDate(target.getDate() - ((target.getDay() + 6) % 7));

  const requests = [];
  for (let offset = 3; offset >= 0; offset -= 1) {
    const current = new Date(monday);
    current.setDate(current.getDate() - offset * 7);
    requests.push(apiFetch(`/api/analytics/weekly?week_start=${current.toISOString().slice(0, 10)}`, { method: "GET" }));
  }
  return Promise.all(requests);
}

function renderCampusOverview(data) {
  const overview = data.campus_overview || {};
  const mood = overview.mood_label || "neutral";
  const titleMap = {
    positive: "Positive campus energy",
    neutral: "Balanced campus mood",
    negative: "Heavier campus mood",
    unknown: "Privacy-safe limited data",
  };

  const hero = document.getElementById("moodHero");
  hero.className = `mood-hero ${mood}`;
  document.getElementById("moodTitle").textContent = titleMap[mood] || titleMap.neutral;
  document.getElementById("moodSubtitle").textContent = `Updated for ${data.date}. ${data.disclaimer || ""}`.trim();
  document.getElementById("kpiPosts").textContent = String(overview.total_posts || overview.current_count || 0);
  document.getElementById("kpiSentiment").textContent = overview.avg_sentiment != null ? Number(overview.avg_sentiment).toFixed(2) : "—";

  const emotions = overview.emotion_distribution || {};
  const topEmotion = Object.entries(emotions).sort((a, b) => b[1] - a[1])[0];
  document.getElementById("kpiEmotion").textContent = topEmotion?.[0] || "—";

  const privacyBanner = document.getElementById("privacyBanner");
  const insufficient = overview.message || (overview.total_posts != null && overview.total_posts < 10);
  privacyBanner.hidden = !insufficient;
  if (insufficient) {
    privacyBanner.textContent = overview.message || "At least 10 posts are required before showing privacy-safe aggregate data.";
  }
}

function renderDailyChart(series) {
  const ctx = document.getElementById("dailyChart");
  if (!ctx || !window.Chart) return;
  dailyChart?.destroy();

  dailyChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: series.map((item) => item.date),
      datasets: [{
        label: "Mood score",
        data: series.map((item) => item.aggregate?.avg_sentiment ?? null),
        borderColor: "#ff4d7d",
        backgroundColor: "rgba(255,77,125,0.12)",
        tension: 0.35,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    },
  });
}

function renderWeeklyChart(series) {
  const ctx = document.getElementById("weeklyChart");
  if (!ctx || !window.Chart) return;
  weeklyChart?.destroy();

  weeklyChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: series.map((item) => item.week_start),
      datasets: [{
        label: "Weekly average",
        data: series.map((item) => item.aggregate?.avg_sentiment ?? null),
        backgroundColor: ["#ff6aa1", "#74b9ff", "#ffd93d", "#55efc4"],
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    },
  });
}

function renderEmotionChart(emotions) {
  const ctx = document.getElementById("emotionChart");
  if (!ctx || !window.Chart) return;
  emotionChart?.destroy();

  const keys    = ["joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"];
  const labels  = ["Joy 😊", "Sadness 😢", "Anger 😠", "Fear 😨", "Surprise 😮", "Disgust 🤢", "Neutral 😐"];
  const colors  = ["#FFD93D", "#74B9FF", "#E74C3C", "#A29BFE", "#FD79A8", "#55EFC4", "#8e9aaf"];
  const data    = keys.map((key) => emotions[key] || 0);
  const total   = data.reduce((a, b) => a + b, 0);

  // If no data, show equal slices with muted colors so the shape is still visible
  const displayData = total === 0 ? keys.map(() => 1) : data;

  emotionChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: displayData,
        backgroundColor: colors,
        borderWidth: 3,
        borderColor: "transparent",
        hoverOffset: 12,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: getComputedStyle(document.documentElement).getPropertyValue("--text").trim() || "#fff",
            padding: 14,
            font: { size: 13, weight: "600", family: "system-ui, sans-serif" },
            usePointStyle: true,
            pointStyleWidth: 10,
          },
        },
        tooltip: {
          callbacks: {
            label: (item) => {
              if (total === 0) return ` No data`;
              const pct = Math.round((item.parsed / total) * 100);
              return ` ${item.label.split(" ")[0]}: ${pct}%`;
            },
          },
        },
      },
      animation: { animateRotate: true, animateScale: true, duration: 600 },
    },
  });
}

function renderZoneBreakdown(zones) {
  const root = document.getElementById("zoneBreakdown");
  if (!root) return;
  if (!zones.length) {
    root.innerHTML = '<div class="state state-illustrated"><div class="state-emoji">🗺️</div><div>No zone breakdown available yet.<br />Aucune ventilation par zone pour le moment.</div></div>';
    return;
  }

  root.innerHTML = zones.map((zone) => {
    const score = Number(zone.avg_sentiment || 0);
    const width = Math.min(100, Math.max(8, Math.abs(score) * 100));
    return `
      <button class="zone-row ${zone.zone_id === selectedZoneId ? "is-selected" : ""}" type="button" data-zone-activity-id="${zone.zone_id || ""}">
        <div class="zone-label">${escapeHtml(zone.zone_name || zone.zone?.name || "Campus")}</div>
        <div class="zone-bar"><div class="zone-bar-fill" style="width:${width}%"></div></div>
        <div class="zone-score">${score >= 0 ? "+" : ""}${score.toFixed(2)}</div>
      </button>
    `;
  }).join("");

  root.querySelectorAll("[data-zone-activity-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      selectedZoneId = Number(btn.dataset.zoneActivityId);
      renderZoneBreakdown(zones);
      await loadZoneActivity(selectedZoneId);
    });
  });
}

async function loadZoneActivity(zoneId) {
  const root = document.getElementById("activityFeed");
  const title = document.getElementById("activityTitle");
  if (!root || !title) return;

  if (!zoneId) {
    title.textContent = "Zone activity";
    root.innerHTML = '<div class="state state-illustrated"><div class="state-emoji">📍</div><div>Select a zone to inspect recent activity.<br />Selectionnez une zone pour voir l activite recente.</div></div>';
    return;
  }

  await runAsyncUI({
    fn:        () => apiCall(`analytics/zone/${zoneId}`, () =>
      apiFetch(`/api/zones/${zoneId}/activity`, { method: "GET" })
    ),
    onLoad:    () => {
      root.innerHTML = '<div class="state">Loading zone activity...</div>';
    },
    isEmpty:   (data) => !(data.recent_posts || []).length,
    onEmpty:   (data) => {
      title.textContent = `${data.zone?.name || "Zone"} activity`;
      root.innerHTML = '<div class="state state-illustrated"><div class="state-emoji">📭</div><div>No recent public posts in this zone yet.<br />Aucune publication publique recente dans cette zone.</div></div>';
    },
    onSuccess: (data) => {
      const last24h = data.last_24h || {};
      const recentPosts = data.recent_posts || [];
      title.textContent = `${data.zone?.name || "Zone"} activity`;
      root.innerHTML = `
        <div class="activity-summary">
          <div class="kpi-box"><div class="kpi-label">Posts 24h</div><div class="kpi-value">${Number(last24h.post_count || 0)}</div></div>
          <div class="kpi-box"><div class="kpi-label">Reactions 24h</div><div class="kpi-value">${Number(last24h.reaction_count || 0)}</div></div>
          <div class="kpi-box"><div class="kpi-label">Dominant mood</div><div class="kpi-value">${escapeHtml(last24h.dominant_sentiment || "neutral")}</div></div>
        </div>
        ${recentPosts.map((entry) => `
          <article class="activity-post">
            <div><strong>${escapeHtml(entry.author?.display_name || entry.author?.username || "Pulse User")}${entry.author?.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : ''}</strong></div>
            <div style="margin-top:6px;">${escapeHtml(entry.content || "")}</div>
            <div class="activity-post-meta">${escapeHtml(formatRelativeTime(entry.created_at || latestAnalyticsDate))}</div>
          </article>
        `).join("")}
      `;
    },
    onError:   (err) => {
      root.innerHTML = `<div class="state">${escapeHtml(err.message || "Failed to load zone activity.")}</div>`;
    },
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatRelativeTime(dateLike) {
  const date = new Date(dateLike);
  if (Number.isNaN(date.getTime())) return "Recently";
  const diffSec = Math.floor((Date.now() - date.getTime()) / 1000);
  if (diffSec < 60) return "Just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  return `${Math.floor(diffHr / 24)}d ago`;
}
