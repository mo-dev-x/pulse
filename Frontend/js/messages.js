import { apiFetch, getAssetUrl, requireAuth } from "./auth.js";
import { initLanguageControls } from "./i18n.js";
import { initThemeToggle, initOfflineBanner } from "./theme.js";

let currentConversationId = null;
let pollTimer = null;

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();

  document.getElementById("newConversationUsername")?.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const username = event.target.value.trim().replace(/^@/, "");
    if (!username) return;
    const data = await apiFetch("/api/messages/conversations", {
      method: "POST",
      body: JSON.stringify({ username }),
    });
    const conversation = data.conversation;
    if (conversation?.id) {
      event.target.value = "";
      await loadConversations(conversation.id);
    }
  });

  document.getElementById("messageComposer")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    await sendMessage();
  });

  await loadConversations();
  updateUnreadBadge();
});

async function loadConversations(selectId = null) {
  const list = document.getElementById("conversationList");
  const data = await apiFetch("/api/messages/conversations", { method: "GET" });
  const conversations = data.conversations || [];

  document.getElementById("messageBadge").textContent = String(
    conversations.reduce((sum, item) => sum + Number(item.unread_count || 0), 0)
  );

  if (!conversations.length) {
    list.innerHTML = '<div class="state state-illustrated"><div class="state-emoji">💬</div><div>No conversations yet.<br />Aucune conversation pour le moment.</div></div>';
    return;
  }

  currentConversationId = selectId || currentConversationId || conversations[0].id;
  list.innerHTML = conversations.map((item) => renderConversation(item, item.id === currentConversationId)).join("");

  list.querySelectorAll("[data-conversation-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      currentConversationId = Number(btn.dataset.conversationId);
      await loadConversations(currentConversationId);
    });
  });

  await loadThread(currentConversationId);
}

async function loadThread(conversationId) {
  const state = document.getElementById("threadState");
  const thread = document.getElementById("messageThread");
  const form = document.getElementById("messageComposer");
  thread.innerHTML = "";
  state.style.display = "block";
  state.textContent = "Loading messages...";

  const data = await apiFetch(`/api/messages/conversations/${conversationId}?per_page=100`, { method: "GET" });
  document.getElementById("threadTitle").textContent = data.conversation?.other_user?.display_name || "Conversation";
  state.style.display = "none";
  form.hidden = false;

  thread.innerHTML = (data.messages || []).map(renderMessage).join("");
  await apiFetch(`/api/messages/conversations/${conversationId}/read`, { method: "PATCH" });
  startPolling(conversationId);
}

function renderConversation(conversation, active) {
  const avatar = conversation.other_user?.profile_picture
    ? getAssetUrl(conversation.other_user.profile_picture)
    : `https://i.pravatar.cc/80?u=${encodeURIComponent(conversation.other_user?.username || conversation.id)}`;

  return `
    <button class="conversation-row ${active ? "active" : ""}" data-conversation-id="${conversation.id}" type="button">
      <img class="avatar" src="${escapeAttr(avatar)}" alt="User" />
      <div>
        <div class="conversation-name">${escapeHtml(conversation.other_user?.display_name || "Unknown user")}</div>
        <div class="conversation-preview">${escapeHtml(conversation.last_message?.content || "No messages yet.")}</div>
      </div>
      <div>${conversation.unread_count ? `<span class="inline-badge">${conversation.unread_count}</span>` : ""}</div>
    </button>
  `;
}

function renderMessage(message) {
  return `
    <article class="message-bubble ${message.is_mine ? "mine" : "theirs"}">
      <div>${escapeHtml(message.content || "")}</div>
      <div class="message-time">${escapeHtml(formatRelativeTime(message.created_at))}${message.is_mine && message.is_read ? " • Read" : ""}</div>
    </article>
  `;
}

async function sendMessage() {
  if (!currentConversationId) return;
  const input = document.getElementById("messageInput");
  const content = input.value.trim();
  if (!content) return;
  await apiFetch(`/api/messages/conversations/${currentConversationId}`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
  input.value = "";
  await loadThread(currentConversationId);
  await loadConversations(currentConversationId);
}

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
    document.getElementById("messageBadge").textContent = String(data.unread_messages || 0);
  } catch {
    // Keep polling resilient.
  }
}

function formatRelativeTime(dateLike) {
  const date = new Date(dateLike);
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
