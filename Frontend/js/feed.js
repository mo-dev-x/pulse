import {
  apiFetch,
  getAssetUrl,
  logout,
  requireAuth,
  saveCurrentUser,
} from "./auth.js";
import { getDefaultAvatarUrl, getPostAvatarUrl, getProfileHref, getUserAvatarUrl } from "./avatar.js";
import { initLanguageControls } from "./i18n.js";
import { initMentionAutocomplete } from "./search.js";
import { initOfflineBanner, initThemeToggle, initUnreadBadges } from "./theme.js";

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
const expandedComments = new Set();
const commentsCache = new Map();

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();
  initUnreadBadges();
  setupUserMenu();
  setupModal();
  setupCharCounter();
  setupZonePicker();
  setupFeedModeSwitch();
  setupGlobalUserSearch();
  setupFeedObserver();
  renderStories();
  renderMessages();

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
  const data = await apiFetch("/api/auth/me", { method: "GET" });
  currentUser = data.user;
  saveCurrentUser(currentUser);
  renderCurrentUser(currentUser);
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
  modal.addEventListener("click", (event) => {
    if (event.target === modal) closeModal();
  });
  form.addEventListener("submit", onCreatePostSubmit);

  function openModal() {
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
    const data = await apiFetch(
      `${modeConfig.endpoint}?page=${currentPage}&per_page=10`,
      { method: "GET" }
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
    mine: isAnonymous ? Boolean(author.is_you) : Boolean(currentUser && author.id === currentUser.id),
    zoneId: zone?.id || null,
    zoneName: zone?.name || "Campus",
    timeRaw: post.created_at || "",
    timeLabel: formatRelativeTime(post.created_at),
    sentiment: post.sentiment || "neutral",
    imagePath: firstImage?.file_path || "",
    videoPath: firstVideo?.file_path || "",
    reactionCounts: { ...(post.reactions || {}) },
    myReaction: post.my_reaction || null,
    commentCount: Number(post.comment_count || 0),
    isBookmarked: bookmarkedPostIds.has(post.id),
  };
}

function sentimentBadge(sentiment) {
  const value = String(sentiment || "neutral").toLowerCase();
  if (value.includes("pos")) return { cls: "green", label: "🟢 Positive" };
  if (value.includes("neg")) return { cls: "red", label: "🔴 Negative" };
  return { cls: "yellow", label: "🟡 Neutral" };
}

function renderPostCard(post) {
  const card = document.createElement("article");
  card.className = "panel post";
  card.dataset.id = post.id;
  const badge = sentimentBadge(post.sentiment);
  const commentOpen = expandedComments.has(post.id);

  card.innerHTML = `
    <div class="post-head">
      <div class="post-user">
        ${post.profileHref ? `
          <a class="post-user-link" href="${escapeAttr(post.profileHref)}" aria-label="View ${escapeAttr(post.authorName)}'s profile">
            <img class="avatar" src="${escapeAttr(post.avatarUrl)}" alt="${escapeAttr(post.authorName)}" />
            <div class="post-meta">
              <div class="u">
                ${escapeHtml(post.authorName)}
                <span class="badge ${badge.cls}">${badge.label}</span>
              </div>
              <div class="m">${escapeHtml(post.handle)}</div>
            </div>
          </a>
        ` : `
          <img class="avatar" src="${escapeAttr(post.avatarUrl)}" alt="User" />
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
        ${post.mine ? `<button class="iconbtn" data-action="delete" title="Delete post">🗑️</button>` : ""}
      </div>
    </div>

    ${post.text ? `<div class="post-text">${escapeHtml(post.text)}</div>` : ""}
    ${renderMedia(post)}

    <div class="post-actions">
      <div class="reaction-grid">
        ${REACTION_EMOJIS.map((emoji) => `
          <button class="react-btn ${post.myReaction === emoji ? "is-active" : ""}" data-emoji="${emoji}">
            ${emoji}
            <span>${post.reactionCounts[emoji] ?? 0}</span>
          </button>
        `).join("")}
      </div>

      <div class="post-secondary-actions">
        <button class="iconbtn ${post.isBookmarked ? "bookmark-active" : ""}" data-action="bookmark" title="Toggle bookmark">
          ${post.isBookmarked ? "🔖" : "📑"}
        </button>
        <button class="iconbtn" data-action="toggle-comments" title="Toggle comments">
          💬 ${post.commentCount || 0}
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

  card.querySelectorAll("[data-emoji]").forEach((btn) => {
    btn.addEventListener("click", async () => {
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
        <img src="${escapeAttr(getAssetUrl(post.imagePath))}" alt="Post media" />
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

  try {
    let data;
    if (post.myReaction === emoji) {
      data = await apiFetch(`/api/posts/${postId}/react`, { method: "DELETE" });
      post.myReaction = null;
      post.reactionCounts = { ...(data.counts || {}) };
    } else {
      data = await apiFetch(`/api/posts/${postId}/react`, {
        method: "POST",
        body: JSON.stringify({ emoji }),
      });
      post.myReaction = emoji;
      post.reactionCounts = { ...(data.counts || {}) };
    }

    rerenderPost(postId);
  } catch (error) {
    showToast(error.message || "Reaction failed", "error");
  }
}

async function toggleBookmark(postId) {
  const post = currentPosts.find((item) => item.id === postId);
  if (!post) return;

  try {
    if (bookmarkedPostIds.has(postId)) {
      await apiFetch(`/api/posts/${postId}/bookmark`, { method: "DELETE" });
      bookmarkedPostIds.delete(postId);
      post.isBookmarked = false;
      showToast("Bookmark removed", "success");
    } else {
      await apiFetch(`/api/posts/${postId}/bookmark`, { method: "POST" });
      bookmarkedPostIds.add(postId);
      post.isBookmarked = true;
      showToast("Post bookmarked", "success");
    }
    rerenderPost(postId);
  } catch (error) {
    showToast(error.message || "Bookmark failed", "error");
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
    const data = await apiFetch(`/api/posts/${postId}/comments?per_page=50`, {
      method: "GET",
    });
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
          <div class="comment-author">${escapeHtml(authorName)}</div>
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
      <div class="comment-author">${escapeHtml(authorName)}</div>
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
    showToast("Comment added", "success");
  } catch (error) {
    showToast(error.message || "Comment failed", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Comment";
  }
}

async function deleteComment(postId, commentId) {
  try {
    await apiFetch(`/api/comments/${commentId}`, { method: "DELETE" });
    await loadCommentsForPost(postId, { refresh: true });
    showToast("Comment deleted", "success");
  } catch (error) {
    showToast(error.message || "Delete failed", "error");
  }
}

function updateCommentCount(postId, comments) {
  const total = comments.reduce((sum, comment) => sum + 1 + (comment.replies?.length || 0), 0);
  const post = currentPosts.find((item) => item.id === postId);
  if (!post) return;
  post.commentCount = total;
  const button = document.querySelector(`.post[data-id="${postId}"] [data-action="toggle-comments"]`);
  if (button) button.textContent = `💬 ${total}`;
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
    showToast("Post deleted", "success");
  } catch (error) {
    showToast(error.message || "Delete failed", "error");
  }
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

    showToast(data.message || "Post created successfully.", "success");
    document.getElementById("createModal")?.classList.remove("open");
    form?.reset();
    zoneAutocomplete?.clearSelection();
    document.getElementById("zoneId").value = "";
    updateCharCount();

    await resetAndLoadCurrentFeed();
  } catch (error) {
    showCreateError(error.message || "Create post failed");
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

function showCreateError(message) {
  const el = document.getElementById("createError");
  if (!el) return;
  el.textContent = message;
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

async function searchUsers(query) {
  const resultsEl = document.getElementById("searchResults");
  if (!resultsEl) return;

  try {
    const data = await apiFetch(`/api/search/users?q=${encodeURIComponent(query)}`, {
      method: "GET",
    });
    renderSearchResults(data.users || []);
  } catch (error) {
    resultsEl.style.display = "block";
    resultsEl.innerHTML = `<div class="search-empty">${escapeHtml(error.message || "Search failed")}</div>`;
  }
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
          <img class="avatar" src="${escapeAttr(avatarUrl)}" alt="User" />
          <div>
            <div class="search-result-name">${escapeHtml(user.display_name || user.username)}</div>
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
    showToast(data.message || `You are now following @${username}`, "success");
    hideSearchResults();

    if (currentFeedMode === "home") {
      await resetAndLoadCurrentFeed();
    }
  } catch (error) {
    btn.disabled = false;
    btn.textContent = "Follow";
    showToast(error.message || "Follow failed", "error");
  }
}

function renderMessages() {
  const msgList = document.getElementById("msgList");
  if (!msgList) return;

  const items = [
    { name: "Daniella Jackson", snippet: "2 new messages", img: 16 },
    { name: "Marc Tremblay", snippet: "Let’s study tonight", img: 33 },
    { name: "Sarah Lavoie", snippet: "Thanks for the follow!", img: 24 },
  ];

  msgList.innerHTML = items.map((item) => `
    <div class="msg">
      <img class="avatar" src="${escapeAttr(getDefaultAvatarUrl())}" alt="${escapeAttr(item.name)}" />
      <div>
        <div class="t">${escapeHtml(item.name)}</div>
        <div class="s">${escapeHtml(item.snippet)}</div>
      </div>
    </div>
  `).join("");
}

function renderStories() {
  const row = document.getElementById("storiesRow");
  if (!row) return;

  row.innerHTML = `
    <div class="story pulse-card">
      <div class="pulse-left">
        <div class="pulse-ring">
          <div class="pulse-ring-inner">
            <p class="pulse-kicker">Campus pulse</p>
            <div class="pulse-mood">Balanced</div>
            <div class="pulse-meta">Community mood snapshot</div>
            <div class="pulse-dots"><span></span><span></span><span></span><span></span><span></span><span></span></div>
          </div>
        </div>
      </div>
      <div class="pulse-right">
        <div class="emotile joy"><div class="emoji">😊</div><div class="label">Joy</div></div>
        <div class="emotile stress"><div class="emoji">😵</div><div class="label">Stress</div></div>
        <div class="emotile calm"><div class="emoji">🫶</div><div class="label">Calm</div></div>
        <div class="emotile connected"><div class="emoji">🤝</div><div class="label">Connected</div></div>
        <div class="emotile tired"><div class="emoji">😴</div><div class="label">Tired</div></div>
        <div class="emotile frustrated"><div class="emoji">😤</div><div class="label">Frustrated</div></div>
      </div>
    </div>
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
