import { apiFetch, getAssetUrl, requireAuth } from "./auth.js";
import { getUserAvatarUrl } from "./avatar.js";
import { initLanguageControls } from "./i18n.js";
import { initThemeToggle, initOfflineBanner } from "./theme.js";

let currentConversationId = null;
let currentOtherUser = null;
let pollTimer = null;

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();

  // Start new conversation by typing @username and pressing Enter
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

  // "New message" buttons open the search field
  const focusSearch = () => document.getElementById("newConversationUsername")?.focus();
  document.getElementById("newMsgBtn")?.addEventListener("click", focusSearch);
  document.getElementById("newMsgBtnEmpty")?.addEventListener("click", focusSearch);

  // Send message on form submit
  document.getElementById("messageComposer")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    await sendMessage();
  });

  // Mobile: back button returns to conversation list
  document.getElementById("backBtn")?.addEventListener("click", () => {
    document.getElementById("dmSidebar").classList.remove("dm-sidebar--hidden");
  });

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
  const name = conv.other_user?.display_name || "Unknown";
  const preview = conv.last_message?.content || "No messages yet.";
  const ts = conv.last_message?.created_at ? formatRelativeTime(conv.last_message.created_at) : "";
  const unread = Number(conv.unread_count || 0) > 0;

  return `
    <button class="dm-conv-row${active ? " dm-conv-row--active" : ""}"
            data-conversation-id="${conv.id}" type="button">
      <div class="dm-conv-avatar-wrap">
        <img class="dm-conv-avatar" src="${escapeAttr(avatar)}" alt="${escapeAttr(name)}" />
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
  // Reveal thread panels (empty state hides, thread shows)
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
  const titleEl = document.getElementById("threadTitle");
  const titleName = currentOtherUser?.display_name || "Conversation";
  titleEl.innerHTML = escapeHtml(titleName) + (currentOtherUser?.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : '');
  document.getElementById("threadAvatar").src = getUserAvatarUrl(
    currentOtherUser,
    getAssetUrl
  );

  thread.innerHTML = renderMessageGroups(data.messages || []);

  // Scroll to latest message
  const area = document.getElementById("messagesArea");
  area.scrollTop = area.scrollHeight;

  await apiFetch(`/api/messages/conversations/${conversationId}/read`, {
    method: "PATCH",
  });

  startPolling(conversationId);
}

/** Group consecutive messages from the same sender, then render. */
function renderMessageGroups(messages) {
  if (!messages.length) {
    return `<div class="dm-empty-thread">No messages yet. Say hello! 👋</div>`;
  }

  // Build groups of consecutive same-sender messages
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
    const n = msgs.length;

    const bubbles = msgs
      .map((m, i) => {
        const pos = n === 1 ? "solo" : i === 0 ? "first" : i === n - 1 ? "last" : "mid";
        return `<div class="dm-bubble" data-pos="${pos}">${escapeHtml(m.content || "")}</div>`;
      })
      .join("");

    const last = msgs[n - 1];
    const timeMeta =
      formatRelativeTime(last.created_at) +
      (last.is_mine && last.is_read ? " · Seen" : "");

    const avatarHtml = !is_mine
      ? `<img class="dm-group-avatar" src="${escapeAttr(getUserAvatarUrl(currentOtherUser, getAssetUrl))}" alt="" />`
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

// ── Send ───────────────────────────────────────────────────────────────────

async function sendMessage() {
  if (!currentConversationId) return;
  const input = document.getElementById("messageInput");
  const content = input.value.trim();
  if (!content) return;
  input.value = "";
  await apiFetch(`/api/messages/conversations/${currentConversationId}`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
  await loadThread(currentConversationId);
  await loadConversations(currentConversationId);
}

// ── Polling ────────────────────────────────────────────────────────────────

function startPolling(conversationId) {
  clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    if (currentConversationId !== conversationId) return;
    await loadThread(conversationId);
    await updateUnreadBadge();
  }, 5000);
}

async function updateUnreadBadge() {
  try {
    const data = await apiFetch("/api/messages/unread-count", { method: "GET" });
    const badge = document.getElementById("messageBadge");
    const count = Number(data.unread_messages || 0);
    badge.textContent = String(count);
    badge.hidden = count === 0;
  } catch {
    // Keep polling resilient.
  }
}

// ── Mobile helpers ─────────────────────────────────────────────────────────

/** On mobile: hide the sidebar, show the thread. */
function showThread() {
  document.getElementById("dmSidebar").classList.add("dm-sidebar--hidden");
  document.getElementById("dmEmpty").hidden = true;
  document.getElementById("threadHeader").hidden = false;
  document.getElementById("messagesArea").hidden = false;
  document.getElementById("messageComposer").hidden = false;
}

// ── Utilities ──────────────────────────────────────────────────────────────

function formatRelativeTime(dateLike) {
  const date = new Date(dateLike);
  const diffSec = Math.floor((Date.now() - date.getTime()) / 1000);
  if (diffSec < 60) return "Just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h`;
  return `${Math.floor(diffHr / 24)}d`;
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

