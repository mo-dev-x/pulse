import { requireAuth, apiFetch, logout } from "./auth.js";

console.log("feed.js loaded");

document.addEventListener("DOMContentLoaded", () => {
  // 1) protect the page (if the function exists...faskhtha)
  requireAuth();
  // 2) setup small UI ths
  setupUserMenu();
  setupModal();
  setupCharCounter();
  setupZonePicker();

  // 3) show top parts
  renderStories();
  renderMessages();

  // 4) load posts
  loadFeed();
});

let zoneAutocomplete = null;

/* --------------- USER MENU (avatar dropdown) -------------- */

function setupUserMenu() {
  const chip = document.getElementById("userChip");
  const btnLogout = document.getElementById("btnLogout");

  if (!chip) return;

  chip.addEventListener("click", (e) => {
    chip.classList.toggle("open"); // open/close menu
    e.stopPropagation();
  });

  // click anywhere else closes it
  document.addEventListener("click", () => chip.classList.remove("open"));

  if (btnLogout) {
    btnLogout.addEventListener("click", (e) => {
      e.stopPropagation();
      logout();
      // window.location.href = "login.html";
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

/* --------------- FEED ---------------- */
async function loadFeed() {
  showState("Loading feed…");

  const feedEl = document.getElementById("feed");
  if (!feedEl) return;
  feedEl.innerHTML = "";

  //try backend first
  try {
    if (typeof apiFetch !== "function") throw new Error("apiFetch not found");

    const data = await apiFetch("/api/posts/feed", { method: "GET" });

    //sometimes backend returns different shapes
    let posts = [];
    if (Array.isArray(data)) posts = data;
    else if (Array.isArray(data?.posts)) posts = data.posts;
    else if (Array.isArray(data?.data?.posts)) posts = data.data.posts;

    if (!posts.length) {
      showState("No posts yet.");
      return;
    }

    hideState();
    posts.forEach((p) => feedEl.appendChild(renderPostCard(normalizePost(p))));
    return;
  } catch (err) {
    console.warn("Backend failed, using demo posts:", err.message);
  }

  //fallback demo
  hideState();
  demoPosts().forEach((p) => feedEl.appendChild(renderPostCard(p)));
}

function normalizePost(p) {
  return {
    id: p.id ?? p.post_id ?? crypto.randomUUID(),
    username: p.username ?? p.user?.username ?? "Anonymous",
    handle: p.handle ?? (p.username ? `@${p.username}` : "@anon"),
    zone: p.zone_name ?? p.zone ?? "Zone",
    time: p.created_at ?? p.timestamp ?? "Just now",
    sentiment: p.sentiment ?? "neutral",
    text: p.text ?? p.content ?? "",
    imageUrl: p.image_url ?? p.imageUrl ?? "",
    videoUrl: p.video_url ?? p.videoUrl ?? "",
    mine: Boolean(p.mine ?? p.is_owner ?? false),
    reactions: p.reactions ?? { like: 0, wow: 0, sad: 0 },
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
        <img class="avatar" src="https://i.pravatar.cc/80?u=${encodeURIComponent(
          post.handle
        )}" alt="User"/>
        <div class="post-meta">
          <div class="u">${escapeHtml(post.username)}
            <span class="badge ${badge.cls}">${badge.label}</span>
          </div>
          <div class="m">${escapeHtml(post.zone)} • ${escapeHtml(post.time)}</div>
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
        <button class="react-btn" data-react="like">❤️ <span>${post.reactions.like ?? 0}</span></button>
        <button class="react-btn" data-react="wow">🔥 <span>${post.reactions.wow ?? 0}</span></button>
        <button class="react-btn" data-react="sad">🥲 <span>${post.reactions.sad ?? 0}</span></button>
      </div>

      <button class="iconbtn" title="Share"><i class="uil uil-share"></i></button>
    </div>
  `;

  //1 event listener for the whole card
  card.addEventListener("click", async (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;

    const action = btn.dataset.action;
    const react = btn.dataset.react;

    if (action === "delete") {
      await onDeletePost(post.id, card);
    }

    if (react) {
      await onReact(post.id, react, btn);
    }
  });

  return card;
}

function renderMedia(post) {
  if (post.imageUrl) {
    return `
      <div class="post-media">
        <img src="${escapeAttr(post.imageUrl)}" alt="Post media"
          onerror="this.closest('.post-media').innerHTML='<div style=&quot;padding:14px;color:rgba(229,231,235,.65)&quot;>Media unavailable ❌</div>';"/>
      </div>`;
  }

  if (post.videoUrl) {
    return `
      <div class="post-media">
        <video controls src="${escapeAttr(post.videoUrl)}"
          onerror="this.closest('.post-media').innerHTML='<div style=&quot;padding:14px;color:rgba(229,231,235,.65)&quot;>Media unavailable ❌</div>';"></video>
      </div>`;
  }

  return "";
}

/*------------ REACTIONS (+ DELETE) -------------- */
async function onReact(postId, type, btn) {
  // quick UI update
  const span = btn.querySelector("span");
  if (span) span.textContent = String((Number(span.textContent) || 0) + 1);

  // call backend if possible
  try {
    if (typeof apiFetch !== "function") return;

    await apiFetch(`/api/posts/${postId}/react`, {
      method: "POST",
      body: JSON.stringify({ type }),
    });
  } catch (err) {
    console.warn("React failed:", err.message);
  }
}

async function onDeletePost(postId, cardEl) {
  if (!confirm("Delete this post?")) return;

  try {
    if (typeof apiFetch !== "function") throw new Error("apiFetch not found");

    await apiFetch(`/api/posts/${postId}`, { method: "DELETE" });
    cardEl.remove();
  } catch (err) {
    alert("Delete failed: " + err.message);
  }
}

/* -------------- CREATE POST --------------- */
async function onCreatePostSubmit(e) {
  e.preventDefault();
  hideCreateError();

  const text = document.getElementById("postText").value.trim();
  if (text.length < 10) {
    showCreateError("Text must be at least 10 characters.");
    return;
  }

  const anonymous = document.getElementById("anonymousToggle").checked;
  const zoneId = document.getElementById("zoneId").value;
  const imageInput = document.getElementById("imageFile");
  const img = imageInput ? imageInput.files[0] : null;

  try {
    if (typeof apiFetch !== "function") throw new Error("apiFetch not found");

    const fd = new FormData();
    fd.append("content", text);
    fd.append("is_anonymous", String(anonymous));
    if (zoneId) fd.append("zone_id", zoneId);
    if (img) fd.append("image", img);

    await apiFetch("/api/posts", { method: "POST", body: fd });

    //close modal
    document.getElementById("createModal").classList.remove("open");
    if (zoneAutocomplete) zoneAutocomplete.clearSelection();
    document.getElementById("zoneId").value = "";

    // refresh
    loadFeed();
  } catch (err) {
    showCreateError(err.message);
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

/* --------------DEMO POSTS ---------------- */
function demoPosts() {
  return [
    {
      id: "p1",
      username: "Lana Rose",
      handle: "@lanarose",
      zone: "Zone 1 • Library",
      time: "12 minutes ago",
      sentiment: "neutral",
      text: "Midterm week is loud in my head even when the library is silent. If you’re struggling too: you’re not alone 🤍",
      imageUrl: "",
      videoUrl: "",
      mine: false,
      reactions: { like: 128, wow: 44, sad: 19 },
    },
    {
      id: "p2",
      username: "Anonymous",
      handle: "@anon",
      zone: "Zone 3 • Study Rooms",
      time: "30 minutes ago",
      sentiment: "negative",
      text: "I feel overwhelmed lately. Not failing… just constantly behind. If someone has tips to manage stress, please share.",
      imageUrl: "",
      videoUrl: "",
      mine: false,
      reactions: { like: 52, wow: 6, sad: 31 },
    },
        {
      id: "p2b",
      username: "Dina A.",
      handle: "@dinaa",
      zone: "Zone 6 • PEPS Gym",
      time: "40 minutes ago",
      sentiment: "positive",
      text: "I forced myself to do a 15-minute walk outside and it genuinely reset my brain. If you’re stuck, try a tiny move — it helps 🌿",
      imageUrl: "",
      videoUrl: "",
      mine: false,
      reactions: { like: 63, wow: 14, sad: 1 }
    },
    {
      id: "p2c",
      username: "Campus Notice",
      handle: "@pulse",
      zone: "Zone 2 • Cafeteria",
      time: "50 minutes ago",
      sentiment: "neutral",
      text: "FYI: cafeteria is extra crowded today around noon. If you want a calmer break, try going a bit earlier or later 🕒",
      imageUrl: "",
      videoUrl: "",
      mine: false,
      reactions: { like: 18, wow: 3, sad: 0 }
    },

  ];
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

/* ------------- OPTIONAL notifications (only if exists) ---------------- */
const notificationsBtn = document.getElementById("notifications");
const popup = document.getElementById("notification-popup");

if (notificationsBtn && popup) {
  notificationsBtn.addEventListener("click", (e) => {
    e.preventDefault();
    popup.classList.toggle("show");
  });

  document.addEventListener("click", (e) => {
    const inside = notificationsBtn.contains(e.target) || popup.contains(e.target);
    if (!inside) popup.classList.remove("show");
  });
}
