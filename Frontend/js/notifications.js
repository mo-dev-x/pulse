import { apiFetch, getAssetUrl, requireAuth } from "./auth.js";
import { getUserAvatarUrl } from "./avatar.js";
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
  const loadingEl = document.getElementById("notifLoadingState");
  const emptyEl   = document.getElementById("notifEmpty");
  const listEl    = document.getElementById("notificationList");

  loadingEl.hidden = false;
  emptyEl.hidden   = true;
  listEl.innerHTML = "";

  try {
    const data = await apiFetch("/api/notifications?per_page=50", { method: "GET" });
    loadingEl.hidden = true;

    const notifications = data.notifications || [];
    if (!notifications.length) {
      emptyEl.hidden = false;
      return;
    }

    // Group by time period
    const groups = groupByTime(notifications);
    const fragment = document.createDocumentFragment();

    for (const [label, items] of Object.entries(groups)) {
      if (!items.length) continue;
      const section = document.createElement("section");

      const labelEl = document.createElement("div");
      labelEl.className = "notif-section-label";
      labelEl.textContent = label;
      section.appendChild(labelEl);

      items.forEach((n) => {
        section.appendChild(buildNotifRow(n));
      });

      fragment.appendChild(section);
    }

    listEl.appendChild(fragment);

    // Delegate delete clicks
    listEl.addEventListener("click", async (e) => {
      const deleteBtn = e.target.closest("[data-delete-id]");
      if (deleteBtn) {
        e.preventDefault();
        e.stopPropagation();
        await apiFetch(`/api/notifications/${deleteBtn.dataset.deleteId}`, { method: "DELETE" });
        deleteBtn.closest(".notif-row")?.remove();
        if (!listEl.querySelector(".notif-row")) {
          emptyEl.hidden = false;
        }
        return;
      }

      // Mark as read on row click
      const row = e.target.closest(".notif-row[data-notif-id]");
      if (row && !row.dataset.read) {
        const id = row.dataset.notifId;
        row.dataset.read = "1";
        row.classList.remove("notif-row--unread");
        const dot = row.querySelector(".notif-row::before");
        if (dot) dot.style.display = "none";
        apiFetch(`/api/notifications/${id}/read`, { method: "PATCH" }).catch(() => {});
      }
    });

  } catch (error) {
    loadingEl.hidden = true;
    const errEl = document.createElement("p");
    errEl.style.cssText = "text-align:center;padding:32px;color:var(--muted)";
    errEl.textContent = error.message || "Failed to load notifications.";
    listEl.appendChild(errEl);
  }
}

function groupByTime(notifications) {
  const now = Date.now();
  const DAY   = 86_400_000;
  const WEEK  = 7 * DAY;

  const groups = { "Today": [], "This week": [], "Earlier": [] };

  notifications.forEach((n) => {
    const age = now - new Date(n.created_at).getTime();
    if (age < DAY)        groups["Today"].push(n);
    else if (age < WEEK)  groups["This week"].push(n);
    else                  groups["Earlier"].push(n);
  });

  return groups;
}

function buildNotifRow(notification) {
  const avatar = getUserAvatarUrl(notification.actor, getAssetUrl);
  const { icon, color, text } = describeNotification(notification);

  const a = document.createElement("a");
  a.className = `notif-row${notification.is_read ? "" : " notif-row--unread"}`;
  a.href = notificationHref(notification);
  a.dataset.notifId = notification.id;
  if (notification.is_read) a.dataset.read = "1";

  a.innerHTML = `
    <div class="notif-avatar-wrap">
      <img class="notif-avatar" src="${escapeAttr(avatar)}" alt="" />
      <div class="notif-type-icon ${color}">${icon}</div>
    </div>
    <div class="notif-body">
      <p class="notif-text">${text}</p>
      <span class="notif-time">${formatRelativeTime(notification.created_at)}</span>
    </div>
    <button class="notif-delete-btn" data-delete-id="${notification.id}" title="Remove">
      <i class="uil uil-times"></i>
    </button>
  `;

  return a;
}

function describeNotification(n) {
  const actor = escapeHtml(n.actor?.display_name || n.actor?.username || "Someone");
  const title = n.title || "";
  const msg   = n.message || "";
  const type  = (n.type || "").toLowerCase();

  let icon  = "🔔";
  let color = "notif-type-icon--default";
  let text  = `<strong class="notif-actor">${actor}</strong> ${escapeHtml(msg)}`;

  if (type.includes("react") || type.includes("like")) {
    icon  = "❤️";
    color = "notif-type-icon--reaction";
    text  = `<strong class="notif-actor">${actor}</strong> reacted to your post`;
    if (msg) text += `: "${escapeHtml(msg)}"`;
  } else if (type.includes("comment")) {
    icon  = "💬";
    color = "notif-type-icon--comment";
    text  = `<strong class="notif-actor">${actor}</strong> commented: "${escapeHtml(msg)}"`;
  } else if (type.includes("follow")) {
    icon  = "👤";
    color = "notif-type-icon--follow";
    text  = `<strong class="notif-actor">${actor}</strong> started following you`;
  } else if (type.includes("mention")) {
    icon  = "@";
    color = "notif-type-icon--mention";
    text  = `<strong class="notif-actor">${actor}</strong> mentioned you: "${escapeHtml(msg)}"`;
  } else if (msg) {
    text = `<strong class="notif-actor">${escapeHtml(title || actor)}</strong> ${escapeHtml(msg)}`;
  }

  return { icon, color, text };
}

function notificationHref(n) {
  if (n.related_type === "post" && n.related_id)    return `feed.html#post-${n.related_id}`;
  if (n.related_type === "user" && n.related_id)    return `profile.html?id=${n.related_id}`;
  if (n.related_type === "comment" && n.related_id) return `feed.html#post-${n.related_id}`;
  return "#";
}

function formatRelativeTime(dateLike) {
  const diffSec = Math.floor((Date.now() - new Date(dateLike).getTime()) / 1000);
  if (diffSec < 60)  return "Just now";
  const m = Math.floor(diffSec / 60);
  if (m < 60)  return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24)  return `${h}h`;
  const d = Math.floor(h / 24);
  if (d < 7)   return `${d}d`;
  return `${Math.floor(d / 7)}w`;
}

function escapeHtml(v) {
  return String(v ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(v) { return escapeHtml(v); }
