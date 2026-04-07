import { apiFetch, getAssetUrl, requireAuth } from "./auth.js";
import { getPostAvatarUrl, getProfileHref, getUserAvatarUrl } from "./avatar.js";
import { initLanguageControls } from "./i18n.js";
import { initOfflineBanner, initThemeToggle, initUnreadBadges } from "./theme.js";

let currentZoneId = null;

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();
  initUnreadBadges();
  await loadCurrentUser();
  setupZoneSearch();

  const params = new URLSearchParams(window.location.search);
  const initialZoneId = params.get("id");
  if (initialZoneId) {
    await loadZoneFeed(initialZoneId);
  } else {
    document.getElementById("zoneState").textContent = "Choose a zone from search to begin.";
  }
});

async function loadCurrentUser() {
  try {
    const data = await apiFetch("/api/auth/me", { method: "GET" });
    const user = data.user;
    const avatarUrl = getUserAvatarUrl(user, getAssetUrl);

    document.getElementById("zoneSidebarAvatar").src = avatarUrl;
    document.getElementById("zoneSidebarName").textContent = user?.display_name || user?.username || "Pulse User";
    document.getElementById("zoneSidebarHandle").textContent = `@${user?.username || "user"}`;
  } catch {
    // Keep shell usable even if the sidebar profile fails.
  }
}

function setupZoneSearch() {
  const input = document.getElementById("zoneLookup");
  const resultsEl = document.getElementById("zoneLookupResults");
  if (!input || !resultsEl) return;

  let timer = null;

  input.addEventListener("input", () => {
    const query = input.value.trim();
    clearTimeout(timer);

    if (query.length < 2) {
      resultsEl.style.display = "none";
      resultsEl.innerHTML = "";
      return;
    }

    timer = setTimeout(async () => {
      try {
        const payload = await apiFetch(`/api/zones/search?q=${encodeURIComponent(query)}`, { method: "GET" });
        const zones = payload.zones || [];

        resultsEl.style.display = "block";
        resultsEl.innerHTML = zones.map((zone) => `
          <button class="zone-result" data-zone-id="${zone.id}" type="button">
            <span class="zone-result-name">${escapeHtml(zone.name)}</span>
            <span class="zone-result-meta">${escapeHtml(zone.description || "")}</span>
          </button>
        `).join("");

        resultsEl.querySelectorAll("[data-zone-id]").forEach((btn) => {
          btn.addEventListener("click", async () => {
            await loadZoneFeed(btn.dataset.zoneId);
            resultsEl.style.display = "none";
            input.value = "";
          });
        });
      } catch {
        resultsEl.style.display = "block";
        resultsEl.innerHTML = '<div class="search-empty">Zone search failed</div>';
      }
    }, 250);
  });
}

async function loadZoneFeed(zoneId) {
  currentZoneId = zoneId;
  const stateEl = document.getElementById("zoneState");
  const feedEl = document.getElementById("zoneFeed");
  const titleEl = document.getElementById("zoneTitle");
  const metaEl = document.getElementById("zoneMeta");

  feedEl.innerHTML = "";
  stateEl.style.display = "block";
  stateEl.textContent = "Loading zone feed...";
  feedEl.innerHTML = renderSkeletonCards(3);

  try {
    const data = await apiFetch(`/api/posts/zone/${encodeURIComponent(zoneId)}?per_page=20`, {
      method: "GET",
    });

    titleEl.textContent = data.zone?.name || "Zone feed";
    metaEl.textContent = data.zone?.description || "Public posts for this zone";
    history.replaceState({}, "", `zone.html?id=${encodeURIComponent(zoneId)}`);

    if (!(data.posts || []).length) {
      stateEl.innerHTML = '<div class="state-illustrated"><div class="state-emoji">📍</div><div>No public posts in this zone yet.<br />Aucune publication publique dans cette zone pour le moment.</div></div>';
      feedEl.innerHTML = "";
      return;
    }

    stateEl.style.display = "none";
    feedEl.innerHTML = (data.posts || []).map(renderPostCard).join("");
  } catch (error) {
    stateEl.textContent = error.message || "Failed to load zone feed.";
  }
}

function renderPostCard(post) {
  const author = post.author || {};
  const isAnonymous = Boolean(post.is_anonymous);
  const avatarUrl = getPostAvatarUrl(author, isAnonymous, getAssetUrl);

  return `
    <article class="panel post">
      <div class="post-head">
        <div class="post-user">
          ${!isAnonymous && author.username ? `
            <a class="post-user-link" href="${escapeAttr(getProfileHref(author.username))}" aria-label="View ${escapeAttr(author.display_name || author.username || "User")}'s profile">
              <img class="avatar" src="${escapeAttr(avatarUrl)}" alt="${escapeAttr(author.display_name || author.username || "User")}" />
              <div class="post-meta">
                <div class="u">${escapeHtml(author.display_name || author.username || "User")}${author.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : ''}</div>
                <div class="m">@${escapeHtml(author.username || "user")}</div>
              </div>
            </a>
          ` : `
            <img class="avatar" src="${escapeAttr(avatarUrl)}" alt="User" />
            <div class="post-meta">
              <div class="u">${escapeHtml(author.pseudonym || "Anonymous")}</div>
              <div class="m">@anonymous</div>
            </div>
          `}
          <div class="post-meta post-meta-secondary">
            <div class="m">${escapeHtml(formatRelativeTime(post.created_at))}</div>
          </div>
        </div>
      </div>
      <div class="post-text">${escapeHtml(post.content || "")}</div>
    </article>
  `;
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
