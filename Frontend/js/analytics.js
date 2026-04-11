import { apiFetch, apiCall, requireAuth } from "./auth.js";
import { notify, runAsyncUI } from "./notify.js";
import { initLanguageControls } from "./i18n.js";
import { initThemeToggle, initOfflineBanner } from "./theme.js";

const USE_MOCK = true;
const DEFAULT_ZONE_LIMIT = 6;
const MAX_CHART_TICKS = 5;
const EMOTION_KEYS = ["joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"];
const LATEST_POINT_PLUGIN = {
  id: "latestPointMarker",
  afterDatasetsDraw(chart, _args, options) {
    if (!options?.enabled) return;

    const dataset = chart.data.datasets?.[0];
    const meta = chart.getDatasetMeta(0);
    if (!dataset || !meta?.data?.length) return;

    const latestIndex = findLatestDefinedIndex(dataset.data);
    if (latestIndex < 0) return;

    const element = meta.data[latestIndex];
    if (!element) return;

    const { ctx } = chart;
    const x = element.x;
    const y = element.y;
    if (!Number.isFinite(x) || !Number.isFinite(y)) return;

    const radius = options.radius || 5;
    const haloRadius = radius + (options.haloSize || 4);

    ctx.save();
    ctx.fillStyle = options.haloColor || "rgba(255, 77, 125, 0.16)";
    ctx.beginPath();
    ctx.arc(x, y, haloRadius, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = options.fillColor || "#ff4d7d";
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();

    ctx.lineWidth = options.strokeWidth || 2;
    ctx.strokeStyle = options.strokeColor || "#141221";
    ctx.stroke();
    ctx.restore();
  },
};

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
    fn: () => getAnalyticsBundle(dateValue),
    onLoad: () => {
      if (dateInput) dateInput.disabled = true;
    },
    onSuccess: async ({ campus, dailySeries, weeklySeries }) => {
      const zoneBreakdown = campus.zone_breakdown || [];
      const previousZone = zoneBreakdown.find((zone) => zone.zone_id === selectedZoneId)?.zone_id || null;
      const fallbackZone = zoneBreakdown.find((zone) => zone.zone_id)?.zone_id || null;

      renderCampusOverview(campus);
      renderDailyChart(dailySeries);
      renderWeeklyChart(weeklySeries);
      renderEmotionChart(campus.campus_overview?.emotion_distribution || {}, campus.campus_overview || {});

      selectedZoneId = previousZone || fallbackZone;
      renderZoneBreakdown(zoneBreakdown);
      await loadZoneActivity(selectedZoneId);
    },
    onError: (err) => {
      notify(err.message || "Could not load analytics. Check your connection and try again.", "error");
    },
    onFinally: () => {
      if (dateInput) dateInput.disabled = false;
    },
  });
}

async function getAnalyticsBundle(dateValue) {
  if (USE_MOCK) {
    return buildMockAnalyticsBundle(dateValue);
  }

  const [campus, dailySeries, weeklySeries] = await Promise.all([
    apiCall("analytics/campus", () =>
      apiFetch(`/api/analytics/campus?date=${dateValue}`, { method: "GET" })
    ),
    loadDailySeries(dateValue),
    loadWeeklySeries(dateValue),
  ]);

  return { campus, dailySeries, weeklySeries };
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
  const monday = getWeekStart(target);
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
  const hero = document.getElementById("moodHero");
  const totalPosts = Number(overview.total_posts || overview.current_count || 0);
  const emotions = overview.emotion_distribution || {};
  const topEmotion = Object.entries(emotions).sort((a, b) => b[1] - a[1])[0];
  const insight = buildCampusInsight({
    mood,
    date: data.date,
    totalPosts,
    avgSentiment: overview.avg_sentiment,
    topEmotion: topEmotion?.[0] || null,
    disclaimer: data.disclaimer || "",
  });

  hero.className = `mood-hero ${mood}`;
  document.getElementById("moodTitle").textContent = insight.title;
  document.getElementById("moodSubtitle").textContent = insight.subtitle;
  document.getElementById("kpiPosts").textContent = String(totalPosts);
  document.getElementById("kpiSentiment").textContent = overview.avg_sentiment != null ? Number(overview.avg_sentiment).toFixed(2) : "—";
  document.getElementById("kpiEmotion").textContent = topEmotion ? formatEmotionName(topEmotion[0]) : "—";

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

  const palette = getChartPalette();
  const values = series.map((item) => item.aggregate?.avg_sentiment ?? null);
  const hasData = values.some((value) => value != null);

  setChartEmptyState("dailyChartEmptyState", !hasData && !USE_MOCK
    ? {
        title: "Awaiting live data",
        description: "Daily mood points will appear once enough privacy-safe posts are available.",
      }
    : null);

  dailyChart = new Chart(ctx, {
    type: "line",
    plugins: [LATEST_POINT_PLUGIN],
    data: {
      labels: series.map((item) => formatShortDate(item.date)),
      datasets: [{
        label: "Mood score",
        data: values,
        borderColor: palette.accent,
        backgroundColor: (context) => createChartAreaGradient(context, palette.accentFill, "rgba(255,77,125,0.02)"),
        borderWidth: 3.5,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBorderWidth: 2,
        pointHoverBackgroundColor: palette.accent,
        pointHoverBorderColor: palette.panel,
        cubicInterpolationMode: "monotone",
        tension: 0.42,
        fill: true,
        spanGaps: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      layout: { padding: { top: 6, right: 6, bottom: 4, left: 2 } },
      plugins: {
        legend: { display: false },
        latestPointMarker: {
          enabled: hasData,
          fillColor: palette.accent,
          strokeColor: palette.panel,
          haloColor: withAlpha(palette.accent, 0.16),
          radius: 5.5,
          haloSize: 5,
          strokeWidth: 2.5,
        },
        tooltip: {
          displayColors: false,
          callbacks: {
            title: (items) => formatLongDate(resolveSeriesDate(series, items[0]?.dataIndex, "date")),
          },
        },
      },
      scales: {
        x: buildXAxisOptions(palette),
        y: buildYAxisOptions(palette),
      },
    },
  });
}

function renderWeeklyChart(series) {
  const ctx = document.getElementById("weeklyChart");
  if (!ctx || !window.Chart) return;
  weeklyChart?.destroy();

  const palette = getChartPalette();
  const values = series.map((item) => item.aggregate?.avg_sentiment ?? null);
  const hasData = values.some((value) => value != null);

  setChartEmptyState("weeklyChartEmptyState", !hasData && !USE_MOCK
    ? {
        title: "Awaiting live data",
        description: "Weekly trend markers will appear as the live aggregate fills in.",
      }
    : null);

  weeklyChart = new Chart(ctx, {
    type: "bar",
    plugins: [LATEST_POINT_PLUGIN],
    data: {
      labels: series.map((item) => formatShortDate(item.week_start)),
      datasets: [{
        label: "Weekly average",
        data: values,
        backgroundColor: series.map((item) => withAlpha(getSentimentBarColor(item.aggregate?.avg_sentiment), 0.82)),
        borderColor: series.map((item) => getSentimentBarColor(item.aggregate?.avg_sentiment)),
        borderWidth: 1.5,
        borderRadius: 12,
        borderSkipped: false,
        maxBarThickness: 44,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 6, right: 6, bottom: 4, left: 2 } },
      plugins: {
        legend: { display: false },
        latestPointMarker: {
          enabled: hasData,
          fillColor: palette.accent,
          strokeColor: palette.panel,
          haloColor: withAlpha(palette.accent, 0.14),
          radius: 5,
          haloSize: 4,
          strokeWidth: 2.5,
        },
        tooltip: {
          displayColors: false,
          callbacks: {
            title: (items) => {
              const weekStart = resolveSeriesDate(series, items[0]?.dataIndex, "week_start");
              return weekStart ? `Week of ${formatLongDate(weekStart)}` : "Weekly trend";
            },
          },
        },
      },
      scales: {
        x: buildXAxisOptions(palette),
        y: buildYAxisOptions(palette),
      },
    },
  });
}

function renderEmotionChart(emotions, overview = {}) {
  const ctx = document.getElementById("emotionChart");
  if (!ctx || !window.Chart) return;
  emotionChart?.destroy();

  const palette = getChartPalette();
  const labels = EMOTION_KEYS.map((key) => formatEmotionName(key));
  const colors = ["#FFD93D", "#74B9FF", "#E74C3C", "#A29BFE", "#FD79A8", "#55EFC4", "#8e9aaf"];
  const data = EMOTION_KEYS.map((key) => Number(emotions[key] || 0));
  const total = data.reduce((sum, value) => sum + value, 0);
  const hasData = total > 0;
  const displayData = hasData ? data : EMOTION_KEYS.map(() => 1);
  const displayColors = hasData || USE_MOCK
    ? colors
    : EMOTION_KEYS.map(() => withAlpha(palette.muted, 0.28));

  setChartEmptyState("emotionChartEmptyState", !hasData && !USE_MOCK
    ? {
        title: "Awaiting live data",
        description: "Emotion share will appear once there is enough real, privacy-safe activity.",
      }
    : null);

  emotionChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: displayData,
        backgroundColor: displayColors,
        borderWidth: 3,
        borderColor: "transparent",
        hoverOffset: 10,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      layout: { padding: { top: 4, right: 8, bottom: 4, left: 8 } },
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: palette.text,
            padding: 12,
            boxWidth: 10,
            boxHeight: 10,
            font: { size: 12, weight: "600", family: "system-ui, sans-serif" },
            usePointStyle: true,
          },
        },
        tooltip: {
          callbacks: {
            label: (item) => {
              if (total === 0) return " No data";
              const pct = Math.round((item.parsed / total) * 100);
              return ` ${item.label}: ${pct}%`;
            },
          },
        },
      },
      animation: { animateRotate: true, animateScale: true, duration: 500 },
    },
  });

  renderEmotionCenter(emotions, overview);
  renderEmotionSummary(emotions, overview);
}

function renderEmotionCenter(emotions, overview) {
  const labelEl = document.getElementById("emotionCenterLabel");
  const valueEl = document.getElementById("emotionCenterValue");
  const detailEl = document.getElementById("emotionCenterDetail");
  if (!labelEl || !valueEl || !detailEl) return;

  const sorted = Object.entries(emotions).sort((a, b) => Number(b[1] || 0) - Number(a[1] || 0));
  const total = sorted.reduce((sum, [, count]) => sum + Number(count || 0), 0);
  const [topEmotion, topCount] = sorted[0] || [];
  const totalPosts = Number(overview.total_posts || overview.current_count || 0);

  if (!topEmotion || total <= 0 || totalPosts <= 0) {
    labelEl.textContent = "Emotion signal";
    valueEl.textContent = USE_MOCK ? "Preview" : "No data";
    detailEl.textContent = USE_MOCK
      ? "Sample distribution"
      : "Waiting for privacy-safe live input";
    return;
  }

  labelEl.textContent = "Top emotion";
  valueEl.textContent = formatEmotionName(topEmotion);
  detailEl.textContent = `${Math.round((Number(topCount || 0) / total) * 100)}% of signals`;
}

function renderEmotionSummary(emotions, overview) {
  const summaryEl = ensureEmotionSummary();
  if (!summaryEl) return;

  const sorted = Object.entries(emotions).sort((a, b) => Number(b[1] || 0) - Number(a[1] || 0));
  const topEmotion = sorted.find(([, count]) => Number(count) > 0)?.[0] || null;
  const totalPosts = Number(overview.total_posts || overview.current_count || 0);

  if (!topEmotion || totalPosts <= 0) {
    summaryEl.textContent = USE_MOCK
      ? "Mock mode is showing a steady campus pulse preview so the dashboard feels realistic before live signals arrive."
      : "Campus pulse will settle into view once enough privacy-safe data is available.";
    return;
  }

  summaryEl.textContent = `Most conversations are landing ${formatEmotionName(topEmotion).toLowerCase()} today, with ${totalPosts} posts contributing to a steadier campus signal than the surrounding moods suggest.`;
}

function ensureEmotionSummary() {
  const chart = document.getElementById("emotionChart");
  const card = chart?.closest(".chart-shell--emotion");
  if (!card) return null;

  let summary = card.querySelector(".emotion-summary");
  if (!summary) {
    summary = document.createElement("p");
    summary.className = "emotion-summary";
    card.appendChild(summary);
  }

  return summary;
}

function renderZoneBreakdown(zones) {
  const root = document.getElementById("zoneBreakdown");
  if (!root) return;

  if (!zones.length) {
    root.innerHTML = '<div class="state state-illustrated"><div class="state-emoji">🗺️</div><div>No zone breakdown available yet.<br />Aucune ventilation par zone pour le moment.</div></div>';
    return;
  }

  root.innerHTML = `
    <div class="zone-search-wrap">
      <input class="zone-search-input" type="search" placeholder="Search zones…" aria-label="Search zones" />
    </div>
    <div class="zone-hint"></div>
    <div class="zone-list"></div>
  `;

  const searchInput = root.querySelector(".zone-search-input");
  const hintEl = root.querySelector(".zone-hint");
  const listEl = root.querySelector(".zone-list");

  const updateList = () => {
    const query = searchInput.value.trim().toLowerCase();
    const visibleZones = getVisibleZones(zones, query);

    if (query) {
      hintEl.textContent = visibleZones.length
        ? `Showing ${visibleZones.length} matching zone${visibleZones.length === 1 ? "" : "s"}.`
        : "No zones match that search yet.";
    } else {
      hintEl.textContent = zones.length > DEFAULT_ZONE_LIMIT
        ? `Showing the top ${DEFAULT_ZONE_LIMIT} zones by activity. Search to explore more.`
        : "Showing all available zones.";
    }

    listEl.innerHTML = visibleZones.length ? buildZoneRows(visibleZones) : '<div class="zone-no-results">No matching zones</div>';
    attachZoneClicks(listEl, zones);
  };

  searchInput.addEventListener("input", updateList);
  updateList();
}

function buildZoneRows(zones) {
  return zones.map((zone) => {
    const score = Number(zone.avg_sentiment || 0);
    const width = Math.min(100, Math.max(8, Math.abs(score) * 100));
    const zoneName = getZoneDisplayName(zone);
    return `
      <button class="zone-row ${zone.zone_id === selectedZoneId ? "is-selected" : ""}" type="button" data-zone-activity-id="${zone.zone_id || ""}">
        <div class="zone-row-main">
          <div class="zone-label" title="${escapeHtml(zoneName)}">${escapeHtml(zoneName)}</div>
          <div class="zone-bar-wrap">
            <div class="zone-bar"><div class="zone-bar-fill" style="width:${width}%"></div></div>
          </div>
        </div>
        <div class="zone-score">${score >= 0 ? "+" : ""}${score.toFixed(2)}</div>
      </button>
    `;
  }).join("");
}

function getVisibleZones(zones, query) {
  const ranked = rankZones(zones);
  const normalizedQuery = normalizeSearchText(query);

  if (normalizedQuery) {
    return ranked.filter((zone) => normalizeSearchText(getZoneDisplayName(zone)).includes(normalizedQuery));
  }

  const limited = ranked.slice(0, DEFAULT_ZONE_LIMIT);
  if (selectedZoneId && !limited.some((zone) => zone.zone_id === selectedZoneId)) {
    const selectedZone = ranked.find((zone) => zone.zone_id === selectedZoneId);
    if (selectedZone) {
      limited[limited.length - 1] = selectedZone;
    }
  }
  return limited;
}

function rankZones(zones) {
  return [...zones].sort((a, b) => {
    const aPosts = Number(a.total_posts || 0);
    const bPosts = Number(b.total_posts || 0);
    if (bPosts !== aPosts) return bPosts - aPosts;

    const aReactions = Number(a.reaction_count || 0);
    const bReactions = Number(b.reaction_count || 0);
    if (bReactions !== aReactions) return bReactions - aReactions;

    return Math.abs(Number(b.avg_sentiment || 0)) - Math.abs(Number(a.avg_sentiment || 0));
  });
}

function attachZoneClicks(listEl, zones) {
  listEl.querySelectorAll("[data-zone-activity-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      selectedZoneId = Number(btn.dataset.zoneActivityId) || null;
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
    fn: () => {
      if (USE_MOCK) {
        return Promise.resolve(buildMockZoneActivity(zoneId, latestAnalyticsDate));
      }
      return apiCall(`analytics/zone/${zoneId}`, () =>
        apiFetch(`/api/zones/${zoneId}/activity`, { method: "GET" })
      );
    },
    onLoad: () => {
      root.innerHTML = '<div class="state">Loading zone activity...</div>';
    },
    isEmpty: (data) => !(data.recent_posts || []).length,
    onEmpty: (data) => {
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
          <div class="kpi-box"><div class="kpi-label">Dominant mood</div><div class="kpi-value">${escapeHtml(formatMoodLabel(last24h.dominant_sentiment || "neutral"))}</div></div>
        </div>
        ${recentPosts.map((entry) => `
          <article class="activity-post">
            <header class="activity-post-header">
              <div class="activity-author-block">
                <div class="activity-author-row">
                  <strong class="activity-author">${escapeHtml(entry.author?.display_name || entry.author?.username || "Pulse User")}${entry.author?.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : ""}</strong>
                </div>
                <div class="activity-post-meta">${escapeHtml(formatAuthorMeta(entry.author))}</div>
              </div>
              <div class="activity-post-time">${escapeHtml(formatRelativeTime(entry.created_at || latestAnalyticsDate))}</div>
            </header>
            <p class="activity-post-body">${escapeHtml(entry.content || "")}</p>
          </article>
        `).join("")}
      `;
    },
    onError: (err) => {
      root.innerHTML = `<div class="state">${escapeHtml(err.message || "Failed to load zone activity.")}</div>`;
    },
  });
}

function buildMockAnalyticsBundle(dateValue) {
  const date = normalizeDate(dateValue);
  const seed = getDateSeed(date);
  const phase = seed * 0.22;
  const baseline = clampNumber(0.1 + Math.sin(seed * 0.13) * 0.08, -0.28, 0.32);
  const drift = Math.cos(seed * 0.09) * 0.035;
  const dailySeries = Array.from({ length: 7 }, (_, index) => {
    const current = new Date(date);
    current.setDate(current.getDate() - (6 - index));
    const wave = Math.sin(phase + index * 0.72) * 0.08;
    const secondaryWave = Math.cos(phase * 0.6 + index * 0.38) * 0.03;
    const trendLift = (index - 3) * 0.008;
    return {
      date: current.toISOString().slice(0, 10),
      aggregate: {
        avg_sentiment: clampNumber(baseline + drift + wave + secondaryWave + trendLift, -0.7, 0.7),
      },
    };
  });
  const campusAvg = clampNumber(average(dailySeries.map((item) => item.aggregate.avg_sentiment)) + 0.018, -0.65, 0.65);
  const totalPosts = 152 + seed * 3 + Math.round(Math.abs(campusAvg) * 40);
  const emotionDistribution = buildMockEmotionDistribution(campusAvg, seed);

  const zoneTemplates = [
    { zone_id: 1, zone_name: "Pavillon Alphonse-Desjardins", baseSentiment: 0.28, total_posts: 42, reaction_count: 118 },
    { zone_id: 2, zone_name: "Pavillon Jean-Charles-Bonenfant", baseSentiment: 0.19, total_posts: 36, reaction_count: 104 },
    { zone_id: 3, zone_name: "Place de l'Universite", baseSentiment: 0.08, total_posts: 31, reaction_count: 92 },
    { zone_id: 4, zone_name: "Pavillon Adrien-Pouliot", baseSentiment: -0.06, total_posts: 27, reaction_count: 74 },
    { zone_id: 5, zone_name: "Cafe Desjardins", baseSentiment: 0.14, total_posts: 24, reaction_count: 67 },
    { zone_id: 6, zone_name: "Pavillon Felix-Antoine-Savard", baseSentiment: 0.05, total_posts: 21, reaction_count: 58 },
    { zone_id: 7, zone_name: "PEPS - Pavillon principal", baseSentiment: 0.22, total_posts: 19, reaction_count: 63 },
    { zone_id: 8, zone_name: "Pavillon Alexandre-Vachon", baseSentiment: -0.02, total_posts: 17, reaction_count: 49 },
  ];

  const zoneBreakdown = zoneTemplates.map((zone, index) => ({
    ...zone,
    avg_sentiment: clampNumber(zone.baseSentiment * 0.55 + campusAvg * 0.45 + Math.sin(phase + index * 0.8) * 0.03, -0.7, 0.7),
    total_posts: zone.total_posts + ((seed + index * 2) % 5) + Math.round(Math.max(0, campusAvg) * 6),
    reaction_count: zone.reaction_count + ((seed + index * 3) % 9) + Math.round(Math.abs(campusAvg) * 18),
  }));
  const weeklySeries = Array.from({ length: 4 }, (_, index) => {
    const current = new Date(getWeekStart(date));
    current.setDate(current.getDate() - (3 - index) * 7);
    const smoothWeekValue = clampNumber(
      baseline + Math.sin(phase * 0.8 + index * 0.58) * 0.07 + drift + (index - 1.5) * 0.014,
      -0.7,
      0.7
    );
    return {
      week_start: current.toISOString().slice(0, 10),
      aggregate: {
        avg_sentiment: smoothWeekValue,
      },
    };
  });

  return {
    campus: {
      date: date.toISOString().slice(0, 10),
      disclaimer: USE_MOCK ? "Mock preview mode is active." : "",
      campus_overview: {
        mood_label: getMoodLabel(campusAvg),
        total_posts: totalPosts,
        avg_sentiment: campusAvg,
        emotion_distribution: emotionDistribution,
      },
      zone_breakdown: zoneBreakdown,
    },
    dailySeries,
    weeklySeries,
  };
}

function buildMockZoneActivity(zoneId, dateValue) {
  const baseDate = normalizeDate(dateValue);
  const zone = getMockZoneSummary(zoneId);

  if (!zone) {
    return {
      zone: { id: zoneId, name: "Zone" },
      last_24h: {},
      recent_posts: [],
    };
  }

  const authors = [
    { display_name: "Maya Chen", username: "maya", is_admin: false },
    { display_name: "Noah Park", username: "noahp", is_admin: false },
    { display_name: "Campus Team", username: "pulse_admin", is_admin: true },
  ];
  const moodWord = getMoodInsightWord(zone.avg_sentiment);
  const messages = [
    `${zone.zone_name} feels ${moodWord} this afternoon, with people settling into longer conversations than usual.`,
    `Traffic through ${zone.zone_name} has evened out tonight, and the overall tone is staying easy to read.`,
    `Quick pulse from ${zone.zone_name}: the mood is holding steady with a few smaller swings around the edges.`,
  ];

  return {
    zone: { id: zone.zone_id, name: zone.zone_name },
    last_24h: {
      post_count: Math.max(4, Math.round(Number(zone.total_posts || 0) / 4)),
      reaction_count: Math.max(10, Math.round(Number(zone.reaction_count || 0) / 3)),
      dominant_sentiment: getMoodLabel(zone.avg_sentiment),
    },
    recent_posts: authors.map((author, index) => {
      const created = new Date(baseDate);
      created.setHours(created.getHours() - (index * 3 + 2));
      return {
        id: `${zone.zone_id}-${index + 1}`,
        author,
        content: messages[index],
        created_at: created.toISOString(),
      };
    }),
  };
}

function getMockZoneSummary(zoneId) {
  return buildMockAnalyticsBundle(latestAnalyticsDate || new Date().toISOString().slice(0, 10))
    .campus.zone_breakdown.find((zone) => Number(zone.zone_id) === Number(zoneId)) || null;
}

function getZoneDisplayName(zone) {
  return String(zone?.zone_name || zone?.zone?.name || "Campus");
}

function getChartPalette() {
  const styles = getComputedStyle(document.documentElement);
  return {
    text: styles.getPropertyValue("--text").trim() || "#ffffff",
    muted: styles.getPropertyValue("--muted").trim() || "rgba(255,255,255,0.6)",
    border: styles.getPropertyValue("--border-soft").trim() || "rgba(255,255,255,0.12)",
    panel: styles.getPropertyValue("--panel").trim() || "#141221",
    accent: styles.getPropertyValue("--accent").trim() || "#ff4d7d",
    accentFill: "rgba(255,77,125,0.22)",
  };
}

function buildXAxisOptions(palette) {
  return {
    ticks: {
      color: palette.muted,
      autoSkip: true,
      maxTicksLimit: MAX_CHART_TICKS,
      maxRotation: 0,
      padding: 8,
    },
    grid: {
      display: false,
      drawBorder: false,
    },
  };
}

function buildYAxisOptions(palette) {
  return {
    suggestedMin: -0.4,
    suggestedMax: 0.4,
    ticks: {
      color: palette.muted,
      maxTicksLimit: 5,
      padding: 8,
      callback: (value) => Number(value).toFixed(1),
    },
    grid: {
      color: withAlpha(palette.border, 0.55),
      drawBorder: false,
    },
  };
}

function buildCampusInsight({ mood, date, totalPosts, avgSentiment, topEmotion, disclaimer }) {
  const dateLabel = formatLongDate(date);
  const emotionLabel = topEmotion ? formatEmotionName(topEmotion).toLowerCase() : "mixed";
  const score = avgSentiment != null ? Number(avgSentiment).toFixed(2) : "—";
  const titleMap = {
    positive: "Momentum is leaning upbeat today",
    neutral: "Campus mood looks steady today",
    negative: "The mood is carrying more weight today",
    unknown: "The signal is still taking shape",
  };
  const subtitleMap = {
    positive: `${dateLabel} shows an optimistic tilt, led by ${emotionLabel} conversations across ${totalPosts} posts.`,
    neutral: `${dateLabel} feels balanced overall, with ${emotionLabel} signals keeping the campus pulse stable across ${totalPosts} posts.`,
    negative: `${dateLabel} is trending more subdued, with ${emotionLabel} reactions showing up most often across ${totalPosts} posts.`,
    unknown: `${dateLabel} does not have enough privacy-safe volume yet, so the dashboard is holding a lighter read of campus mood.`,
  };
  const baseSubtitle = subtitleMap[mood] || subtitleMap.neutral;
  return {
    title: titleMap[mood] || titleMap.neutral,
    subtitle: `${baseSubtitle} Average sentiment is ${score}.${disclaimer ? ` ${disclaimer}` : ""}`.trim(),
  };
}

function buildMockEmotionDistribution(campusAvg, seed) {
  const profile = campusAvg > 0.08
    ? { joy: 0.31, surprise: 0.18, neutral: 0.21, sadness: 0.1, fear: 0.08, anger: 0.06, disgust: 0.06 }
    : campusAvg < -0.08
      ? { sadness: 0.26, fear: 0.19, neutral: 0.2, surprise: 0.11, joy: 0.1, anger: 0.09, disgust: 0.05 }
      : { neutral: 0.29, joy: 0.2, surprise: 0.15, sadness: 0.12, fear: 0.1, anger: 0.08, disgust: 0.06 };
  const total = 100 + (seed % 9);
  const distribution = {};

  EMOTION_KEYS.forEach((key, index) => {
    const wave = Math.sin(seed * 0.3 + index * 0.8) * 0.015;
    distribution[key] = Math.max(1, Math.round(total * ((profile[key] || 0.08) + wave)));
  });

  return distribution;
}

function getMoodInsightWord(score) {
  if (score > 0.12) return "brighter";
  if (score < -0.12) return "heavier";
  return "more balanced";
}

function createChartAreaGradient(context, from, to) {
  const { chart } = context;
  const { ctx, chartArea } = chart;
  if (!chartArea) return from;
  const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
  gradient.addColorStop(0, from);
  gradient.addColorStop(1, to);
  return gradient;
}

function withAlpha(color, alpha) {
  if (!color) return color;
  if (color.startsWith("rgba(")) {
    return color.replace(/rgba\(([^)]+),\s*[^)]+\)/, `rgba($1, ${alpha})`);
  }
  if (color.startsWith("rgb(")) {
    return color.replace("rgb(", "rgba(").replace(")", `, ${alpha})`);
  }
  if (color.startsWith("#")) {
    const normalized = color.length === 4
      ? `#${color[1]}${color[1]}${color[2]}${color[2]}${color[3]}${color[3]}`
      : color;
    const int = Number.parseInt(normalized.slice(1), 16);
    const r = (int >> 16) & 255;
    const g = (int >> 8) & 255;
    const b = int & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  return color;
}

function getSentimentBarColor(score) {
  const value = Number(score || 0);
  if (value > 0.1) return "#ff6aa1";
  if (value < -0.1) return "#74b9ff";
  return "#ffd166";
}

function resolveSeriesDate(series, index, key) {
  if (!Number.isInteger(index) || index < 0 || index >= series.length) return "";
  return series[index]?.[key] || "";
}

function normalizeSearchText(value) {
  return String(value || "").trim().toLocaleLowerCase();
}

function findLatestDefinedIndex(values) {
  for (let index = values.length - 1; index >= 0; index -= 1) {
    if (values[index] != null) return index;
  }
  return -1;
}

function setChartEmptyState(elementId, state) {
  const element = document.getElementById(elementId);
  if (!element) return;

  if (!state) {
    element.hidden = true;
    element.innerHTML = "";
    return;
  }

  element.hidden = false;
  element.innerHTML = `<strong>${escapeHtml(state.title)}</strong><span>${escapeHtml(state.description)}</span>`;
}

function formatEmotionName(key) {
  const labels = {
    joy: "Joy",
    sadness: "Sadness",
    anger: "Anger",
    fear: "Fear",
    surprise: "Surprise",
    disgust: "Disgust",
    neutral: "Neutral",
  };
  return labels[key] || "Mood";
}

function formatMoodLabel(value) {
  const labels = {
    positive: "Positive",
    neutral: "Neutral",
    negative: "Negative",
    unknown: "Unknown",
  };
  return labels[String(value || "neutral").toLowerCase()] || "Neutral";
}

function formatAuthorMeta(author = {}) {
  const username = String(author.username || "").trim();
  const displayName = String(author.display_name || "").trim().toLowerCase();

  if (username && displayName && displayName !== username.toLowerCase()) {
    return `@${username}`;
  }

  if (author.is_admin) return "Campus team";
  return username ? "Pulse member" : "Community post";
}

function formatShortDate(dateLike) {
  const date = new Date(dateLike);
  if (Number.isNaN(date.getTime())) return String(dateLike || "");
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function formatLongDate(dateLike) {
  const date = new Date(dateLike);
  if (Number.isNaN(date.getTime())) return String(dateLike || "");
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function getMoodLabel(score) {
  if (score == null) return "unknown";
  if (score > 0.05) return "positive";
  if (score < -0.05) return "negative";
  return "neutral";
}

function normalizeDate(dateLike) {
  const parsed = new Date(`${dateLike}T12:00:00`);
  return Number.isNaN(parsed.getTime()) ? new Date() : parsed;
}

function getWeekStart(date) {
  const monday = new Date(date);
  monday.setDate(date.getDate() - ((date.getDay() + 6) % 7));
  monday.setHours(12, 0, 0, 0);
  return monday;
}

function getDateSeed(date) {
  return Number(date.toISOString().slice(8, 10)) || 1;
}

function clampNumber(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function average(values) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + Number(value || 0), 0) / values.length;
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
