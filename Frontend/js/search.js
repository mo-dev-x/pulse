import { apiFetch, getAssetUrl, requireAuth } from "./auth.js";
import { getUserAvatarUrl } from "./avatar.js";
import { initLanguageControls } from "./i18n.js";
import { initThemeToggle, initOfflineBanner } from "./theme.js";

export function initMentionAutocomplete(textarea) {
  if (!textarea || textarea.dataset.mentionReady === "true") return;
  textarea.dataset.mentionReady = "true";

  const wrapper = document.createElement("div");
  wrapper.className = "mention-dropdown";
  wrapper.style.display = "none";
  textarea.insertAdjacentElement("afterend", wrapper);

  let timer = null;

  textarea.addEventListener("input", () => {
    clearTimeout(timer);
    const trigger = getMentionTrigger(textarea.value, textarea.selectionStart);
    if (!trigger) {
      wrapper.style.display = "none";
      wrapper.innerHTML = "";
      return;
    }

    timer = setTimeout(async () => {
      try {
        const data = await apiFetch(`/api/search/users?q=${encodeURIComponent(trigger.word)}&limit=5`, { method: "GET" });
        const users = data.users || [];
        if (!users.length) {
          wrapper.style.display = "none";
          return;
        }

        wrapper.style.display = "block";
        wrapper.innerHTML = users.map((user) => `
          <button class="zone-result" type="button" data-mention-username="${escapeAttr(user.username)}">
            <span class="zone-result-name">${escapeHtml(user.display_name || user.username)}</span>
            <span class="zone-result-meta">@${escapeHtml(user.username)}</span>
          </button>
        `).join("");

        wrapper.querySelectorAll("[data-mention-username]").forEach((btn) => {
          btn.addEventListener("click", () => {
            insertMention(textarea, trigger.start, trigger.end, btn.dataset.mentionUsername);
            wrapper.style.display = "none";
            wrapper.innerHTML = "";
          });
        });
      } catch {
        wrapper.style.display = "none";
      }
    }, 250);
  });
}

function getMentionTrigger(text, caret) {
  const slice = text.slice(0, caret);
  const match = slice.match(/(^|\s)@([a-zA-Z0-9_]{1,50})$/);
  if (!match) return null;
  const start = slice.lastIndexOf(`@${match[2]}`);
  return {
    word: match[2],
    start,
    end: caret,
  };
}

function insertMention(textarea, start, end, username) {
  const value = textarea.value;
  const nextValue = `${value.slice(0, start)}@${username} ${value.slice(end)}`;
  textarea.value = nextValue;
  const caret = start + username.length + 2;
  textarea.setSelectionRange(caret, caret);
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
  textarea.focus();
}

function initSearchPage() {
  const input = document.getElementById("searchPageInput");
  const filters = document.querySelectorAll("[data-search-type]");
  const resultsEl = document.getElementById("searchResultsPage");
  const summaryEl = document.getElementById("searchSummary");
  const loadMoreBtn = document.getElementById("searchLoadMore");

  if (!input || !resultsEl || !summaryEl || !loadMoreBtn) return;

  let query = "";
  let type = "all";
  let page = 1;
  let hasNext = false;

  const runSearch = async ({ reset = true } = {}) => {
    query = input.value.trim();
    if (query.length < 2) {
      summaryEl.textContent = "Enter at least 2 characters to search.";
      resultsEl.innerHTML = "";
      loadMoreBtn.hidden = true;
      return;
    }

    if (reset) {
      page = 1;
      resultsEl.innerHTML = "";
      renderSearchSkeleton(resultsEl);
    }

    const data = await apiFetch(`/api/search?q=${encodeURIComponent(query)}&type=${type}&page=${page}&per_page=8`, {
      method: "GET",
    });

    hasNext = Boolean(data.has_next);
    summaryEl.textContent = `Results for "${data.query}"`;

    const markup = renderSearchGroups(data.results, type);
    if (reset) {
      resultsEl.innerHTML = markup;
    } else {
      resultsEl.insertAdjacentHTML("beforeend", markup);
    }

    loadMoreBtn.hidden = !hasNext;
  };

  filters.forEach((btn) => {
    btn.addEventListener("click", async () => {
      type = btn.dataset.searchType;
      filters.forEach((item) => item.classList.toggle("active", item === btn));
      await runSearch({ reset: true });
    });
  });

  input.addEventListener("keydown", async (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      await runSearch({ reset: true });
    }
  });

  loadMoreBtn.addEventListener("click", async () => {
    page += 1;
    await runSearch({ reset: false });
  });

  const params = new URLSearchParams(window.location.search);
  if (params.get("q")) input.value = params.get("q");
  if (params.get("type")) {
    type = params.get("type");
    filters.forEach((item) => item.classList.toggle("active", item.dataset.searchType === type));
  }
  if (input.value.trim().length >= 2) {
    runSearch({ reset: true }).catch((error) => {
      summaryEl.textContent = error.message || "Search failed.";
    });
  }
}

function renderSearchGroups(results, type) {
  const sections = [];

  if (type === "all" || type === "posts") {
    const posts = results.posts || [];
    sections.push(`
      <section class="panel analytics-card">
        <div class="panel-title"><span>Posts</span></div>
        ${posts.length ? posts.map((post) => `
          <article class="activity-post">
            <div>${escapeHtml(post.content || "")}</div>
            <div class="activity-post-meta">${escapeHtml(post.zone?.name || "Campus")} • ${escapeHtml(post.sentiment || "neutral")}</div>
          </article>
        `).join("") : '<div class="state state-illustrated"><div class="state-emoji">📝</div><div>No posts found.<br />Aucune publication trouvee.</div></div>'}
      </section>
    `);
  }

  if (type === "all" || type === "users") {
    const users = results.users || [];
    sections.push(`
      <section class="panel analytics-card">
        <div class="panel-title"><span>People</span></div>
        ${users.length ? users.map((user) => `
          <a class="search-result-item search-result-link" href="profile.html?u=${encodeURIComponent(user.username)}">
            <div class="search-result-left">
              <img class="avatar" src="${escapeAttr(getUserAvatarUrl(user, getAssetUrl))}" alt="User" loading="lazy" />
              <div>
                <div class="search-result-name">${escapeHtml(user.display_name || user.username)}</div>
                <div class="search-result-handle">@${escapeHtml(user.username)}</div>
              </div>
            </div>
          </a>
        `).join("") : '<div class="state state-illustrated"><div class="state-emoji">👥</div><div>No people found.<br />Aucun profil trouve.</div></div>'}
      </section>
    `);
  }

  if (type === "all" || type === "zones") {
    const zones = results.zones || [];
    sections.push(`
      <section class="panel analytics-card">
        <div class="panel-title"><span>Zones</span></div>
        ${zones.length ? zones.map((zone) => `
          <a class="search-result-item search-result-link" href="zone.html?id=${encodeURIComponent(zone.id)}">
            <div>
              <div class="search-result-name">${escapeHtml(zone.name)}</div>
              <div class="search-result-handle">${escapeHtml(zone.description || "")}</div>
            </div>
          </a>
        `).join("") : '<div class="state state-illustrated"><div class="state-emoji">🗺️</div><div>No zones found.<br />Aucune zone trouvee.</div></div>'}
      </section>
    `);
  }

  return sections.join("");
}

function renderSearchSkeleton(root) {
  root.innerHTML = `
    <section class="panel analytics-card skeleton-stack">
      <div class="skeleton-card">
        <div class="skeleton-line short"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line medium"></div>
      </div>
      <div class="skeleton-card">
        <div class="skeleton-line short"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line medium"></div>
      </div>
    </section>
  `;
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

document.addEventListener("DOMContentLoaded", () => {
  if (!document.body.dataset.pageSearch) return;
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();
  initSearchPage();
});
