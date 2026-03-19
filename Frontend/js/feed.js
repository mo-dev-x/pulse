import { requireAuth, apiFetch, logout, getAssetUrl } from "./auth.js";

let currentUser = null;
let currentPosts = [];
let zoneAutocomplete = null;
let currentFeedMode = "home";

const FEED_MODES = {
  home: {
    endpoint: "/api/posts/feed",
    emptyMessage: "No posts yet. Follow users to see posts in your feed.",
  },
  myPosts: {
    endpoint: "/api/posts/me",
    emptyMessage: "You don’t have any public posts yet.",
  },
  myAnonymous: {
    endpoint: "/api/posts/me/anonymous",
    emptyMessage: "You don’t have any anonymous posts yet.",
  },
};

document.addEventListener("DOMContentLoaded", async () => {
  // 1) protect the page (if the function exists...faskhtha)
  requireAuth();
  // 2) setup small UI ths
  setupUserMenu();
  setupModal();
  setupCharCounter();
  setupZonePicker();
  setupFeedModeSwitch();
  //show search results
  setupGlobalUserSearch();

  // 3) show top parts
  renderStories();
  renderMessages();

  // 4) load posts
  // loadFeed();
  await initFeedPage();
});


function setupGlobalUserSearch() {
  const input = document.getElementById("globalSearch");
  const resultsEl = document.getElementById("searchResults");

  if (!input || !resultsEl) return;

  let debounceTimer = null;

  input.addEventListener("input", () => {
    const query = input.value.trim();

    clearTimeout(debounceTimer);

    if (query.length < 2) {
      hideSearchResults();
      return;
    }

    debounceTimer = setTimeout(async () => {
      await searchUsers(query);
    }, 250);
  });

  document.addEventListener("click", (e) => {
    const insideSearch =
      input.contains(e.target) ||
      resultsEl.contains(e.target);

    if (!insideSearch) {
      hideSearchResults();
    }
  });
}

async function searchUsers(query) {
  const resultsEl = document.getElementById("searchResults");
  if (!resultsEl) return;

  try {
    const data = await apiFetch(`/api/search/users?q=${encodeURIComponent(query)}`, {
      method: "GET",
    });

    const users = data.users || [];
    renderSearchResults(users);
  } catch (err) {
    resultsEl.style.display = "block";
    resultsEl.innerHTML = `<div class="search-empty">${escapeHtml(err.message || "Search failed")}</div>`;
  }
}

function renderSearchResults(users) {
  const resultsEl = document.getElementById("searchResults");
  if (!resultsEl) return;

  const filteredUsers = users.filter((user) => user.username !== currentUser?.username);

  if (!filteredUsers.length) {
    resultsEl.style.display = "block";
    resultsEl.innerHTML = `<div class="search-empty">No users found</div>`;
    return;
  }

  resultsEl.style.display = "block";
  resultsEl.innerHTML = filteredUsers.map((user) => {
    const avatarUrl = user.profile_picture
      ? getAssetUrl(user.profile_picture)
      : `https://i.pravatar.cc/80?u=${encodeURIComponent(user.username)}`;

    return `
      <div class="search-result-item">
        <div class="search-result-left">
          <img class="avatar" src="${escapeAttr(avatarUrl)}" alt="User" />
          <div>
            <div class="search-result-name">${escapeHtml(user.display_name || user.username)}</div>
            <div class="search-result-handle">@${escapeHtml(user.username)}</div>
          </div>
        </div>
        <button class="btn btn-accent btn-sm" data-follow-user="${escapeAttr(user.username)}">
          Follow
        </button>
      </div>
    `;
  }).join("");

  resultsEl.querySelectorAll("[data-follow-user]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const username = btn.dataset.followUser;
      await followUser(username, btn);
    });
  });
}

function hideSearchResults() {
  const resultsEl = document.getElementById("searchResults"); //mnbench lro7i
  if (!resultsEl) return;

  resultsEl.style.display = "none";
  resultsEl.innerHTML = "";
}

async function followUser(username, btn) {
  try {
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Following...";
    }

    const data = await apiFetch(`/api/follow/@${encodeURIComponent(username)}`, {
      method: "POST",
    });

    if (btn) {
      btn.textContent = "Following";
    }

    showToast(data.message || `You are now following @${username}`, "success");
    hideSearchResults();

    if (currentFeedMode === "home") {
      await loadCurrentFeed();
    }
  } catch (err) {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Follow";
    }
    showToast(err.message || "Follow failed", "error");
  }
}


async function initFeedPage() {
  try {
    showState("Loading feed...");
    await loadCurrentUser();
    await loadCurrentFeed();
  } catch (err) {
    showState(err.message || "Failed to load feed.");
  }
}

async function loadCurrentUser() {
  const data = await apiFetch("/api/auth/me", { method: "GET" });
  currentUser = data.user;
  renderCurrentUser(currentUser);
}

function renderCurrentUser(user) {
  const nameEl = document.getElementById("meName");
  const handleEl = document.getElementById("meHandle");

  const sidebarAvatar = document.getElementById("sidebarAvatar");
  const topbarAvatar = document.getElementById("topbarAvatar");
  const composerAvatar = document.getElementById("composerAvatar");

  const displayName = user?.display_name || user?.username || "Pulse User";
  const username = user?.username || "user";

  if (nameEl) nameEl.textContent = displayName;
  if (handleEl) handleEl.textContent = `@${username}`;

  const avatarUrl = user?.profile_picture
    ? getAssetUrl(user.profile_picture)
    : `https://i.pravatar.cc/100?u=${encodeURIComponent(username)}`;

  if (topbarAvatar) topbarAvatar.src = avatarUrl;
  if (sidebarAvatar) sidebarAvatar.src = avatarUrl;
  if (composerAvatar) composerAvatar.src = avatarUrl;

}

/* --------------- USER MENU (avatar dropdown) -------------- */

function setupUserMenu() {
  const chip = document.getElementById("userChip");
  const btnLogout = document.getElementById("btnLogout");
  const profileLink = document.getElementById("topbarProfileLink");

  if (!chip) return;

  chip.addEventListener("click", (e) => {
    if (profileLink && profileLink.contains(e.target)) {
      return;
    }

    chip.classList.toggle("open");
    e.stopPropagation();
  });

  // click anywhere else closes it
  document.addEventListener("click", () => chip.classList.remove("open"));

  if (btnLogout) {
    btnLogout.addEventListener("click", (e) => {
      e.stopPropagation();
      logout();
    });
  }
}

/* -------------- MODAL(Create Post) ---------------- */
function setupModal() {
  const modal = document.getElementById("createModal");
  const form = document.getElementById("createForm");
  const btnClose = document.getElementById("btnCloseModal");
  const btnCancel = document.getElementById("btnCancel");

  if (!modal || !form) return;

  //buttons that open the modal
  const openBtns = [
    "btnOpenCreateTop",
    "btnOpenCreateLeft",
    "btnOpenCreateComposer",
    "btnOpenCreateSmall",
  ]
    .map((id) => document.getElementById(id))
    .filter(Boolean);

  openBtns.forEach((btn) => btn.addEventListener("click", openModal));
  if (btnClose) btnClose.addEventListener("click", closeModal);
  if (btnCancel) btnCancel.addEventListener("click", closeModal);

  //clicking outside closes it
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  //submit post
  form.addEventListener("submit", onCreatePostSubmit);

  function openModal() {
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    const t = document.getElementById("postText");
    if (t) t.focus();
  }

  function closeModal() {
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    hideCreateError();
    form.reset();
    if (zoneAutocomplete) zoneAutocomplete.clearSelection();
    const hiddenZoneId = document.getElementById("zoneId");
    if (hiddenZoneId) hiddenZoneId.value = "";
    updateCharCount();
  }
}

function setupZonePicker() {
  if (typeof window.initZoneAutocomplete !== "function") return;
  zoneAutocomplete = window.initZoneAutocomplete("zoneSearch", "zoneResults", (zone) => {
    const zoneIdInput = document.getElementById("zoneId");
    if (zoneIdInput) zoneIdInput.value = String(zone.id);
  });
}

/* --------------- COUNTER ---------------- */
function setupCharCounter() {
  const textarea = document.getElementById("postText");
  if (!textarea) return;

  textarea.addEventListener("input", updateCharCount);
  updateCharCount();
}

function updateCharCount() {
  const textarea = document.getElementById("postText");
  const count = document.getElementById("charCount");
  if (!textarea || !count) return;

  count.textContent = String(textarea.value.length);
}

function setupFeedModeSwitch() {
  const buttons = document.querySelectorAll("[data-feed-mode]");

  buttons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const mode = btn.dataset.feedMode;
      if (!FEED_MODES[mode] || mode === currentFeedMode) return;

      currentFeedMode = mode;
      updateFeedModeUi();
      await loadCurrentFeed();
    });
  });
}

function updateFeedModeUi() {
  document.querySelectorAll("[data-feed-mode]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.feedMode === currentFeedMode);
  });
}

/* -------------- STATE (Loading/Empty) ---------------- */
function showState(text) {
  const box = document.getElementById("stateBox");
  if (!box) return;
  box.textContent = text;
  box.style.display = "block";
}

function hideState() {
  const box = document.getElementById("stateBox");
  if (!box) return;
  box.style.display = "none";
}

/* -------------- ERROR BOX(create post) ---------------- */
function showCreateError(msg) {
  const el = document.getElementById("createError");
  if (!el) return;
  el.textContent = msg;
  el.style.display = "block";
}

function hideCreateError() {
  const el = document.getElementById("createError");
  if (!el) return;
  el.textContent = "";
  el.style.display = "none";
}
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 2600);
}

/* --------------- FEED ---------------- */
async function loadCurrentFeed() {
  const feedEl = document.getElementById("feed");
  if (!feedEl) return;

  const modeConfig = FEED_MODES[currentFeedMode];
  if (!modeConfig) return;

  feedEl.innerHTML = "";

  try {
    const data = await apiFetch(modeConfig.endpoint, { method: "GET" });
    const posts = data.posts || [];

    currentPosts = posts.map(normalizePost);

    if (!currentPosts.length) {
      showState(data.message || modeConfig.emptyMessage);
      return;
    }

    hideState();

    currentPosts.forEach((post) => {
      feedEl.appendChild(renderPostCard(post));
    });
  } catch (err) {
    showState(err.message || "Failed to load feed.");
  }
}
  // } catch (err) {
  //   console.warn("Backend failed, using demo posts:", err.message);
  // }
  //fallback demo
  // hideState();
  // demoPosts().forEach((p) => feedEl.appendChild(renderPostCard(p)));


function normalizePost(p) {
  const media = Array.isArray(p.media) ? p.media : [];

  const firstImage = media.find((m) => m.file_type === "image");
  const firstVideo = media.find((m) => m.file_type === "video");

  const isAnonymous = Boolean(p.is_anonymous);
  const author = p.author || {};
  const zone = p.zone || null;

  const authorName = isAnonymous
    ? (author.pseudonym || "Anonymous")
    : (author.display_name || author.username || "User");

  const handle = isAnonymous
    ? "@anonymous"
    : (author.username ? `@${author.username}` : "@user");

  const mine = isAnonymous
    ? Boolean(author.is_you)
    : Boolean(currentUser && author.id === currentUser.id);

  const avatarSeed = isAnonymous
    ? `anon-${p.id}`
    : (author.username || author.display_name || p.id);

  const avatarUrl = !isAnonymous && author.profile_picture
    ? getAssetUrl(author.profile_picture)
    : `https://i.pravatar.cc/80?u=${encodeURIComponent(avatarSeed)}`;

  return {
    id: p.id,
    text: p.content || "",
    isAnonymous,
    authorName,
    handle,
    avatarUrl,
    zoneName: zone?.name || "Campus",
    timeRaw: p.created_at || "",
    timeLabel: formatRelativeTime(p.created_at),
    sentiment: p.sentiment || "neutral",
    imagePath: firstImage?.file_path || "",
    videoPath: firstVideo?.file_path || "",
    mine,
    reactions: {
      love: p.reactions?.["❤️"] ?? 0,
      fire: p.reactions?.["🔥"] ?? 0,
      sad: p.reactions?.["😢"] ?? 0,
    },
    myReaction: p.my_reaction || null,
    reactionCount: p.reaction_count ?? 0,
  };
}

function sentimentBadge(sentiment) {
  const s = String(sentiment || "neutral").toLowerCase();
  if (s.includes("pos")) return { cls: "green", label: "🟢 Positive" };
  if (s.includes("neg")) return { cls: "red", label: "🔴 Negative" };
  return { cls: "yellow", label: "🟡 Neutral" };
}

function renderPostCard(post) {
  const card = document.createElement("article");
  card.className = "panel post";
  card.dataset.id = post.id;

  const badge = sentimentBadge(post.sentiment);

  card.innerHTML = `
    <div class="post-head">
      <div class="post-user">
        <img class="avatar" src="${escapeAttr(post.avatarUrl)}" alt="User" />
        <div class="post-meta">
          <div class="u">
            ${escapeHtml(post.authorName)}
            <span class="badge ${badge.cls}">${badge.label}</span>
          </div>
          <div class="m">
            ${escapeHtml(post.handle)} • ${escapeHtml(post.zoneName)} • ${escapeHtml(post.timeLabel)}
          </div>
        </div>
      </div>

      <div class="post-menu">
        ${
          post.mine
            ? `<button class="iconbtn" data-action="delete" title="Delete">🗑️</button>`
            : `<button class="iconbtn" title="More">⋯</button>`
        }
      </div>
    </div>

    ${post.text ? `<div class="post-text">${escapeHtml(post.text)}</div>` : ""}

    ${renderMedia(post)}

    <div class="post-actions">
      <div class="actions-left reaction">
        <button class="react-btn ${post.myReaction === "❤️" ? "is-active" : ""}" data-emoji="❤️">
          ❤️ <span>${post.reactions.love ?? 0}</span>
        </button>

        <button class="react-btn ${post.myReaction === "🔥" ? "is-active" : ""}" data-emoji="🔥">
          🔥 <span>${post.reactions.fire ?? 0}</span>
        </button>

        <button class="react-btn ${post.myReaction === "😢" ? "is-active" : ""}" data-emoji="😢">
          😢 <span>${post.reactions.sad ?? 0}</span>
        </button>
      </div>

      <button class="iconbtn" title="Share">
        <i class="uil uil-share"></i>
      </button>
    </div>
  `;

  card.addEventListener("click", async (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;

    const action = btn.dataset.action;
    const emoji = btn.dataset.emoji;

    if (action === "delete") {
      await onDeletePost(post.id);
      return;
    }

    if (emoji) {
      await onReact(post.id, emoji);
    }
  });

  return card;
}

function renderMedia(post) {
  if (post.imagePath) {
    return `
      <div class="post-media">
        <img
          src="${escapeAttr(getAssetUrl(post.imagePath))}"
          alt="Post media"
          onerror="this.closest('.post-media').innerHTML='<div style=&quot;padding:14px;color:rgba(229,231,235,.65)&quot;>Media unavailable ❌</div>';"
        />
      </div>
    `;
  }

  if (post.videoPath) {
    return `
      <div class="post-media">
        <video
          controls
          src="${escapeAttr(getAssetUrl(post.videoPath))}"
          onerror="this.closest('.post-media').innerHTML='<div style=&quot;padding:14px;color:rgba(229,231,235,.65)&quot;>Media unavailable ❌</div>';"
        ></video>
      </div>
    `;
  }
  return "";
}

/*------------ REACTIONS (+ DELETE) -------------- */
async function onReact(postId, emoji) {
  const post = currentPosts.find((p) => p.id === postId);
  if (!post) return;

  const isRemoving = post.myReaction === emoji;

  try {
    if (isRemoving) {
      await apiFetch(`/api/posts/${postId}/react`, {
        method: "DELETE",
      });
      showToast("Reaction removed", "success");
    } else {
      await apiFetch(`/api/posts/${postId}/react`, {
        method: "POST",
        body: JSON.stringify({ emoji }),
      });
      showToast("Reaction updated", "success");
    }
    await loadCurrentFeed();
  } catch (err) {
    showToast(err.message || "Reaction failed", "error");
  }
}

async function onDeletePost(postId) {
  if (!confirm("Delete this post?")) return;

  try {
    await apiFetch(`/api/posts/${postId}`, { method: "DELETE" });
    showToast("Post deleted", "success");
    await loadCurrentFeed();

  } catch (err) {
    showToast("Delete failed: " + err.message, "error");
  }
}

/* -------------- CREATE POST --------------- */
async function onCreatePostSubmit(e) {
  e.preventDefault();
  hideCreateError();
  const form = document.getElementById("createForm");

  const text = document.getElementById("postText").value.trim();
  const anonymous = document.getElementById("anonymousToggle").checked;
  const zoneId = document.getElementById("zoneId").value;
  const imageInput = document.getElementById("imageFile");
  const img = imageInput ? imageInput.files[0] : null;


  if (text.length < 10) {
    showCreateError("Text must be at least 10 characters.");
    return;
  }

  if (text.length > 500) {
    showCreateError("Text must not exceed 500 characters.");
    return;
  }
  const submitBtn = e.target.querySelector('button[type="submit"]');

  try {
    if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = "Posting...";
  }
    const fd = new FormData();
    fd.append("content", text);
    fd.append("is_anonymous", String(anonymous));
    if (zoneId) fd.append("zone_id", zoneId);
    if (img) fd.append("image", img);

    const result = await apiFetch("/api/posts", {
      method: "POST",
      body: fd,
    });
    const modal = document.getElementById("createModal");

    if (modal) {
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
    }

    if (form) form.reset();
    if (zoneAutocomplete) zoneAutocomplete.clearSelection();
    const hiddenZoneId = document.getElementById("zoneId");
    if (hiddenZoneId) hiddenZoneId.value = "";

    updateCharCount();
    if (currentFeedMode === "home") {
      currentFeedMode = anonymous ? "myAnonymous" : "myPosts";
      updateFeedModeUi();
    }

    showToast(result.message || "Post created successfully.", "success");
    await loadCurrentFeed();

  } catch (err) {
    showCreateError(err.message || "Create post failed");

  }finally { //prevents double submit
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Post";
    }
  }
}

/* -------------- RIGHT PANEL(demo) --------------- */
function renderMessages() {
  const msgList = document.getElementById("msgList");
  if (!msgList) return;

  const items = [
    { name: "Eden Quist", snippet: "Just woke up bruh", img: 2 },
    { name: "Franco Della", snippet: "Received bruh. Thanks!", img: 5 },
    { name: "Jane Doe", snippet: "ok", img: 10 },
    { name: "Daniella Jackson", snippet: "2 new messages", img: 16 },
    { name: "Juliet Mukorey", snippet: "lol u right", img: 24 },
  ];

  msgList.innerHTML = items
    .map(
      (i) => `
    <div class="msg">
      <img class="avatar" src="https://i.pravatar.cc/80?img=${i.img}" alt=""/>
      <div>
        <div class="t">${escapeHtml(i.name)}</div>
        <div class="s">${escapeHtml(i.snippet)}</div>
      </div>
    </div>
  `
    )
    .join("");
}

/* ---------------- STORIES(Campus Pulse card) ---------------- */
function renderStories() {
  const row = document.getElementById("storiesRow");
  if (!row) return;

  row.innerHTML = `
    <div class="story pulse-card">
      <div class="pulse-left">
        <div class="pulse-ring">
          <div class="pulse-ring-inner">
            <div class="pulse-kicker">Campus mood</div>
            <div class="pulse-mood">Happy</div>
            <div class="pulse-meta">Last 24h • 341 posts</div>
            <div class="pulse-dots" aria-hidden="true">
              <span></span><span></span><span></span><span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>
      <div class="pulse-right">
          <div class="emotile stress"><div class="emoji">😅</div><div class="label">Stress</div></div>
          <div class="emotile joy"><div class="emoji">😄</div><div class="label">Joy</div></div>
          <div class="emotile tired"><div class="emoji">😴</div><div class="label">Tired</div></div>
          <div class="emotile calm"><div class="emoji">😌</div><div class="label">Calm</div></div>
          <div class="emotile connected"><div class="emoji">🤝</div><div class="label">Connected</div></div>
          <div class="emotile frustrated"><div class="emoji">😤</div><div class="label">Frustrated</div></div>
      </div>
    </div>
  `;
}

function formatRelativeTime(dateLike) {
  const d = new Date(dateLike);
  if (Number.isNaN(d.getTime())) return "Recently";

  const diffMs = Date.now() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 60) return "Just now";

  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;

  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;

  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;

  return d.toLocaleDateString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/* -------------- SAFE USE HTML ---------------- */
function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
function escapeAttr(str) {
  return escapeHtml(str).replaceAll("`", "&#096;");
}

// /* ------------- OPTIONAL notifications (only if exists) ---------------- */
// const notificationsBtn = document.getElementById("notifications");
// const popup = document.getElementById("notification-popup");

// if (notificationsBtn && popup) {
//   notificationsBtn.addEventListener("click", (e) => {
//     e.preventDefault();
//     popup.classList.toggle("show");
//   });

//   document.addEventListener("click", (e) => {
//     const inside = notificationsBtn.contains(e.target) || popup.contains(e.target);
//     if (!inside) popup.classList.remove("show");
//   });
// }
