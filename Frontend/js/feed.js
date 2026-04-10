import {
  apiFetch,
  apiCall,
  getAssetUrl,
  logout,
  requireAuth,
  saveCurrentUser,
} from "./auth.js";
import { notify, runAsyncUI } from "./notify.js";
import { getDefaultAvatarUrl, getPostAvatarUrl, getProfileHref, getUserAvatarUrl } from "./avatar.js";
import { initLanguageControls, t } from "./i18n.js";
import { initMentionAutocomplete } from "./search.js";
import { initGlobalErrorHandler, initOfflineBanner, initThemeToggle, initUnreadBadges } from "./theme.js";
import { initInstallPrompt, initPushNotifications } from "./pwa.js";

const REACTION_EMOJIS = ["❤️", "👍", "👎", "😊", "😢", "😂", "😮", "🔥", "💪", "🙏"];

const FEED_MODES = {
  home: {
    endpoint: "/api/posts/feed",
    emptyMessage: "No posts yet. Follow users to see posts in your feed.",
  },
  myPosts: {
    endpoint: "/api/posts/me",
    emptyMessage: "You do not have any public posts yet.",
  },
  myAnonymous: {
    endpoint: "/api/posts/me/anonymous",
    emptyMessage: "You do not have any anonymous posts yet.",
  },
};

let currentUser = null;
let currentPosts = [];
let currentFeedMode = "home";
let currentPage = 1;
let hasNextPage = true;
let isFeedLoading = false;
let zoneAutocomplete = null;
let feedObserver = null;
let bookmarkedPostIds = new Set();
let pendingCreateImagePreviewUrl = null;
const expandedComments = new Set();
const commentsCache = new Map();

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initGlobalErrorHandler();
  initOfflineBanner();
  initUnreadBadges();
  initInstallPrompt();
  // Delay push subscription slightly so the page is interactive first
  setTimeout(() => initPushNotifications(), 3000);
  setupUserMenu();
  setupModal();
  setupCreateResendLink();
  setupCharCounter();
  setupZonePicker();
  setupFeedModeSwitch();
  setupGlobalUserSearch();
  setupFeedObserver();
  setupReactionPopupDismiss();
  setupMobileDrawer();
  renderStories();

  try {
    renderFeedSkeletons();
    showState("Loading feed...");
    await Promise.all([loadCurrentUser(), loadBookmarks()]);
    await resetAndLoadCurrentFeed();
  } catch (error) {
    showState(error.message || "Failed to load feed.");
  }
});

async function loadCurrentUser() {
  const data = await apiCall("feed/me", () => apiFetch("/api/auth/me", { method: "GET" }));
  currentUser = data.user;
  saveCurrentUser(currentUser);
  renderCurrentUser(currentUser);
  showVerificationBanner(currentUser);
}

function showVerificationBanner(user) {
  if (user?.is_verified) return;
  const existing = document.getElementById("verifyBanner");
  if (existing) return;

  const banner = document.createElement("div");
  banner.id = "verifyBanner";
  banner.className = "verify-banner";
  banner.innerHTML = `
    <span><i class="ui-icon ui-icon--action uil uil-envelope-check" aria-hidden="true"></i> Please verify your email to post.</span>
    <a class="verify-banner-link" href="verify-email.html">Verify now →</a>
    <button class="verify-banner-close" aria-label="Dismiss"><i class="ui-icon ui-icon--action uil uil-times" aria-hidden="true"></i></button>
  `;
  banner.querySelector(".verify-banner-close").addEventListener("click", () => banner.remove());

  // Insert before the composer
  const composer = document.querySelector(".composer");
  if (composer) {
    composer.parentNode.insertBefore(banner, composer);
  } else {
    document.querySelector(".main")?.prepend(banner);
  }

  // Intercept all post-creation buttons for unverified users
  ["btnOpenCreateTop", "btnOpenCreateLeft", "btnOpenCreateComposer", "btnOpenCreateSmall"].forEach((id) => {
    const btn = document.getElementById(id);
    if (btn) {
      btn.addEventListener("click", (e) => {
        if (!currentUser?.is_verified) {
          e.stopImmediatePropagation();
          window.location.href = "verify-email.html";
        }
      }, true); // capture phase so it fires before the modal opener
    }
  });
}

async function loadBookmarks() {
  try {
    const data = await apiFetch("/api/bookmarks?per_page=100", { method: "GET" });
    bookmarkedPostIds = new Set(
      (data.bookmarks || [])
        .map((entry) => entry.post?.id)
        .filter(Boolean)
    );
  } catch {
    bookmarkedPostIds = new Set();
  }
}

function renderCurrentUser(user) {
  const displayName = user?.display_name || user?.username || "Pulse User";
  const username = user?.username || "user";
  const avatarUrl = getUserAvatarUrl(user, getAssetUrl);

  const nameEl = document.getElementById("meName");
  const handleEl = document.getElementById("meHandle");
  const sidebarAvatar = document.getElementById("sidebarAvatar");
  const topbarAvatar = document.getElementById("topbarAvatar");
  const composerAvatar = document.getElementById("composerAvatar");

  if (nameEl) nameEl.textContent = displayName;
  if (handleEl) handleEl.textContent = `@${username}`;
  if (sidebarAvatar) sidebarAvatar.src = avatarUrl;
  if (topbarAvatar) topbarAvatar.src = avatarUrl;
  if (composerAvatar) composerAvatar.src = avatarUrl;
}

function setupUserMenu() {
  const chip = document.getElementById("userChip");
  const btnLogout = document.getElementById("btnLogout");
  const profileLink = document.getElementById("topbarProfileLink");

  if (!chip) return;

  chip.addEventListener("click", (event) => {
    if (profileLink && profileLink.contains(event.target)) return;
    chip.classList.toggle("open");
    event.stopPropagation();
  });

  document.addEventListener("click", () => chip.classList.remove("open"));
  btnLogout?.addEventListener("click", (event) => {
    event.stopPropagation();
    logout();
  });
}

function setupModal() {
  const modal = document.getElementById("createModal");
  const form = document.getElementById("createForm");
  const btnClose = document.getElementById("btnCloseModal");
  const btnCancel = document.getElementById("btnCancel");

  if (!modal || !form) return;

  [
    "btnOpenCreateTop",
    "btnOpenCreateLeft",
    "btnOpenCreateComposer",
    "btnOpenCreateSmall",
  ]
    .map((id) => document.getElementById(id))
    .filter(Boolean)
    .forEach((btn) => btn.addEventListener("click", openModal));

  btnClose?.addEventListener("click", closeModal);
  btnCancel?.addEventListener("click", closeModal);
  document.getElementById("imageFile")?.addEventListener("change", onCreateImageSelected);
  document.getElementById("clearImagePreview")?.addEventListener("click", clearCreateImagePreview);
  modal.addEventListener("click", (event) => {
    if (event.target === modal) closeModal();
  });
  form.addEventListener("submit", onCreatePostSubmit);

  function openModal() {
    clearCreateImagePreview();
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    document.getElementById("postText")?.focus();
  }

  function closeModal() {
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    hideCreateError();
    form.reset();
    zoneAutocomplete?.clearSelection();
    const hiddenZoneId = document.getElementById("zoneId");
    if (hiddenZoneId) hiddenZoneId.value = "";
    clearCreateImagePreview();
    updateCharCount();
  }
}

function onCreateImageSelected(event) {
  const file = event.target?.files?.[0];
  const previewWrap = document.getElementById("imagePreviewWrap");
  const preview = document.getElementById("imagePreview");
  if (!previewWrap || !preview) return;

  if (!file) {
    clearCreateImagePreview();
    return;
  }

  if (pendingCreateImagePreviewUrl) {
    URL.revokeObjectURL(pendingCreateImagePreviewUrl);
  }

  pendingCreateImagePreviewUrl = URL.createObjectURL(file);
  preview.src = pendingCreateImagePreviewUrl;
  previewWrap.hidden = false;
}

function clearCreateImagePreview() {
  const input = document.getElementById("imageFile");
  const previewWrap = document.getElementById("imagePreviewWrap");
  const preview = document.getElementById("imagePreview");

  if (pendingCreateImagePreviewUrl) {
    URL.revokeObjectURL(pendingCreateImagePreviewUrl);
    pendingCreateImagePreviewUrl = null;
  }

  if (input) input.value = "";
  if (preview) preview.removeAttribute("src");
  if (previewWrap) {
    previewWrap.hidden = true;
    previewWrap.setAttribute("hidden", "");
  }
}

function setupZonePicker() {
  if (typeof window.initZoneAutocomplete !== "function") return;
  zoneAutocomplete = window.initZoneAutocomplete("zoneSearch", "zoneResults", (zone) => {
    const zoneIdInput = document.getElementById("zoneId");
    if (zoneIdInput) zoneIdInput.value = String(zone.id);
  });
}

function setupCharCounter() {
  const textarea = document.getElementById("postText");
  if (!textarea) return;
  initMentionAutocomplete(textarea);
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
  document.querySelectorAll("[data-feed-mode]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const mode = btn.dataset.feedMode;
      if (!FEED_MODES[mode] || mode === currentFeedMode) return;
      currentFeedMode = mode;
      updateFeedModeUi();
      await resetAndLoadCurrentFeed();
    });
  });
}

function updateFeedModeUi() {
  document.querySelectorAll("[data-feed-mode]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.feedMode === currentFeedMode);
  });
}

function setupReactionPopupDismiss() {
  document.addEventListener("click", () => {
    document.querySelectorAll(".reaction-popup.open").forEach((p) => p.classList.remove("open"));
  });
}

function setupMobileDrawer() {
  const trigger  = document.getElementById("mobileMenuTrigger");
  const drawer   = document.getElementById("mobileDrawer");
  const overlay  = document.getElementById("mobileDrawerOverlay");
  const closeBtn = document.getElementById("mobileDrawerClose");
  if (!drawer || !overlay) return;

  function openDrawer() {
    drawer.classList.add("open");
    overlay.classList.add("open");
    document.body.style.overflow = "hidden";
  }
  function closeDrawer() {
    drawer.classList.remove("open");
    overlay.classList.remove("open");
    document.body.style.overflow = "";
  }

  trigger?.addEventListener("click", openDrawer);
  closeBtn?.addEventListener("click", closeDrawer);
  overlay.addEventListener("click", closeDrawer);
}

function setupFeedObserver() {
  const sentinel = document.getElementById("feedSentinel");
  if (!sentinel) return;

  feedObserver = new IntersectionObserver(async (entries) => {
    if (!entries[0]?.isIntersecting || isFeedLoading || !hasNextPage) return;
    currentPage += 1;
    await loadCurrentFeed({ append: true });
  }, { threshold: 0.2 });

  feedObserver.observe(sentinel);
}

async function resetAndLoadCurrentFeed() {
  currentPage = 1;
  hasNextPage = true;
  currentPosts = [];
  expandedComments.clear();
  commentsCache.clear();

  const feedEl = document.getElementById("feed");
  if (feedEl) feedEl.innerHTML = "";

  await loadCurrentFeed({ append: false });
}

async function loadCurrentFeed({ append = false } = {}) {
  const feedEl = document.getElementById("feed");
  const modeConfig = FEED_MODES[currentFeedMode];
  if (!feedEl || !modeConfig || isFeedLoading) return;

  isFeedLoading = true;
  if (!append) {
    renderFeedSkeletons();
    showState("Loading feed...");
  }

  try {
    const data = await apiCall(`feed/${currentFeedMode}`, () =>
      apiFetch(`${modeConfig.endpoint}?page=${currentPage}&per_page=10`, { method: "GET" })
    );

    const posts = (data.posts || []).map(normalizePost);
    hasNextPage = Boolean(data.has_next);

    if (!append) {
      currentPosts = posts;
      feedEl.innerHTML = "";
    } else {
      currentPosts = [...currentPosts, ...posts];
    }

    if (!currentPosts.length) {
      showState(data.message || modeConfig.emptyMessage);
      return;
    }

    hideState();

    posts.forEach((post) => {
      feedEl.appendChild(renderPostCard(post));
    });

    hydrateExpandedCommentBlocks();
    updateFeedSentinel();
  } catch (error) {
    showState(error.message || "Failed to load feed.");
  } finally {
    isFeedLoading = false;
  }
}

function updateFeedSentinel() {
  const sentinel = document.getElementById("feedSentinel");
  if (!sentinel) return;
  sentinel.style.display = hasNextPage ? "block" : "none";
  sentinel.textContent = hasNextPage ? "Loading more posts..." : "";
}

function normalizePost(post) {
  const media = Array.isArray(post.media) ? post.media : [];
  const firstImage = media.find((item) => item.file_type === "image");
  const firstVideo = media.find((item) => item.file_type === "video");
  const isAnonymous = Boolean(post.is_anonymous);
  const author = post.author || {};
  const zone = post.zone || null;
  const avatarUrl = getPostAvatarUrl(author, isAnonymous, getAssetUrl);

  return {
    id: post.id,
    text: post.content || "",
    isAnonymous,
    authorName: isAnonymous
      ? (author.pseudonym || "Anonymous")
      : (author.display_name || author.username || "User"),
    handle: isAnonymous ? "@anonymous" : `@${author.username || "user"}`,
    avatarUrl,
    profileHref: !isAnonymous && author.username ? getProfileHref(author.username) : "",
    isAdmin: !isAnonymous && Boolean(author.is_admin),
    mine: isAnonymous ? Boolean(author.is_you) : Boolean(currentUser && author.id === currentUser.id),
    zoneId: zone?.id || null,
    zoneName: zone?.name || "Campus",
    timeRaw: post.created_at || "",
    timeLabel: formatRelativeTime(post.created_at),
    sentiment: post.sentiment || "neutral",
    emotionLabel: post.emotion_label || "",
    emotionDisplay: post.emotion_display || "",
    imagePath: firstImage?.file_path || "",
    videoPath: firstVideo?.file_path || "",
    reactionCounts: { ...(post.reactions || {}) },
    myReaction: post.my_reaction || null,
    commentCount: Number(post.comment_count || 0),
    isBookmarked: bookmarkedPostIds.has(post.id),
  };
}

function sentimentBadge(sentiment, emotionDisplay = "", emotionLabel = "") {
  const raw = String(emotionDisplay || emotionLabel || sentiment || "neutral").trim();
  const value = raw.toLowerCase();
  if (/(joy|love|excited|hope|positive|calm|grateful|happy)/i.test(value)) return { cls: "green", label: `🟢 ${raw}` };
  if (/(anger|sad|fear|stress|anx|negative|frustr|overwhelm|disgust)/i.test(value)) return { cls: "red", label: `🔴 ${raw}` };
  return { cls: "yellow", label: `🟡 ${raw}` };
}

function renderPostCard(post) {
  const card = document.createElement("article");
  card.className = "panel post";
  card.dataset.id = post.id;
  const badge = sentimentBadge(post.sentiment, post.emotionDisplay, post.emotionLabel);
  const commentOpen = expandedComments.has(post.id);

  card.innerHTML = `
    <div class="post-head">
      <div class="post-user">
        ${post.profileHref ? `
          <a class="post-user-link" href="${escapeAttr(post.profileHref)}" aria-label="View ${escapeAttr(post.authorName)}'s profile">
            <img class="avatar" src="${escapeAttr(post.avatarUrl)}" alt="${escapeAttr(post.authorName)}" loading="lazy" />
            <div class="post-meta">
              <div class="u">
                ${escapeHtml(post.authorName)}${post.isAdmin ? '<span class="admin-star" title="Admin">⭐</span>' : ''}
                <span class="badge ${badge.cls}">${badge.label}</span>
              </div>
              <div class="m">${escapeHtml(post.handle)}</div>
            </div>
          </a>
        ` : `
          <img class="avatar" src="${escapeAttr(post.avatarUrl)}" alt="User" loading="lazy" />
          <div class="post-meta">
            <div class="u">
              ${escapeHtml(post.authorName)}
              <span class="badge ${badge.cls}">${badge.label}</span>
            </div>
            <div class="m">${escapeHtml(post.handle)}</div>
          </div>
        `}
        <div class="post-meta post-meta-secondary">
          <div class="m">
            <button class="zone-pill" data-zone-id="${post.zoneId || ""}" ${post.zoneId ? "" : "disabled"}>
              ${escapeHtml(post.zoneName)}
            </button>
            <span class="dot-sep">•</span>
            ${escapeHtml(post.timeLabel)}
          </div>
        </div>
      </div>
      <div class="post-menu">
        ${post.mine ? `<button class="iconbtn" data-action="delete" title="Delete post" aria-label="Delete post"><i class="ui-icon ui-icon--action uil uil-trash-alt"></i></button>` : ""}
      </div>
    </div>

    ${post.text ? `<div class="post-text">${escapeHtml(post.text)}</div>` : ""}
    ${renderMedia(post)}

    <div class="post-actions">
      <div class="reactions-wrap">
        <button class="react-trigger" data-react-trigger aria-label="React to post">
          ${post.myReaction
            ? `${post.myReaction} <span class="react-trigger-count">${post.reactionCounts[post.myReaction] ?? 0}</span>`
            : `<span class="react-trigger-plus">+</span><span class="react-trigger-label">React</span>`}
        </button>
        <div class="reaction-popup" data-reaction-popup>
          ${REACTION_EMOJIS.map((emoji) => `
            <button class="react-btn ${post.myReaction === emoji ? "is-active" : ""}" data-emoji="${emoji}" title="${emoji}">
              ${emoji}<span>${post.reactionCounts[emoji] ?? 0}</span>
            </button>
          `).join("")}
        </div>
      </div>

      <div class="post-secondary-actions">
        <button class="iconbtn ${post.isBookmarked ? "bookmark-active" : ""}" data-action="bookmark" title="Toggle bookmark" aria-label="Bookmark post">
          <i class="ui-icon ui-icon--action uil ${post.isBookmarked ? "uil-bookmark-full" : "uil-bookmark"}"></i>
        </button>
        <button class="iconbtn" data-action="toggle-comments" title="Toggle comments" aria-label="Toggle comments">
          <i class="ui-icon ui-icon--action uil uil-comment-dots"></i> ${post.commentCount || 0}
        </button>
      </div>
    </div>

    <section class="comment-block ${commentOpen ? "open" : ""}" data-comment-block>
      <div class="reply-context" data-reply-context style="display:none;"></div>
      <form class="comment-form" data-comment-form>
        <input type="hidden" name="parent_id" value="" />
        <textarea
          class="comment-input"
          name="content"
          placeholder="Write a comment..."
          maxlength="500"
          required
        ></textarea>
        <div class="comment-form-actions">
          <label class="checkbox">
            <input type="checkbox" name="is_anonymous" />
            <span>Anonymous</span>
          </label>
          <div class="comment-form-buttons">
            <button type="button" class="btn btn-ghost btn-sm" data-action="cancel-reply">Cancel reply</button>
            <button type="submit" class="btn btn-accent btn-sm">Comment</button>
          </div>
        </div>
      </form>
      <div class="comment-state" data-comment-state>${commentOpen ? "Loading comments..." : ""}</div>
      <div class="comment-list" data-comment-list></div>
    </section>
  `;

  // Reaction trigger — toggle popup
  card.querySelector("[data-react-trigger]")?.addEventListener("click", (e) => {
    e.stopPropagation();
    const popup = card.querySelector("[data-reaction-popup]");
    const isNowOpen = !popup.classList.contains("open");
    // Close any other open popups first
    document.querySelectorAll(".reaction-popup.open").forEach((p) => p.classList.remove("open"));
    popup.classList.toggle("open", isNowOpen);
  });

  // Emoji buttons inside popup
  card.querySelectorAll("[data-emoji]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      card.querySelector("[data-reaction-popup]")?.classList.remove("open");
      await onReact(post.id, btn.dataset.emoji);
    });
  });

  card.querySelector('[data-action="bookmark"]')?.addEventListener("click", async () => {
    await toggleBookmark(post.id);
  });

  card.querySelector('[data-action="toggle-comments"]')?.addEventListener("click", async () => {
    await toggleComments(post.id);
  });

  card.querySelector('[data-action="delete"]')?.addEventListener("click", async () => {
    await onDeletePost(post.id);
  });

  card.querySelector("[data-zone-id]")?.addEventListener("click", () => {
    if (!post.zoneId) return;
    window.location.href = `zone.html?id=${encodeURIComponent(post.zoneId)}`;
  });

  const form = card.querySelector("[data-comment-form]");
  const commentTextarea = form?.querySelector('textarea[name="content"]');
  if (commentTextarea) initMentionAutocomplete(commentTextarea);
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitComment(post.id, form);
  });

  card.querySelector('[data-action="cancel-reply"]')?.addEventListener("click", () => {
    clearReplyContext(post.id);
  });

  return card;
}

function renderMedia(post) {
  if (post.imagePath) {
    return `
      <div class="post-media">
        <img src="${escapeAttr(getAssetUrl(post.imagePath))}" alt="Post media" loading="lazy" />
      </div>
    `;
  }

  if (post.videoPath) {
    return `
      <div class="post-media">
        <video controls src="${escapeAttr(getAssetUrl(post.videoPath))}"></video>
      </div>
    `;
  }

  return "";
}

async function onReact(postId, emoji) {
  const post = currentPosts.find((item) => item.id === postId);
  if (!post) return;

  // Save previous state for rollback
  const prevReaction = post.myReaction;
  const prevCounts   = { ...post.reactionCounts };
  const removing     = post.myReaction === emoji;

  // Optimistic update
  if (removing) {
    post.myReaction = null;
    const updated = { ...post.reactionCounts };
    if (updated[emoji]) { updated[emoji] = Math.max(0, updated[emoji] - 1); }
    post.reactionCounts = updated;
  } else {
    if (post.myReaction) {
      // switching emoji — decrement the old one
      const updated = { ...post.reactionCounts };
      if (updated[post.myReaction]) { updated[post.myReaction] = Math.max(0, updated[post.myReaction] - 1); }
      post.reactionCounts = updated;
    }
    post.myReaction = emoji;
    post.reactionCounts = { ...post.reactionCounts, [emoji]: (post.reactionCounts[emoji] || 0) + 1 };
  }
  rerenderPost(postId);

  try {
    let data;
    if (removing) {
      data = await apiFetch(`/api/posts/${postId}/react`, { method: "DELETE" });
    } else {
      data = await apiFetch(`/api/posts/${postId}/react`, {
        method: "POST",
        body: JSON.stringify({ emoji }),
      });
    }
    // Reconcile with server counts
    post.reactionCounts = { ...(data.counts || {}) };
    rerenderPost(postId);
  } catch (error) {
    // Rollback
    post.myReaction    = prevReaction;
    post.reactionCounts = prevCounts;
    rerenderPost(postId);
    notify(error.message || "Reaction failed", "error");
  }
}

async function toggleBookmark(postId) {
  const post = currentPosts.find((item) => item.id === postId);
  if (!post) return;

  const wasBookmarked = bookmarkedPostIds.has(postId);

  // Optimistic update
  if (wasBookmarked) {
    bookmarkedPostIds.delete(postId);
    post.isBookmarked = false;
  } else {
    bookmarkedPostIds.add(postId);
    post.isBookmarked = true;
  }
  rerenderPost(postId);

  try {
    if (wasBookmarked) {
      await apiFetch(`/api/posts/${postId}/bookmark`, { method: "DELETE" });
      notify("Bookmark removed", "success");
    } else {
      await apiFetch(`/api/posts/${postId}/bookmark`, { method: "POST" });
      notify("Post bookmarked", "success");
    }
  } catch (error) {
    // Rollback
    if (wasBookmarked) {
      bookmarkedPostIds.add(postId);
      post.isBookmarked = true;
    } else {
      bookmarkedPostIds.delete(postId);
      post.isBookmarked = false;
    }
    rerenderPost(postId);
    notify(error.message || "Bookmark failed", "error");
  }
}

async function toggleComments(postId) {
  if (expandedComments.has(postId)) {
    expandedComments.delete(postId);
    rerenderPost(postId);
    return;
  }

  expandedComments.add(postId);
  rerenderPost(postId);
  await loadCommentsForPost(postId);
}

async function loadCommentsForPost(postId, { refresh = false } = {}) {
  if (!refresh && commentsCache.has(postId)) {
    renderComments(postId, commentsCache.get(postId));
    return;
  }

  const card = document.querySelector(`.post[data-id="${postId}"]`);
  const stateEl = card?.querySelector("[data-comment-state]");
  const listEl = card?.querySelector("[data-comment-list]");

  if (stateEl) {
    stateEl.style.display = "block";
    stateEl.textContent = "Loading comments...";
  }
  if (listEl) listEl.innerHTML = "";

  try {
    const data = await apiCall(`feed/comments/${postId}`, () =>
      apiFetch(`/api/posts/${postId}/comments?per_page=50`, { method: "GET" })
    );
    const comments = await Promise.all(
      (data.comments || []).map(async (comment) => ({
        ...comment,
        replies: comment.reply_count
          ? await loadReplies(comment.id)
          : [],
      }))
    );
    commentsCache.set(postId, comments);
    updateCommentCount(postId, comments);
    renderComments(postId, comments);
  } catch (error) {
    if (stateEl) {
      stateEl.style.display = "block";
      stateEl.textContent = error.message || "Failed to load comments.";
    }
  }
}

async function loadReplies(commentId) {
  try {
    const data = await apiFetch(`/api/comments/${commentId}/replies?per_page=50`, {
      method: "GET",
    });
    return data.replies || [];
  } catch {
    return [];
  }
}

function renderComments(postId, comments) {
  const card = document.querySelector(`.post[data-id="${postId}"]`);
  const stateEl = card?.querySelector("[data-comment-state]");
  const listEl = card?.querySelector("[data-comment-list]");
  if (!card || !stateEl || !listEl) return;

  if (!comments.length) {
    stateEl.style.display = "block";
    stateEl.textContent = "No comments yet.";
    listEl.innerHTML = "";
    return;
  }

  stateEl.style.display = "none";
  listEl.innerHTML = comments.map((comment) => renderCommentItem(postId, comment)).join("");

  listEl.querySelectorAll("[data-reply-to]").forEach((btn) => {
    btn.addEventListener("click", () => {
      setReplyContext(postId, btn.dataset.replyTo, btn.dataset.replyLabel);
    });
  });

  listEl.querySelectorAll("[data-delete-comment]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await deleteComment(postId, btn.dataset.deleteComment);
    });
  });
}

function renderCommentItem(postId, comment) {
  const authorName = comment.is_anonymous
    ? (comment.author?.pseudonym || "Anonymous")
    : (comment.author?.display_name || comment.author?.username || "User");
  const canDelete = Boolean(comment.author?.is_you) || comment.author?.id === currentUser?.id;

  return `
    <div class="comment-item">
      <div class="comment-row">
        <div>
          <div class="comment-author">${escapeHtml(authorName)}${!comment.is_anonymous && comment.author?.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : ''}</div>
          <div class="comment-meta">${escapeHtml(formatRelativeTime(comment.created_at))}</div>
        </div>
        <div class="comment-actions-inline">
          <button class="inline-link" type="button" data-reply-to="${comment.id}" data-reply-label="${escapeAttr(authorName)}">Reply</button>
          ${canDelete ? `<button class="inline-link danger-link" type="button" data-delete-comment="${comment.id}">Delete</button>` : ""}
        </div>
      </div>
      <div class="comment-content">${escapeHtml(comment.content || "")}</div>
      ${
        Array.isArray(comment.replies) && comment.replies.length
          ? `
            <div class="comment-replies">
              ${comment.replies.map((reply) => renderReplyItem(reply)).join("")}
            </div>
          `
          : ""
      }
    </div>
  `;
}

function renderReplyItem(reply) {
  const authorName = reply.is_anonymous
    ? (reply.author?.pseudonym || "Anonymous")
    : (reply.author?.display_name || reply.author?.username || "User");

  return `
    <div class="comment-reply">
      <div class="comment-author">${escapeHtml(authorName)}${!reply.is_anonymous && reply.author?.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : ''}</div>
      <div class="comment-meta">${escapeHtml(formatRelativeTime(reply.created_at))}</div>
      <div class="comment-content">${escapeHtml(reply.content || "")}</div>
    </div>
  `;
}

function setReplyContext(postId, commentId, label) {
  const card = document.querySelector(`.post[data-id="${postId}"]`);
  const form = card?.querySelector("[data-comment-form]");
  const parentInput = form?.querySelector('input[name="parent_id"]');
  const replyContext = card?.querySelector("[data-reply-context]");

  if (!form || !parentInput || !replyContext) return;

  parentInput.value = String(commentId);
  replyContext.style.display = "block";
  replyContext.textContent = `Replying to ${label}`;
  form.querySelector('textarea[name="content"]')?.focus();
}

function clearReplyContext(postId) {
  const card = document.querySelector(`.post[data-id="${postId}"]`);
  const form = card?.querySelector("[data-comment-form]");
  const parentInput = form?.querySelector('input[name="parent_id"]');
  const replyContext = card?.querySelector("[data-reply-context]");

  if (parentInput) parentInput.value = "";
  if (replyContext) {
    replyContext.style.display = "none";
    replyContext.textContent = "";
  }
}

async function submitComment(postId, form) {
  const textarea = form.querySelector('textarea[name="content"]');
  const parentId = form.querySelector('input[name="parent_id"]').value;
  const isAnonymous = form.querySelector('input[name="is_anonymous"]').checked;
  const submitBtn = form.querySelector('button[type="submit"]');
  const content = textarea.value.trim();

  if (!content) return;

  try {
    submitBtn.disabled = true;
    submitBtn.textContent = "Posting...";

    await apiFetch(`/api/posts/${postId}/comments`, {
      method: "POST",
      body: JSON.stringify({
        content,
        is_anonymous: isAnonymous,
        parent_id: parentId ? Number(parentId) : null,
      }),
    });

    textarea.value = "";
    form.querySelector('input[name="is_anonymous"]').checked = false;
    clearReplyContext(postId);
    await loadCommentsForPost(postId, { refresh: true });
    notify("Comment added", "success");
  } catch (error) {
    notify(error.message || "Comment failed", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Comment";
  }
}

async function deleteComment(postId, commentId) {
  try {
    await apiFetch(`/api/comments/${commentId}`, { method: "DELETE" });
    await loadCommentsForPost(postId, { refresh: true });
    notify("Comment deleted", "success");
  } catch (error) {
    notify(error.message || "Delete failed", "error");
  }
}

function updateCommentCount(postId, comments) {
  const total = comments.reduce((sum, comment) => sum + 1 + (comment.replies?.length || 0), 0);
  const post = currentPosts.find((item) => item.id === postId);
  if (!post) return;
  post.commentCount = total;
  const button = document.querySelector(`.post[data-id="${postId}"] [data-action="toggle-comments"]`);
  if (button) button.innerHTML = `<i class="ui-icon ui-icon--action uil uil-comment-dots" aria-hidden="true"></i> ${total}`;
}

function hydrateExpandedCommentBlocks() {
  currentPosts.forEach((post) => {
    if (expandedComments.has(post.id)) {
      loadCommentsForPost(post.id);
    }
  });
}

function rerenderPost(postId) {
  const post = currentPosts.find((item) => item.id === postId);
  const currentNode = document.querySelector(`.post[data-id="${postId}"]`);
  if (!post || !currentNode) return;

  const nextNode = renderPostCard(post);
  currentNode.replaceWith(nextNode);

  if (expandedComments.has(postId)) {
    loadCommentsForPost(postId);
  }
}

async function onDeletePost(postId) {
  try {
    await apiFetch(`/api/posts/${postId}`, { method: "DELETE" });
    currentPosts = currentPosts.filter((item) => item.id !== postId);
    document.querySelector(`.post[data-id="${postId}"]`)?.remove();
    if (!currentPosts.length) {
      showState(FEED_MODES[currentFeedMode]?.emptyMessage || "No posts found.");
    }
    notify("Post deleted", "success");
  } catch (error) {
    notify(error.message || "Delete failed", "error");
  }
}

function setupCreateResendLink() {
  const link = document.getElementById("create-resend-link");
  if (!link) return;

  link.textContent = t("auth.login.resend_verification");
  link.addEventListener("click", async (event) => {
    event.preventDefault();
    const email = currentUser?.email;
    if (!email) return;

    link.textContent = t("common.loading");
    try {
      await apiFetch("/api/auth/resend-verification", {
        method: "POST",
        body: JSON.stringify({ email }),
        skipAuthRedirect: true,
      });
      notify(t("auth.login.resend_success"), "success");
      document.getElementById("create-resend-verification").style.display = "none";
    } catch {
      showCreateError(t("auth.login.resend_error"));
    } finally {
      link.textContent = t("auth.login.resend_verification");
    }
  });
}

async function onCreatePostSubmit(event) {
  event.preventDefault();
  hideCreateError();

  const form = document.getElementById("createForm");
  const text = document.getElementById("postText").value.trim();
  const anonymous = document.getElementById("anonymousToggle").checked;
  const zoneId = document.getElementById("zoneId").value;
  const imageInput = document.getElementById("imageFile");
  const imageFile = imageInput?.files?.[0] || null;
  const submitBtn = form?.querySelector('button[type="submit"]');

  if (text.length < 10) {
    showCreateError("Text must be at least 10 characters.");
    return;
  }

  try {
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Posting...";
    }

    const body = new FormData();
    body.append("content", text);
    body.append("is_anonymous", String(anonymous));
    if (zoneId) body.append("zone_id", zoneId);
    if (imageFile) body.append("image", imageFile);

    const data = await apiFetch("/api/posts", {
      method: "POST",
      body,
    });

    notify(data.message || "Post created successfully.", "success");
    document.getElementById("createModal")?.classList.remove("open");
    form?.reset();
    zoneAutocomplete?.clearSelection();
    document.getElementById("zoneId").value = "";
    updateCharCount();

    await resetAndLoadCurrentFeed();
  } catch (error) {
    const needsVerification = error.payload?.needs_verification === true;
    showCreateError(error.message || "Create post failed", needsVerification);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Post";
    }
  }
}

function showState(text) {
  const box = document.getElementById("stateBox");
  if (!box) return;
  box.textContent = text;
  box.style.display = "block";
}

function renderFeedSkeletons() {
  const feedEl = document.getElementById("feed");
  if (!feedEl || currentPosts.length) return;
  feedEl.innerHTML = Array.from({ length: 3 }, () => `
    <article class="skeleton-card">
      <div class="skeleton-line short"></div>
      <div class="skeleton-line medium"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line medium"></div>
    </article>
  `).join("");
}

function hideState() {
  const box = document.getElementById("stateBox");
  if (!box) return;
  box.style.display = "none";
}

function showCreateError(message, showResend = false) {
  const el = document.getElementById("createError");
  if (!el) return;
  el.textContent = message;
  el.style.display = "block";
  const resendEl = document.getElementById("create-resend-verification");
  if (resendEl) resendEl.style.display = showResend ? "block" : "none";
}

function hideCreateError() {
  const el = document.getElementById("createError");
  if (!el) return;
  el.textContent = "";
  el.style.display = "none";
  const resendEl = document.getElementById("create-resend-verification");
  if (resendEl) resendEl.style.display = "none";
}

function setupGlobalUserSearch() {
  const input = document.getElementById("globalSearch");
  const resultsEl = document.getElementById("searchResults");
  if (!input || !resultsEl) return;

  let debounceTimer = null;
  let activeController = null;

  input.addEventListener("input", () => {
    const query = input.value.trim();
    clearTimeout(debounceTimer);
    activeController?.abort();
    activeController = null;

    if (query.length < 2) {
      hideSearchResults();
      return;
    }

    debounceTimer = setTimeout(() => {
      activeController = new AbortController();
      searchUsers(query, activeController.signal);
    }, 300);
  });

  input.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const query = input.value.trim();
    if (query.length < 2) return;
    event.preventDefault();
    window.location.href = `search.html?q=${encodeURIComponent(query)}`;
  });

  document.addEventListener("click", (event) => {
    const insideSearch = input.contains(event.target) || resultsEl.contains(event.target);
    if (!insideSearch) hideSearchResults();
  });
}

async function searchUsers(query, signal) {
  const resultsEl = document.getElementById("searchResults");
  if (!resultsEl) return;

  await runAsyncUI({
    fn:        () => apiCall("feed/search-users", () =>
      apiFetch(`/api/search/users?q=${encodeURIComponent(query)}`, { method: "GET", signal })
    ),
    onLoad:    () => {
      resultsEl.style.display = "block";
      resultsEl.innerHTML = `
        <div class="search-skeleton">
          <div class="skeleton-line short"></div>
          <div class="skeleton-line medium"></div>
          <div class="skeleton-line short"></div>
        </div>`;
    },
    onSuccess: (data) => renderSearchResults(data.users || []),
    onError:   (err)  => {
      if (err.name === "AbortError") return; // superseded by a newer query — do nothing
      resultsEl.innerHTML = `<div class="search-empty">${escapeHtml(err.message || "Search failed")}</div>`;
    },
  });
}

function renderSearchResults(users) {
  const resultsEl = document.getElementById("searchResults");
  if (!resultsEl) return;

  const filtered = users.filter((user) => user.username !== currentUser?.username);
  if (!filtered.length) {
    resultsEl.style.display = "block";
    resultsEl.innerHTML = '<div class="search-empty">No users found</div>';
    return;
  }

  resultsEl.style.display = "block";
  resultsEl.innerHTML = filtered.map((user) => {
    const avatarUrl = getUserAvatarUrl(user, getAssetUrl);

    return `
      <div class="search-result-item">
        <a class="search-result-left search-result-link" href="profile.html?u=${encodeURIComponent(user.username)}">
          <img class="avatar" src="${escapeAttr(avatarUrl)}" alt="User" loading="lazy" />
          <div>
            <div class="search-result-name">${escapeHtml(user.display_name || user.username)}${user.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : ''}</div>
            <div class="search-result-handle">@${escapeHtml(user.username)}</div>
          </div>
        </a>
        <button class="btn btn-accent btn-sm" data-follow-user="${escapeAttr(user.username)}">Follow</button>
      </div>
    `;
  }).join("");

  resultsEl.querySelectorAll("[data-follow-user]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await followUser(btn.dataset.followUser, btn);
    });
  });
}

function hideSearchResults() {
  const resultsEl = document.getElementById("searchResults");
  if (!resultsEl) return;
  resultsEl.style.display = "none";
  resultsEl.innerHTML = "";
}

async function followUser(username, btn) {
  try {
    btn.disabled = true;
    btn.textContent = "Following...";
    const data = await apiFetch(`/api/follow/@${encodeURIComponent(username)}`, {
      method: "POST",
    });
    btn.textContent = "Following";
    notify(data.message || `You are now following @${username}`, "success");
    hideSearchResults();

    if (currentFeedMode === "home") {
      await resetAndLoadCurrentFeed();
    }
  } catch (error) {
    btn.disabled = false;
    btn.textContent = "Follow";
    notify(error.message || "Follow failed", "error");
  }
}

function renderStories() {
  const row = document.getElementById("storiesRow");
  if (!row) return;

  row.innerHTML = `
    <div class="story pulse-card">
      <div class="pulse-center">
        <div class="pulse-ring">
          <div class="pulse-ring-inner">
            <p class="pulse-kicker">Campus pulse</p>
            <div class="pulse-mood" id="pulseMood">—</div>
            <div class="pulse-meta" id="pulseMeta">Share how you feel</div>
            <div class="pulse-dots"><span></span><span></span><span></span><span></span><span></span><span></span></div>
          </div>
        </div>
      </div>
      <div class="pulse-emotions">
        <button class="emotile joy"      data-emotion="joy"      type="button"><div class="emoji">😊</div><div class="label">Joy</div></button>
        <button class="emotile sadness"  data-emotion="sadness"  type="button"><div class="emoji">😢</div><div class="label">Sad</div></button>
        <button class="emotile anger"    data-emotion="anger"    type="button"><div class="emoji">😤</div><div class="label">Angry</div></button>
        <button class="emotile fear"     data-emotion="fear"     type="button"><div class="emoji">😰</div><div class="label">Anxious</div></button>
        <button class="emotile disgust"  data-emotion="disgust"  type="button"><div class="emoji">🤢</div><div class="label">Overwhelmed</div></button>
        <button class="emotile surprise" data-emotion="surprise" type="button"><div class="emoji">😲</div><div class="label">Surprised</div></button>
        <button class="emotile neutral"  data-emotion="neutral"  type="button"><div class="emoji">😐</div><div class="label">Neutral</div></button>
        <div class="emotile-cooldown" id="emotileCooldown" hidden></div>
      </div>
    </div>
  `;

  row.querySelectorAll(".emotile[data-emotion]").forEach((btn) => {
    btn.addEventListener("click", () => checkInMood(btn.dataset.emotion));
  });

  loadCampusPulse();
}

const EMOTION_LABELS = {
  joy: "Joy 😊", sadness: "Sad 😢", anger: "Angry 😤",
  fear: "Anxious 😰", disgust: "Overwhelmed 🤢", surprise: "Surprised 😲", neutral: "Neutral 😐",
};
const EMOTION_EMOJI = {
  joy: "😊", sadness: "😢", anger: "😤", fear: "😰", disgust: "🤢", surprise: "😲", neutral: "😐",
};

let _cooldownInterval = null;

async function loadCampusPulse() {
  try {
    const data = await apiFetch("/api/mood/pulse", { method: "GET" });
    const moodEl = document.getElementById("pulseMood");
    const metaEl = document.getElementById("pulseMeta");

    if (moodEl) {
      moodEl.textContent = data.dominant ? (EMOTION_LABELS[data.dominant] || data.dominant) : "Be first!";
    }
    if (metaEl) {
      metaEl.textContent = data.total > 0
        ? `${data.total} check-in${data.total !== 1 ? "s" : ""} today`
        : "Share how you feel";
    }

    const allEmotiles = document.querySelectorAll(".emotile[data-emotion]");
    const inCooldown = data.cooldown_seconds > 0;
    const cooldownEl = document.getElementById("emotileCooldown");

    allEmotiles.forEach((b) => {
      b.classList.remove("emotile--active");
      b.removeAttribute("data-timer");
      b.disabled = inCooldown;
    });

    if (data.user_emotion) {
      const activeBtn = document.querySelector(`.emotile[data-emotion="${data.user_emotion}"]`);
      if (activeBtn) {
        activeBtn.classList.add("emotile--active");
        if (inCooldown) activeBtn.dataset.timer = formatCooldown(data.cooldown_seconds);
      }
    }

    if (cooldownEl) {
      if (inCooldown) {
        cooldownEl.textContent = `Next check-in in ${formatCooldown(data.cooldown_seconds)}`;
        cooldownEl.hidden = false;
      } else {
        cooldownEl.hidden = true;
      }
    }

    // Live countdown timer
    if (_cooldownInterval) { clearInterval(_cooldownInterval); _cooldownInterval = null; }
    if (inCooldown) {
      const endsAt = Date.now() + data.cooldown_seconds * 1000;
      _cooldownInterval = setInterval(() => {
        const remaining = Math.max(0, Math.round((endsAt - Date.now()) / 1000));
        if (remaining <= 0) {
          clearInterval(_cooldownInterval);
          _cooldownInterval = null;
          loadCampusPulse();
          return;
        }
        const text = formatCooldown(remaining);
        const el = document.getElementById("emotileCooldown");
        const active = document.querySelector(".emotile--active");
        if (el) el.textContent = `Next check-in in ${text}`;
        if (active) active.dataset.timer = text;
      }, 30_000);
    }

    renderCampusMoodSidebar(data);
  } catch {
    // Campus pulse is non-critical — fail silently.
  }
}

function formatCooldown(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

async function checkInMood(emotion) {
  try {
    document.querySelectorAll(".emotile[data-emotion]").forEach((b) => b.classList.remove("emotile--active"));
    const btn = document.querySelector(`.emotile[data-emotion="${emotion}"]`);
    if (btn) btn.classList.add("emotile--active");

    await apiFetch("/api/mood/checkin", {
      method: "POST",
      body: JSON.stringify({ emotion }),
    });

    await loadCampusPulse();
    notify("Feeling logged!", "success");
  } catch (err) {
    const payload = err?.payload;
    if (payload?.retry_after != null) {
      notify(`Already checked in. Next check-in in ${formatCooldown(payload.retry_after)}.`, "info");
      await loadCampusPulse();
    } else {
      notify("Could not log feeling", "error");
    }
  }
}

function renderCampusMoodSidebar(data) {
  const el = document.getElementById("campusMoodList");
  if (!el) return;

  const total = data.total || 0;
  if (!total) {
    el.innerHTML = `<div class="mood-sidebar-empty">No check-ins yet today.<br><span>Be the first to share!</span></div>`;
    return;
  }

  const sorted = Object.entries(data.distribution || {}).sort((a, b) => b[1] - a[1]);
  el.innerHTML = sorted.map(([emotion, count]) => {
    const pct = Math.round(count / total * 100);
    const emoji = EMOTION_EMOJI[emotion] || "";
    return `
      <div class="mood-bar-row">
        <span class="mood-bar-label">${escapeHtml(emoji)} ${escapeHtml(emotion)}</span>
        <div class="mood-bar-track">
          <div class="mood-bar-fill" style="width:${pct}%"></div>
        </div>
        <span class="mood-bar-pct">${pct}%</span>
      </div>
    `;
  }).join("");
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

  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;

  return date.toLocaleDateString([], {
    month: "short",
    day: "numeric",
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
  return escapeHtml(value);
}
