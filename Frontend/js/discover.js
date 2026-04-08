import { apiFetch, requireAuth } from "./auth.js";
import { getProfileHref } from "./avatar.js";
import { initLanguageControls } from "./i18n.js";
import { initMobileDrawer, initThemeToggle, initOfflineBanner } from "./theme.js";

let discoverPage = 1;
let discoverLoading = false;
let discoverHasNext = false;

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();
  initMobileDrawer();

  document.getElementById("discoverSentiment")?.addEventListener("change", async () => {
    discoverPage = 1;
    await loadDiscover({ append: false });
  });

  await Promise.all([loadDiscover({ append: false }), loadTrending()]);
  setupInfiniteScroll();
});

function setupInfiniteScroll() {
  const sentinel = document.getElementById("discoverSentinel");
  if (!sentinel) return;
  const observer = new IntersectionObserver(async (entries) => {
    if (!entries[0]?.isIntersecting || discoverLoading || !discoverHasNext) return;
    discoverPage += 1;
    await loadDiscover({ append: true });
  }, { rootMargin: "200px" });
  observer.observe(sentinel);
}

async function loadDiscover({ append = false } = {}) {
  if (discoverLoading) return;
  discoverLoading = true;

  const sentiment = document.getElementById("discoverSentiment").value;
  const state = document.getElementById("discoverState");
  const feed = document.getElementById("discoverFeed");

  if (!append) {
    state.textContent = "Loading discovery feed...";
    state.style.display = "";
    feed.innerHTML = renderSkeletonCards(3);
    discoverPage = 1;
  }

  try {
    const params = new URLSearchParams({ page: discoverPage, per_page: 20 });
    if (sentiment) params.set("sentiment", sentiment);
    const data = await apiFetch(`/api/posts/discover?${params.toString()}`, { method: "GET" });
    const posts = data.posts || [];
    discoverHasNext = data.has_next ?? false;

    if (!append) feed.innerHTML = "";

    if (!posts.length && !append) {
      state.innerHTML = '<div class="state-illustrated"><div class="state-emoji">🧭</div><div>No discovery posts yet.<br />Aucune publication de decouverte pour le moment.</div></div>';
      return;
    }

    state.style.display = "none";
    feed.insertAdjacentHTML("beforeend", posts.map(renderPostCard).join(""));
  } finally {
    discoverLoading = false;
  }
}

function renderPostCard(post) {
  return `
    <article class="panel post">
      <div class="post-head">
        <div class="post-user">
          <div class="post-meta">
            <div class="u">${post.is_anonymous || !post.author?.username
              ? escapeHtml(post.author?.pseudonym || "Anonymous")
              : `<a class="post-user-link-text" href="${escapeAttr(getProfileHref(post.author.username))}">${escapeHtml(post.author?.display_name || post.author?.username || "Pulse User")}${post.author?.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : ''}</a>`}</div>
            <div class="m">${escapeHtml(post.zone?.name || "Campus")} • ${escapeHtml(post.emotion_display || post.emotion_label || post.sentiment || "neutral")}</div>
          </div>
        </div>
      </div>
      <div class="post-text">${escapeHtml(post.content || "")}</div>
    </article>
  `;
}

async function loadTrending() {
  const root = document.getElementById("discoverTrending");
  const data = await apiFetch("/api/zones/trending?window=24h&limit=5", { method: "GET" });
  const zones = data.zones || [];
  root.innerHTML = zones.length
    ? zones.map((entry) => `
        <a class="activity-post search-result-link" href="zone.html?id=${encodeURIComponent(entry.zone?.id)}">
          <div><strong>${escapeHtml(entry.zone?.name || "Zone")}</strong></div>
          <div class="activity-post-meta">${entry.post_count} posts • ${entry.reaction_count} reactions • ${escapeHtml(entry.mood || "neutral")}</div>
        </a>
      `).join("")
    : '<div class="state state-illustrated"><div class="state-emoji">📈</div><div>No trending zones yet.<br />Aucune zone tendance pour le moment.</div></div>';
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}

function renderSkeletonCards(count) {
  return Array.from({ length: count }, () => `
    <article class="skeleton-card">
      <div class="skeleton-line short"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line medium"></div>
    </article>
  `).join("");
}
