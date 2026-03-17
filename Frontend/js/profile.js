import { apiFetch, requireAuth, logout } from "./auth.js";

const els = {
  topbarAvatar: document.getElementById("topbarAvatar"),
  sidebarAvatar: document.getElementById("sidebarAvatar"),
  sidebarName: document.getElementById("sidebarName"),
  sidebarHandle: document.getElementById("sidebarHandle"),

  profileAvatar: document.getElementById("profileAvatar"),
  profileDisplayName: document.getElementById("profileDisplayName"),
  profileHandle: document.getElementById("profileHandle"),
  profileBio: document.getElementById("profileBio"),

  statPosts: document.getElementById("statPosts"),
  statFollowers: document.getElementById("statFollowers"),
  statFollowing: document.getElementById("statFollowing"),

  aboutName: document.getElementById("aboutName"),
  aboutHandle: document.getElementById("aboutHandle"),
  aboutFaculty: document.getElementById("aboutFaculty"),
  aboutZone: document.getElementById("aboutZone"),
  aboutJoined: document.getElementById("aboutJoined"),

  summaryMood: document.getElementById("summaryMood"),
  summaryZone: document.getElementById("summaryZone"),
  summaryPostCount: document.getElementById("summaryPostCount"),

  sideFaculty: document.getElementById("sideFaculty"),
  sideZone: document.getElementById("sideZone"),
  sideJoined: document.getElementById("sideJoined"),
  sideMood: document.getElementById("sideMood"),

  profilePostsFeed: document.getElementById("profilePostsFeed"),
  profilePostsState: document.getElementById("profilePostsState"),
  mediaGrid: document.getElementById("mediaGrid"),
  mediaState: document.getElementById("mediaState"),

  userChip: document.getElementById("userChip"),
  btnLogout: document.getElementById("btnLogout"),
  btnViewFeed: document.getElementById("btnViewFeed"),
  btnShareProfile: document.getElementById("btnShareProfile"),
};

let currentUser = null;
let publicPosts = [];
let anonymousPosts = [];
let profileData = null;

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  setupMenu();
  setupTabs();
  setupActions();

  try {
    await initProfilePage();
  } catch (err) {
    console.error("Profile page init error:", err);
    if (els.profilePostsState) {
      els.profilePostsState.textContent = err.message || "Could not load profile.";
      els.profilePostsState.style.display = "block";
    }
    if (els.mediaState) {
      els.mediaState.textContent = "Could not load media.";
      els.mediaState.style.display = "block";
    }
  }
});

async function initProfilePage() {
  const meRes = await apiFetch("/api/auth/me", { method: "GET" });
  currentUser = meRes.user;

  const profileRes = await apiFetch(`/api/users/@${encodeURIComponent(currentUser.username)}`, {
    method: "GET",
  });
  profileData = profileRes;

  const myPostsRes = await apiFetch("/api/posts/me", { method: "GET" });
  publicPosts = (myPostsRes.posts || []).map(normalizePost);

  const myAnonRes = await apiFetch("/api/posts/me/anonymous", { method: "GET" });
  anonymousPosts = (myAnonRes.posts || []).map(normalizePost);

  renderUser(currentUser, profileData);
  renderPosts(publicPosts);
  renderMedia([...publicPosts, ...anonymousPosts]);
}

function setupMenu() {
  if (!els.userChip) return;

  const profileLink = document.getElementById("topbarProfileLink");

  els.userChip.addEventListener("click", (e) => {
    if (profileLink && profileLink.contains(e.target)) {
      return;
    }

    e.stopPropagation();
    els.userChip.classList.toggle("open");
  });

  document.addEventListener("click", () => {
    els.userChip.classList.remove("open");
  });
}

function setupTabs() {
  const tabs = document.querySelectorAll(".profile-tab");
  const panels = document.querySelectorAll(".profile-tab-panel");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      panels.forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const key = tab.dataset.tab;
      document.getElementById(`tab-${key}`).classList.add("active");
    });
  });
}

function setupActions() {
  els.btnLogout?.addEventListener("click", () => {
    logout();
  });

  els.btnViewFeed?.addEventListener("click", () => {
    window.location.href = "feed.html";
  });

  els.btnShareProfile?.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      alert("Profile link copied.");
    } catch {
      alert("Could not copy the profile link.");
    }
  });
}

function renderUser(user, profile) {
  const publicUser = profile?.user || {};
  const displayName = user?.display_name || user?.username || "Pulse User";
  const username = user?.username || "user";
  const bio = user?.bio || "No bio yet.";
  const joined = formatJoined(user?.created_at);

  const avatarUrl = user?.profile_picture
    ? `/uploads/${user.profile_picture}`
    : `https://i.pravatar.cc/180?u=${encodeURIComponent(username)}`;

  if (els.topbarAvatar) els.topbarAvatar.src = avatarUrl;
  if (els.sidebarAvatar) els.sidebarAvatar.src = avatarUrl;
  if (els.profileAvatar) els.profileAvatar.src = avatarUrl;

  if (els.sidebarName) els.sidebarName.textContent = displayName;
  if (els.sidebarHandle) els.sidebarHandle.textContent = `@${username}`;

  if (els.profileDisplayName) els.profileDisplayName.textContent = displayName;
  if (els.profileHandle) els.profileHandle.textContent = `@${username}`;
  if (els.profileBio) els.profileBio.textContent = bio;

  const faculty = "Université Laval";
  const favoriteZone = publicPosts[0]?.zoneName || "Campus";
  const mood = computeOverallMood([...publicPosts, ...anonymousPosts]);

  if (els.statPosts) els.statPosts.textContent = String(publicPosts.length + anonymousPosts.length);
  if (els.statFollowers) els.statFollowers.textContent = String(publicUser.follower_count ?? 0);
  if (els.statFollowing) els.statFollowing.textContent = String(publicUser.following_count ?? 0);

  if (els.aboutName) els.aboutName.textContent = displayName;
  if (els.aboutHandle) els.aboutHandle.textContent = `@${username}`;
  if (els.aboutFaculty) els.aboutFaculty.textContent = faculty;
  if (els.aboutZone) els.aboutZone.textContent = favoriteZone;
  if (els.aboutJoined) els.aboutJoined.textContent = joined;

  if (els.summaryMood) els.summaryMood.textContent = mood;
  if (els.summaryZone) els.summaryZone.textContent = favoriteZone;
  if (els.summaryPostCount) {
    const total = publicPosts.length + anonymousPosts.length;
    els.summaryPostCount.textContent = `${total} post${total !== 1 ? "s" : ""}`;
  }

  if (els.sideFaculty) els.sideFaculty.textContent = faculty;
  if (els.sideZone) els.sideZone.textContent = favoriteZone;
  if (els.sideJoined) els.sideJoined.textContent = joined;
  if (els.sideMood) els.sideMood.textContent = mood;
}

function renderPosts(posts) {
  if (!els.profilePostsFeed || !els.profilePostsState) return;

  els.profilePostsFeed.innerHTML = "";

  if (!posts.length) {
    els.profilePostsState.textContent = "No public posts yet.";
    els.profilePostsState.style.display = "block";
    return;
  }

  els.profilePostsState.style.display = "none";

  posts.forEach((post) => {
    els.profilePostsFeed.appendChild(createPostCard(post));
  });
}

function renderMedia(posts) {
  if (!els.mediaGrid || !els.mediaState) return;

  els.mediaGrid.innerHTML = "";

  const mediaPosts = posts.filter((p) => p.imageUrl);

  if (!mediaPosts.length) {
    els.mediaState.textContent = "No media yet.";
    els.mediaState.style.display = "block";
    return;
  }

  els.mediaState.style.display = "none";

  mediaPosts.forEach((post) => {
    const item = document.createElement("div");
    item.className = "media-item";
    item.innerHTML = `<img src="${escapeHtml(post.imageUrl)}" alt="Post media">`;
    els.mediaGrid.appendChild(item);
  });
}

function normalizePost(p) {
  const media = Array.isArray(p.media) ? p.media : [];
  const firstImage = media.find((m) => m.file_type === "image");
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

  const avatarUrl = !isAnonymous && author.profile_picture
    ? `/uploads/${author.profile_picture}`
    : `https://i.pravatar.cc/80?u=${encodeURIComponent(isAnonymous ? `anon-${p.id}` : (author.username || p.id))}`;

  return {
    id: p.id,
    text: p.content || "",
    isAnonymous,
    authorName,
    handle,
    avatarUrl,
    zoneName: zone?.name || "Campus",
    time: p.created_at || "",
    sentiment: p.sentiment || "neutral",
    imageUrl: firstImage ? `/${String(firstImage.file_path).replace(/^\/+/, "")}` : "",
    mine,
    reactions: {
      like: p.reactions?.["❤️"] ?? 0,
      wow: p.reactions?.["🔥"] ?? 0,
      sad: p.reactions?.["🥲"] ?? 0,
    },
  };
}

function createPostCard(post) {
  const card = document.createElement("article");
  card.className = "panel post";

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
            ${escapeHtml(post.handle)} • ${escapeHtml(post.zoneName)} • ${escapeHtml(formatTimestamp(post.time))}
          </div>
        </div>
      </div>
    </div>

    ${post.text ? `<div class="post-text">${escapeHtml(post.text)}</div>` : ""}

    ${
      post.imageUrl
        ? `
      <div class="post-media">
        <img src="${escapeAttr(post.imageUrl)}" alt="Post media" />
      </div>
    `
        : ""
    }

    <div class="post-actions">
      <div class="actions-left">
        <div class="reaction">
          <button class="react-btn">❤️ <span>${post.reactions.like}</span></button>
          <button class="react-btn">🔥 <span>${post.reactions.wow}</span></button>
          <button class="react-btn">🥲 <span>${post.reactions.sad}</span></button>
        </div>
      </div>
    </div>
  `;

  return card;
}

function sentimentBadge(sentiment) {
  const s = String(sentiment || "neutral").toLowerCase();
  if (s.includes("pos")) return { cls: "green", label: "🟢 Positive" };
  if (s.includes("neg")) return { cls: "red", label: "🔴 Negative" };
  return { cls: "yellow", label: "🟡 Neutral" };
}

function computeOverallMood(posts) {
  if (!posts.length) return "Mostly Neutral";

  const scores = { positive: 0, neutral: 0, negative: 0 };

  posts.forEach((post) => {
    const key = String(post.sentiment || "neutral").toLowerCase();
    if (scores[key] !== undefined) scores[key] += 1;
  });

  const top = Object.entries(scores).sort((a, b) => b[1] - a[1])[0]?.[0] || "neutral";

  if (top === "positive") return "Mostly Happy";
  if (top === "negative") return "Mostly Stressed";
  return "Mostly Neutral";
}

function formatTimestamp(dateLike) {
  const d = new Date(dateLike);
  if (Number.isNaN(d.getTime())) return "Recently";

  return d.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatJoined(dateLike) {
  const d = new Date(dateLike);
  if (Number.isNaN(d.getTime())) return "Recently joined";

  return d.toLocaleString([], {
    month: "long",
    year: "numeric",
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

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}