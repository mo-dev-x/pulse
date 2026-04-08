import { apiFetch, getAssetUrl, requireAuth } from "./auth.js";
import { getUserAvatarUrl } from "./avatar.js";
import { initLanguageControls } from "./i18n.js";
import { initThemeToggle, initOfflineBanner } from "./theme.js";

let currentConversationId = null;
let currentOtherUser = null;
let pollTimer = null;
let lastKnownMessageId = null;   // used by smooth polling
let mediaRecorder = null;
let audioChunks   = [];
let isRecording   = false;

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();

  // Start new conversation
  document.getElementById("newConversationUsername")?.addEventListener("keydown", async (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    const username = e.target.value.trim().replace(/^@/, "");
    if (!username) return;
    const data = await apiFetch("/api/messages/conversations", {
      method: "POST",
      body: JSON.stringify({ username }),
    });
    const conversation = data.conversation;
    if (conversation?.id) {
      e.target.value = "";
      await loadConversations(conversation.id);
      showThread();
    }
  });

  const focusSearch = () => document.getElementById("newConversationUsername")?.focus();
  document.getElementById("newMsgBtn")?.addEventListener("click", focusSearch);
  document.getElementById("newMsgBtnEmpty")?.addEventListener("click", focusSearch);

  document.getElementById("messageComposer")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    await sendMessage();
  });

  document.getElementById("backBtn")?.addEventListener("click", () => {
    document.getElementById("dmSidebar").classList.remove("dm-sidebar--hidden");
  });

  // Image attach
  document.getElementById("imageAttachBtn")?.addEventListener("click", () => {
    document.getElementById("imageAttachInput")?.click();
  });
  document.getElementById("imageAttachInput")?.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    await sendMediaMessage(file);
  });

  // Audio record
  document.getElementById("audioRecordBtn")?.addEventListener("click", toggleAudioRecording);

  // Reply on bubble-wrap button click
  document.getElementById("messageThread")?.addEventListener("click", (e) => {
    const btn = e.target.closest(".dm-reply-btn");
    if (!btn) return;
    e.stopPropagation();
    const preview = btn.dataset.replyPreview || "";
    const ctx = document.getElementById("dmReplyContext");
    if (!ctx) return;
    ctx.dataset.replyToId = btn.dataset.replyId;
    const previewEl = ctx.querySelector(".dm-reply-preview");
    if (previewEl) previewEl.textContent = preview;
    ctx.hidden = false;
    document.getElementById("messageInput")?.focus();
  });

  document.getElementById("dmReplyCancelBtn")?.addEventListener("click", () => {
    const ctx = document.getElementById("dmReplyContext");
    if (ctx) { ctx.hidden = true; ctx.dataset.replyToId = ""; }
  });

  // Right-click context menu for messages
  setupContextMenu();

  await loadConversations();
  updateUnreadBadge();
});

// ── Conversation list ──────────────────────────────────────────────────────

async function loadConversations(selectId = null) {
  const list = document.getElementById("conversationList");
  const data = await apiFetch("/api/messages/conversations", { method: "GET" });
  const conversations = data.conversations || [];

  const totalUnread = conversations.reduce((sum, c) => sum + Number(c.unread_count || 0), 0);
  const badge = document.getElementById("messageBadge");
  badge.textContent = String(totalUnread);
  badge.hidden = totalUnread === 0;

  if (!conversations.length) {
    list.innerHTML = `
      <div class="dm-empty-thread" style="padding: 32px 16px;">
        💬 No conversations yet.<br>
        <span style="font-size:13px;opacity:.7">Search for a username above to start chatting.</span>
      </div>`;
    return;
  }

  currentConversationId = selectId || currentConversationId || conversations[0].id;
  list.innerHTML = conversations
    .map((c) => renderConversation(c, c.id === currentConversationId))
    .join("");

  list.querySelectorAll("[data-conversation-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      currentConversationId = Number(btn.dataset.conversationId);
      await loadConversations(currentConversationId);
      showThread();
    });
  });

  await loadThread(currentConversationId);
}

function renderConversation(conv, active) {
  const avatar = getUserAvatarUrl(conv.other_user, getAssetUrl);
  const name   = conv.other_user?.display_name || "Unknown";
  const preview = conv.last_message
    ? (conv.last_message.content?.startsWith("[audio]") ? "🎤 Voice message" : conv.last_message.content)
    : "No messages yet.";
  const ts     = conv.last_message?.created_at ? formatRelativeTime(conv.last_message.created_at) : "";
  const unread = Number(conv.unread_count || 0) > 0;

  return `
    <button class="dm-conv-row${active ? " dm-conv-row--active" : ""}"
            data-conversation-id="${conv.id}" type="button">
      <div class="dm-conv-avatar-wrap">
        <img class="dm-conv-avatar" src="${escapeAttr(avatar)}" alt="${escapeAttr(name)}" loading="lazy" />
        ${unread ? `<span class="dm-conv-dot"></span>` : ""}
      </div>
      <div class="dm-conv-body">
        <div class="dm-conv-top">
          <span class="dm-conv-name${unread ? " dm-conv-name--bold" : ""}">${escapeHtml(name)}${conv.other_user?.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : ''}</span>
          <span class="dm-conv-ts">${escapeHtml(ts)}</span>
        </div>
        <div class="dm-conv-preview${unread ? " dm-conv-preview--bold" : ""}">${escapeHtml(preview)}</div>
      </div>
    </button>`;
}

// ── Thread ─────────────────────────────────────────────────────────────────

async function loadThread(conversationId) {
  document.getElementById("dmEmpty").hidden = true;
  document.getElementById("threadHeader").hidden = false;
  document.getElementById("messagesArea").hidden = false;
  document.getElementById("messageComposer").hidden = false;

  const thread = document.getElementById("messageThread");
  thread.innerHTML = `
    <div class="dm-loading">
      <div class="dm-skel dm-skel-theirs"></div>
      <div class="dm-skel dm-skel-mine"></div>
      <div class="dm-skel dm-skel-theirs" style="width:35%"></div>
    </div>`;

  const data = await apiFetch(
    `/api/messages/conversations/${conversationId}?per_page=100`,
    { method: "GET" }
  );

  currentOtherUser = data.conversation?.other_user || null;
  const titleEl   = document.getElementById("threadTitle");
  const titleName = currentOtherUser?.display_name || "Conversation";
  titleEl.innerHTML = escapeHtml(titleName) + (currentOtherUser?.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : '');
  document.getElementById("threadAvatar").src = getUserAvatarUrl(currentOtherUser, getAssetUrl);
  const profileLink = document.getElementById("threadProfileLink");
  if (profileLink && currentOtherUser?.username) {
    profileLink.href = `profile.html?u=${encodeURIComponent(currentOtherUser.username)}`;
  }

  const messages = data.messages || [];
  lastKnownMessageId = messages.length ? messages[messages.length - 1].id : null;

  thread.innerHTML = renderMessageGroups(messages);

  const area = document.getElementById("messagesArea");
  area.scrollTop = area.scrollHeight;

  await apiFetch(`/api/messages/conversations/${conversationId}/read`, { method: "PATCH" });

  startPolling(conversationId);
}

// ── Smooth poll — only updates DOM when new messages arrive ───────────────

async function pollMessages(conversationId) {
  if (currentConversationId !== conversationId) return;

  try {
    const data = await apiFetch(
      `/api/messages/conversations/${conversationId}?per_page=100`,
      { method: "GET" }
    );
    const messages = data.messages || [];
    if (!messages.length) return;

    const latestId = messages[messages.length - 1].id;
    if (latestId === lastKnownMessageId) return; // Nothing new

    lastKnownMessageId = latestId;

    const thread = document.getElementById("messageThread");
    const area   = document.getElementById("messagesArea");

    // Remember if user was near the bottom before update
    const nearBottom = area.scrollHeight - area.scrollTop - area.clientHeight < 120;

    // Remove optimistic bubbles before re-rendering real messages
    thread.querySelectorAll(".dm-optimistic").forEach((el) => el.remove());

    thread.innerHTML = renderMessageGroups(messages);

    if (nearBottom) area.scrollTop = area.scrollHeight;

    await apiFetch(`/api/messages/conversations/${conversationId}/read`, { method: "PATCH" });
    await updateUnreadBadge();
  } catch {
    // Polling errors are silent
  }
}

/** Group consecutive messages from the same sender, then render. */
function renderMessageGroups(messages) {
  if (!messages.length) {
    return `<div class="dm-empty-thread">No messages yet. Say hello! 👋</div>`;
  }

  const groups = [];
  for (const msg of messages) {
    const last = groups[groups.length - 1];
    if (last && last.is_mine === msg.is_mine) {
      last.msgs.push(msg);
    } else {
      groups.push({ is_mine: msg.is_mine, msgs: [msg] });
    }
  }

  return groups.map(({ is_mine, msgs }) => {
    const side = is_mine ? "mine" : "theirs";
    const n    = msgs.length;

    const bubbles = msgs.map((m, i) => {
      const pos = n === 1 ? "solo" : i === 0 ? "first" : i === n - 1 ? "last" : "mid";
      const isAudio = m.content?.startsWith("[audio]");
      const isMedia = isAudio || m.content?.startsWith("[image]") || m.content?.startsWith("[video]");
      const extraClass = isAudio ? " dm-bubble--audio" : isMedia ? " dm-bubble--media" : "";
      // Build a short preview for the reply label (strip prefixes, cap at 40 chars)
      const rawPreview = isMedia ? (isAudio ? "🎤 Voice message" : "📎 Media") : (m.content || "");
      const preview = rawPreview.startsWith("↩ ") ? rawPreview.slice(rawPreview.indexOf("\n") + 1) : rawPreview;
      const previewShort = preview.length > 40 ? preview.slice(0, 40) + "…" : preview;
      return `
        <div class="dm-bubble-wrap dm-bubble-wrap--${side}">
          <button class="dm-reply-btn" data-reply-id="${m.id}" data-reply-preview="${escapeAttr(previewShort)}" aria-label="Reply" title="Reply">
            <i class="uil uil-corner-up-left"></i>
          </button>
          <div class="dm-bubble${extraClass}" data-pos="${pos}" data-msg-id="${m.id}" data-is-mine="${m.is_mine}">${renderBubbleContent(m.content)}</div>
        </div>`;
    }).join("");

    const last    = msgs[n - 1];
    const timeMeta = formatRelativeTime(last.created_at) +
      (last.is_mine && last.is_read ? " · Seen" : "");

    const avatarHtml = !is_mine
      ? `<img class="dm-group-avatar" src="${escapeAttr(getUserAvatarUrl(currentOtherUser, getAssetUrl))}" alt="" loading="lazy" />`
      : "";

    return `
      <div class="dm-msg-group dm-msg-group--${side}">
        ${avatarHtml}
        <div class="dm-bubbles">
          ${bubbles}
          <span class="dm-msg-time">${escapeHtml(timeMeta)}</span>
        </div>
      </div>`;
  }).join("");
}

/** Render bubble content — handles audio/image/video messages specially. */
function renderBubbleContent(content) {
  if (!content) return "";
  if (content.startsWith("[audio]")) {
    const url = escapeAttr(content.slice(7));
    return `<audio class="dm-audio" controls src="${url}" preload="metadata"></audio>`;
  }
  if (content.startsWith("[image]")) {
    const url = escapeAttr(content.slice(7));
    return `<img class="dm-media-img" src="${url}" alt="Image" loading="lazy" />`;
  }
  if (content.startsWith("[video]")) {
    const url = escapeAttr(content.slice(7));
    return `<video class="dm-media-video" controls src="${url}" preload="metadata"></video>`;
  }
  return escapeHtml(content);
}

// ── Send text message ──────────────────────────────────────────────────────

async function sendMessage() {
  if (!currentConversationId) return;
  const input   = document.getElementById("messageInput");
  const content = input.value.trim();
  if (!content) return;

  // Clear reply context UI immediately
  const replyCtx = document.getElementById("dmReplyContext");
  let replyingToId = null;
  let replyPrefix   = "";
  if (replyCtx && !replyCtx.hidden) {
    replyingToId = replyCtx.dataset.replyToId || null;
    const previewEl = replyCtx.querySelector(".dm-reply-preview");
    if (previewEl) replyPrefix = `↩ ${previewEl.textContent.trim()}\n`;
    replyCtx.hidden = true;
    replyCtx.dataset.replyToId = "";
  }

  const fullContent = replyPrefix ? replyPrefix + content : content;

  // Optimistic: append bubble immediately
  input.value = "";
  appendOptimisticBubble(fullContent);

  try {
    await apiFetch(`/api/messages/conversations/${currentConversationId}`, {
      method: "POST",
      body: JSON.stringify({ content: fullContent }),
    });
    // Trigger a silent poll to sync real IDs
    lastKnownMessageId = null;
    await pollMessages(currentConversationId);
  } catch (err) {
    showDmToast(err.message || "Failed to send message.");
  }
}

/** Append a temporary optimistic bubble at the bottom of the thread. */
function appendOptimisticBubble(content) {
  const thread = document.getElementById("messageThread");
  const area   = document.getElementById("messagesArea");
  if (!thread) return;

  const wrapper = document.createElement("div");
  wrapper.className = "dm-msg-group dm-msg-group--mine dm-optimistic";
  wrapper.innerHTML = `
    <div class="dm-bubbles">
      <div class="dm-bubble" data-pos="solo">${escapeHtml(content)}</div>
      <span class="dm-msg-time">Sending…</span>
    </div>`;
  thread.appendChild(wrapper);
  area.scrollTop = area.scrollHeight;
}

function showDmToast(msg) {
  const container = document.getElementById("toastContainer") || document.body;
  const el = document.createElement("div");
  el.className = "toast error";
  el.textContent = msg;
  el.style.cssText = "position:fixed;bottom:80px;right:18px;z-index:200;padding:12px 14px;border-radius:14px;background:var(--surface-toast);border:1px solid var(--accent);color:var(--text);font-size:14px;";
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// ── Send image/video message ───────────────────────────────────────────────

async function sendMediaMessage(file) {
  if (!currentConversationId) return;

  // Show optimistic placeholder
  appendOptimisticBubble(`📎 Sending ${file.type.startsWith("video") ? "video" : "image"}…`);

  const form = new FormData();
  form.append("media", file, file.name);
  try {
    await apiFetch(`/api/messages/conversations/${currentConversationId}/media`, {
      method: "POST",
      body: form,
    });
    lastKnownMessageId = null;
    await pollMessages(currentConversationId);
  } catch (err) {
    showDmToast(err.message || "Failed to send image/video. Check that the file is ≤ 5 MB.");
  }
}

// ── Audio recording ────────────────────────────────────────────────────────

async function toggleAudioRecording() {
  if (isRecording) {
    stopAudioRecording();
  } else {
    await startAudioRecording();
  }
}

async function startAudioRecording() {
  if (!navigator.mediaDevices?.getUserMedia) {
    alert("Audio recording is not supported in this browser.");
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks  = [];
    mediaRecorder = new MediaRecorder(stream, { mimeType: getSupportedAudioMime() });
    mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
      await sendAudioMessage(blob);
    };
    mediaRecorder.start();
    isRecording = true;
    setAudioBtnRecording(true);
  } catch {
    alert("Microphone access was denied. Please allow it in your browser settings.");
  }
}

function stopAudioRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    setAudioBtnRecording(false);
  }
}

function getSupportedAudioMime() {
  const types = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/ogg", "audio/mp4"];
  return types.find((t) => MediaRecorder.isTypeSupported?.(t)) || "";
}

function setAudioBtnRecording(active) {
  const btn = document.getElementById("audioRecordBtn");
  if (!btn) return;
  btn.classList.toggle("dm-audio-btn--recording", active);
  btn.title = active ? "Stop recording" : "Send audio";
  btn.querySelector("i").className = active ? "uil uil-stop-circle" : "uil uil-microphone";
}

async function sendAudioMessage(blob) {
  if (!currentConversationId) return;
  appendOptimisticBubble("🎤 Sending voice message…");
  const ext  = blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "mp4" : "webm";
  const form = new FormData();
  form.append("audio", blob, `voice.${ext}`);
  try {
    await apiFetch(`/api/messages/conversations/${currentConversationId}/audio`, {
      method: "POST",
      body: form,
    });
    lastKnownMessageId = null;
    await pollMessages(currentConversationId);
  } catch (err) {
    showDmToast(err.message || "Could not send voice message. Please try again.");
  }
}

// ── Right-click context menu ───────────────────────────────────────────────

let ctxTargetMsgId = null;
let ctxTargetConvId = null;

function setupContextMenu() {
  const menu = document.getElementById("dmCtxMenu");
  const unsendBtn = document.getElementById("dmCtxUnsend");

  function showMenuAt(msgId, convId, x, y) {
    ctxTargetMsgId = msgId;
    ctxTargetConvId = convId;
    menu.hidden = false;
    menu.style.left = `${Math.max(8, Math.min(x, window.innerWidth - 160))}px`;
    menu.style.top  = `${Math.max(8, Math.min(y, window.innerHeight - 80))}px`;
  }

  const threadEl = document.getElementById("messageThread");

  // Desktop: right-click
  threadEl?.addEventListener("contextmenu", (e) => {
    const bubble = e.target.closest(".dm-bubble[data-is-mine='true']");
    if (!bubble) return;
    e.preventDefault();
    showMenuAt(Number(bubble.dataset.msgId), currentConversationId, e.clientX, e.clientY);
  });

  // Mobile: long-press (touch-and-hold)
  let longPressTimer = null;
  threadEl?.addEventListener("touchstart", (e) => {
    const bubble = e.target.closest(".dm-bubble[data-is-mine='true']");
    if (!bubble) return;
    longPressTimer = setTimeout(() => {
      const touch = e.touches[0];
      showMenuAt(Number(bubble.dataset.msgId), currentConversationId, touch.clientX, touch.clientY - 60);
      navigator.vibrate?.(30);
    }, 500);
  }, { passive: true });
  threadEl?.addEventListener("touchend",  () => clearTimeout(longPressTimer), { passive: true });
  threadEl?.addEventListener("touchmove", () => clearTimeout(longPressTimer), { passive: true });

  // Dismiss menu on outside click / touch
  document.addEventListener("click", () => { menu.hidden = true; });
  document.addEventListener("touchstart", (e) => {
    if (!e.target.closest(".dm-bubble") && !e.target.closest(".dm-ctx-menu")) menu.hidden = true;
  }, { passive: true });
  document.addEventListener("contextmenu", (e) => {
    if (!e.target.closest(".dm-bubble[data-is-mine='true']")) menu.hidden = true;
  });

  unsendBtn?.addEventListener("click", async () => {
    menu.hidden = true;
    if (!ctxTargetMsgId || !ctxTargetConvId) return;
    try {
      await apiFetch(
        `/api/messages/conversations/${ctxTargetConvId}/messages/${ctxTargetMsgId}`,
        { method: "DELETE" }
      );
      // Remove the bubble-wrap (and its group if now empty)
      const bubble = document.querySelector(`.dm-bubble[data-msg-id="${ctxTargetMsgId}"]`);
      if (bubble) {
        const bubbleWrap = bubble.closest(".dm-bubble-wrap") || bubble;
        const bubblesWrap = bubble.closest(".dm-bubbles");
        bubbleWrap.remove();
        if (bubblesWrap && !bubblesWrap.querySelector(".dm-bubble")) {
          bubblesWrap.closest(".dm-msg-group")?.remove();
        }
      }
      lastKnownMessageId = null; // force re-sync on next poll
    } catch {
      // silent
    }
  });
}

// ── Polling ────────────────────────────────────────────────────────────────

function startPolling(conversationId) {
  clearInterval(pollTimer);
  pollTimer = setInterval(() => pollMessages(conversationId), 5000);
}

async function updateUnreadBadge() {
  try {
    const data = await apiFetch("/api/messages/unread-count", { method: "GET" });
    const badge = document.getElementById("messageBadge");
    const count = Number(data.unread_messages || 0);
    badge.textContent = String(count);
    badge.hidden = count === 0;
  } catch {
    // Keep polling resilient
  }
}

// ── Mobile helpers ─────────────────────────────────────────────────────────

function showThread() {
  document.getElementById("dmSidebar").classList.add("dm-sidebar--hidden");
  document.getElementById("dmEmpty").hidden = true;
  document.getElementById("threadHeader").hidden = false;
  document.getElementById("messagesArea").hidden = false;
  document.getElementById("messageComposer").hidden = false;
}

// ── Utilities ──────────────────────────────────────────────────────────────

function formatRelativeTime(dateLike) {
  const diffSec = Math.floor((Date.now() - new Date(dateLike).getTime()) / 1000);
  if (diffSec < 60) return "Just now";
  const m = Math.floor(diffSec / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) { return escapeHtml(value); }
