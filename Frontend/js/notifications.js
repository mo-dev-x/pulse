import { apiFetch, getAssetUrl, requireAuth } from "./auth.js";
import { initLanguageControls } from "./i18n.js";
import { initThemeToggle, initOfflineBanner } from "./theme.js";

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();

  document.getElementById("markAllRead")?.addEventListener("click", async () => {
    await apiFetch("/api/notifications/read-all", { method: "PATCH" });
    await loadNotifications();
  });

  await loadNotifications();
});

async function loadNotifications() {
  const summary = document.getElementById("notifSummary");
  const list = document.getElementById("notificationList");
  summary.textContent = "Loading...";
  list.innerHTML = "";

  try {
    const data = await apiFetch("/api/notifications?per_page=50", { method: "GET" });
    summary.innerHTML = `Unread <span class="inline-badge">${data.unread_count || 0}</span>`;

    if (!(data.notifications || []).length) {
      list.innerHTML = '<div class="state state-illustrated"><div class="state-emoji">🔔</div><div>No notifications yet.<br />Aucune notification pour le moment.</div></div>';
      return;
    }

    list.innerHTML = data.notifications.map((notification) => renderNotification(notification)).join("");

    list.querySelectorAll("[data-mark-read]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await apiFetch(`/api/notifications/${btn.dataset.markRead}/read`, { method: "PATCH" });
        await loadNotifications();
      });
    });

    list.querySelectorAll("[data-delete-notification]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await apiFetch(`/api/notifications/${btn.dataset.deleteNotification}`, { method: "DELETE" });
        await loadNotifications();
      });
    });
  } catch (error) {
    summary.textContent = error.message || "Failed to load notifications.";
  }
}

function renderNotification(notification) {
  const avatar = notification.actor?.profile_picture
    ? getAssetUrl(notification.actor.profile_picture)
    : `https://i.pravatar.cc/80?u=${encodeURIComponent(notification.actor?.username || notification.id)}`;

  return `
    <article class="notification-item ${notification.is_read ? "" : "unread"}">
      <img class="notification-avatar" src="${escapeAttr(avatar)}" alt="Actor" />
      <div>
        <div class="notification-title">${escapeHtml(notification.title || notification.type)}</div>
        <div class="notification-message">${escapeHtml(notification.message || "")}</div>
        <div class="notification-meta">${escapeHtml(formatRelativeTime(notification.created_at))}</div>
      </div>
      <div class="notification-actions">
        ${notification.is_read ? "" : `<button class="iconbtn" data-mark-read="${notification.id}" title="Mark as read">✓</button>`}
        <button class="iconbtn" data-delete-notification="${notification.id}" title="Delete">✕</button>
      </div>
    </article>
  `;
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
