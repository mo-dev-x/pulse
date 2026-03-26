import { apiFetch } from "./auth.js";

const THEME_KEY = "pulse_theme";
let badgeTimer = null;

export function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  const systemDark = window.matchMedia?.("(prefers-color-scheme: dark)")?.matches;
  const theme = saved || (systemDark ? "dark" : "light");
  applyTheme(theme);
}

export function applyTheme(theme) {
  const next = theme === "light" ? "light" : theme === "auto"
    ? (window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ? "dark" : "light")
    : "dark";

  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem(THEME_KEY, next);

  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    btn.textContent = next === "dark" ? "☀️" : "🌙";
    btn.setAttribute("aria-label", next === "dark" ? "Switch to light mode" : "Switch to dark mode");
  });

  return next;
}

export function initThemeToggle(root = document) {
  initTheme();
  root.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      applyTheme(current === "dark" ? "light" : "dark");
    });
  });
}

export function initOfflineBanner() {
  const banner = document.getElementById("offlineBanner");
  if (!banner) return;

  const sync = () => {
    const online = navigator.onLine !== false;
    banner.hidden = online;
  };

  window.addEventListener("online", sync);
  window.addEventListener("offline", sync);
  sync();
}

export async function refreshUnreadBadges(root = document) {
  const messageBadges = root.querySelectorAll("[data-message-badge]");
  const notificationBadges = root.querySelectorAll("[data-notification-badge]");

  if (!messageBadges.length && !notificationBadges.length) return;

  try {
    const tasks = [];
    if (messageBadges.length) tasks.push(apiFetch("/api/messages/unread-count", { method: "GET" }));
    else tasks.push(Promise.resolve(null));
    if (notificationBadges.length) tasks.push(apiFetch("/api/notifications?per_page=1", { method: "GET" }));
    else tasks.push(Promise.resolve(null));

    const [messagesData, notificationsData] = await Promise.all(tasks);

    const unreadMessages = Number(messagesData?.unread_messages || 0);
    const unreadNotifications = Number(notificationsData?.unread_count || 0);

    messageBadges.forEach((badge) => {
      badge.hidden = unreadMessages <= 0;
      badge.textContent = String(unreadMessages);
    });

    notificationBadges.forEach((badge) => {
      badge.hidden = unreadNotifications <= 0;
      badge.textContent = String(unreadNotifications);
    });
  } catch {
    // Keep shell resilient when badge endpoints fail.
  }
}

export function initUnreadBadges(root = document) {
  refreshUnreadBadges(root);
  if (badgeTimer) clearInterval(badgeTimer);
  badgeTimer = setInterval(() => {
    refreshUnreadBadges(root);
  }, 60000);
}
